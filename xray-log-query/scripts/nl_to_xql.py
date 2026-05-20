#!/usr/bin/env python3
"""
自然语言 → Xray XQL 查询语句转换脚本
用途：将用户的自然语言描述转换为符合 Xray 日志表约束的 XQL 查询参数，
      输出 JSON，供 `xray-cli log {query|chart|cluster}` 的 --query / --st / --et /
      --search-trace-app 参数直接使用（v2.0.0+ 流程，详见 SKILL.md）。

XQL 语法规则（来源：Redoc 文档《日志查询语法》）：
  - 键值检索：field:value（精确匹配，性能最高）
  - 短语检索：field:"value"（包含该 token）
  - 模糊检索：field:"*value*"（通配符，性能较差）
  - 数值检索：field:>400、field:>=200
  - 多值检索：field:v1,v2（等同于 OR）
  - 逻辑组合：AND / OR / NOT / ()
  - 结构化字段：ext.uid:12345
  - 管道分析：query | SELECT ...（本脚本仅生成检索部分，不生成 SELECT）

转换策略（基于规则匹配 + LLM，无需网络即可运行基础规则模式）：

  模式 A（规则模式，无需 LLM）：
    从 table_config 的 nl_field_rules 动态加载识别规则，支持多表。

  模式 B（LLM 模式，需配置 API Key）：
    当规则模式置信度不足时，调用大模型生成精确 XQL。
    通过环境变量或 --llm-api-key 参数配置。

用法：
  # 规则模式（默认，application 表）
  python nl_to_xql.py --text "查一下 my-service 最近 1 小时的 error 日志"

  # 指定表
  python nl_to_xql.py --text "查 edith.xiaohongshu.com 最近 30 分钟的 500 错误" --table rgw

  # LLM 模式
  python nl_to_xql.py --text "..." --llm-api-key sk-xxx [--llm-base-url https://...]

  # 管道用法（直接传给下游脚本）
  python nl_to_xql.py --text "my-service 最近 error" | \\
    python -c "import json,sys; p=json.load(sys.stdin); \\
      print(p['query'], p['st'], p['et'])"

输出 JSON 格式：
  {
    "query": "subApplication:my-service AND level:error",
    "st": 1700000000,
    "et": 1700003600,
    "search_trace_app": false,
    "mode": "rule",          // rule | llm
    "confidence": "high",    // high | medium | low
    "explanation": "识别到服务名 my-service，时间范围最近 1 小时，日志级别 error"
  }
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from typing import Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from table_config import get_table_config, TABLE_CONFIGS


# ── 时间解析 ──────────────────────────────────────────────────────────────────

_TIME_PATTERNS = [
    # 最近 N 分钟
    (re.compile(r"最近\s*(\d+)\s*分钟"), lambda m: int(m.group(1)) * 60),
    # 最近 N 小时
    (re.compile(r"最近\s*(\d+)\s*(小时|h|hour)"), lambda m: int(m.group(1)) * 3600),
    # 最近 N 天
    (re.compile(r"最近\s*(\d+)\s*(天|d|day)"), lambda m: int(m.group(1)) * 86400),
    # last N minutes
    (re.compile(r"last\s+(\d+)\s*min", re.I), lambda m: int(m.group(1)) * 60),
    # last N hours
    (re.compile(r"last\s+(\d+)\s*h", re.I), lambda m: int(m.group(1)) * 3600),
    # past N hours / past N minutes
    (re.compile(r"past\s+(\d+)\s*hour", re.I), lambda m: int(m.group(1)) * 3600),
    (re.compile(r"past\s+(\d+)\s*min", re.I), lambda m: int(m.group(1)) * 60),
    # 1h / 30m 简写
    (re.compile(r"\b(\d+)\s*h\b", re.I), lambda m: int(m.group(1)) * 3600),
    (re.compile(r"\b(\d+)\s*m\b"), lambda m: int(m.group(1)) * 60),
]

_DEFAULT_RANGE_SECONDS = 3600  # 未识别时间时默认最近 1 小时


def _parse_time_range(text: str) -> Tuple[int, int]:
    """从自然语言中提取时间范围，返回 (st, et) Unix 秒。"""
    now = int(time.time())
    for pattern, calc in _TIME_PATTERNS:
        m = pattern.search(text)
        if m:
            seconds = calc(m)
            return now - seconds, now
    return now - _DEFAULT_RANGE_SECONDS, now


# ── 字段识别（基于 table_config 动态规则）──────────────────────────────────────


def _build_query_from_config(text: str, table: str):
    """
    基于 table_config 中的 nl_field_rules 从自然语言文本提取字段，构建 XQL 条件列表。

    Returns:
        (conditions: list[str], search_trace_app: bool, explanation_parts: list[str], confidence_score: int)
    """
    cfg = get_table_config(table)
    rules = cfg.get("nl_field_rules", [])

    conditions = []
    explanation_parts = []
    confidence_score = 0
    search_trace_app = False
    seen_fields = set()

    # subApplication 字段使用去时间短语后的文本，避免"最近"等词被误识别为服务名
    text_for_service = re.sub(
        r"最近\s*\d+\s*(?:分钟|小时|天|min|hour|h|d|day)",
        "",
        text,
        flags=re.I,
    )

    for rule in rules:
        field = rule["field"]
        if field in seen_fields:
            continue
        op = rule.get("op", ":")
        quote = rule.get("quote", False)
        value_group = rule.get("value_group", 1)
        value_map = rule.get("value_map", {})
        # subApplication 和部分字段用去时间短语后的文本匹配
        search_text = text_for_service if field in ("subApplication",) else text

        for pattern in rule.get("patterns", []):
            m = re.search(pattern, search_text, re.I)
            if m:
                try:
                    raw_val = m.group(value_group)
                except IndexError:
                    continue
                if not raw_val:
                    continue
                val = value_map.get(raw_val.lower(), raw_val)
                if quote:
                    cond = f'{field}{op}"{val}"'
                else:
                    cond = f"{field}{op}{val}"
                conditions.append(cond)
                seen_fields.add(field)
                # 高权重字段
                if field in (
                    "subApplication",
                    "xrayTraceId",
                    "x-xray-traceid",
                    "http_host",
                    "ext.uid",
                    "release",  # flink 表任务标识，等权重于 subApplication
                    "cluster",  # event/audit 表集群标识，等权重于 subApplication
                ):
                    confidence_score += 40
                else:
                    confidence_score += 10
                explanation_parts.append(f"识别到 {field}: {val}")
                if rule.get("set_search_trace_app"):
                    search_trace_app = True
                break  # 每个 field 只匹配一次

    return conditions, search_trace_app, explanation_parts, confidence_score


def _parse_rule(text: str, table: str = "application") -> dict:
    """规则模式：从 table_config 的 nl_field_rules 提取字段，构建 XQL。"""
    try:
        conditions, search_trace_app, explanation_parts, confidence_score = (
            _build_query_from_config(text, table)
        )
    except ValueError as e:
        now = int(time.time())
        return {
            "query": "",
            "st": now - 3600,
            "et": now,
            "search_trace_app": False,
            "mode": "rule",
            "confidence": "low",
            "explanation": str(e),
        }

    # 检查是否有必要字段（required_fields 非空时降低置信度）
    cfg = get_table_config(table)
    required = cfg.get("required_fields", [])
    if required:
        has_required = any(
            any(c.startswith(f + ":") or c.startswith(f + ":>") for f in required)
            for c in conditions
        )
        if not has_required:
            confidence_score = max(0, confidence_score - 30)

    query = " AND ".join(conditions) if conditions else ""

    if confidence_score >= 50:
        confidence = "high"
    elif confidence_score >= 20:
        confidence = "medium"
    else:
        confidence = "low"

    st, et = _parse_time_range(text)
    explanation_parts.append(
        f"时间范围：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st))} ~ "
        f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(et))}"
    )

    return {
        "query": query,
        "st": st,
        "et": et,
        "search_trace_app": search_trace_app,
        "mode": "rule",
        "confidence": confidence,
        "explanation": "；".join(explanation_parts) if explanation_parts else "未能识别有效字段",
    }


# ── LLM 模式 ──────────────────────────────────────────────────────────────────


def _parse_llm(
    text: str, api_key: str, base_url: str, model: str, table: str = "application"
) -> dict:
    """LLM 模式：调用大模型生成 XQL。"""
    cfg = get_table_config(table)
    common_fields = cfg.get("common_fields", [])
    required_fields = cfg.get("required_fields", [])

    now = int(time.time())
    required_note = (
        f"必须包含以下字段之一：{', '.join(required_fields)}"
        if required_fields
        else "无必填字段约束"
    )
    system_prompt = f"""你是 Xray 日志平台的 XQL 查询专家。
当前查询目标表：{table}
常用过滤字段：{", ".join(common_fields)}
字段约束：{required_note}

请将用户的自然语言描述转换为 Xray XQL 查询参数，以 JSON 格式输出，不要包含任何其他内容。

XQL 语法规则：
- 键值精确匹配：field:value
- 短语检索：field:"value"
- 模糊检索：field:"*value*"
- 数值比较：field:>400 / field:>=200 / field:<500
- 多值 OR：field:v1,v2
- 逻辑组合：AND / OR / NOT / ()
- 结构化字段：ext.uid:12345
- 不要生成 | SELECT 语法

时间参数：st 和 et 为 Unix 秒（当前时间戳参考：{now}）。

输出 JSON 格式（严格遵守，不要有多余字段）：
{{
  "query": "XQL 查询语句",
  "st": 开始时间Unix秒,
  "et": 结束时间Unix秒,
  "search_trace_app": true/false（仅当 query 含 xrayTraceId 时为 true）,
  "confidence": "high/medium/low",
  "explanation": "简要说明识别逻辑"
}}"""

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.0,
            "max_tokens": 512,
        }
    ).encode()

    url = base_url.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp_data = json.loads(resp.read().decode())
    except Exception as e:
        raise RuntimeError(f"LLM API 调用失败：{e}") from e

    content = resp_data["choices"][0]["message"]["content"].strip()

    # 从响应中提取 JSON（模型有时会包裹在 ```json ... ``` 中）
    json_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", content)
    if json_match:
        content = json_match.group(1)

    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM 返回内容无法解析为 JSON：{content!r}") from e

    result["mode"] = "llm"
    return result


# ── CLI 入口 ──────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="将自然语言转换为 Xray XQL 查询参数",
        epilog=(
            "示例：\n"
            '  python nl_to_xql.py --text "查一下 my-service 最近 1 小时的 error 日志"\n'
            '  python nl_to_xql.py --text "查 edith.xiaohongshu.com 最近 30 分钟的 500 错误" --table rgw\n'
            '  python nl_to_xql.py --text "..." --llm-api-key sk-xxx\n\n'
            "对接 xray-cli（典型用法）：\n"
            "  PARSE=$(python3 nl_to_xql.py --text '...' --table rgw)\n"
            '  QUERY=$(echo "$PARSE" | jq -r .query)\n'
            '  ST=$(echo "$PARSE" | jq .st)\n'
            '  ET=$(echo "$PARSE" | jq .et)\n'
            '  xray-cli log query --table rgw --query "$QUERY" --st $ST --et $ET --output-format json'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--text", required=True, help="自然语言查询描述")
    parser.add_argument(
        "--llm-api-key",
        default=os.environ.get("LLM_API_KEY", ""),
        help="LLM API Key（也可通过环境变量 LLM_API_KEY 设置）",
    )
    parser.add_argument(
        "--llm-base-url",
        default=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
        help="LLM API Base URL，默认 https://api.openai.com/v1（也可通过 LLM_BASE_URL 设置）",
    )
    parser.add_argument(
        "--llm-model",
        default=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        help="LLM 模型名，默认 gpt-4o-mini（也可通过 LLM_MODEL 设置）",
    )
    parser.add_argument(
        "--force-rule",
        action="store_true",
        help="强制使用规则模式，即使配置了 LLM API Key",
    )
    parser.add_argument(
        "--table",
        default="application",
        help=f"目标日志表名，默认 application（可选值：{' / '.join(TABLE_CONFIGS.keys())}）",
    )
    args = parser.parse_args()

    use_llm = bool(args.llm_api_key) and not args.force_rule

    if use_llm:
        try:
            result = _parse_llm(
                text=args.text,
                api_key=args.llm_api_key,
                base_url=args.llm_base_url,
                model=args.llm_model,
                table=args.table,
            )
        except RuntimeError as e:
            # LLM 失败时降级到规则模式
            sys.stderr.write(f"[warn] LLM 模式失败，降级到规则模式：{e}\n")
            result = _parse_rule(args.text, table=args.table)
            result["llm_fallback"] = True
    else:
        result = _parse_rule(args.text, table=args.table)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 置信度 low 时以非零退出，提示调用方人工确认
    if result.get("confidence") == "low":
        sys.stderr.write(
            "[warn] 置信度较低，建议人工确认 query 是否符合预期，"
            "或使用 --llm-api-key 启用 LLM 模式以获得更准确的结果\n"
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
