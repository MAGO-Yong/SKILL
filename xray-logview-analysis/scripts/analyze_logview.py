#!/usr/bin/env python3
"""
XRay Logview 分析脚本

用法:
    python3 analyze_logview.py <messageId> --base-url <url>
    python3 analyze_logview.py --json <file>   # 直接分析本地 JSON 文件

输出: 结构化分析报告（Markdown 格式）
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional


# ─────────────────────────────────────────────
# 数据获取
# ─────────────────────────────────────────────


def fetch_logview(base_url: str, message_id: str) -> dict:
    url = f"{base_url.rstrip('/')}/open/skill/application/r/logview/{message_id}/json"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] HTTP {e.code}: {e.reason}", file=sys.stderr)
        print(f"[ERROR] 响应体: {body[:500]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 请求失败: {e}", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────────────────────
# 分析逻辑
# ─────────────────────────────────────────────


@dataclass
class NodeStat:
    type: str
    name: str
    duration_ms: float
    status: str
    error: bool
    data: str
    depth: int
    parent_type: str = ""
    parent_name: str = ""
    children_count: int = 0


def walk(node: dict, depth: int = 0, stats: list = None) -> list:
    if stats is None:
        stats = []
    if node is None:
        return stats

    duration = node.get("durationInMillis", -1)
    stat = NodeStat(
        type=node.get("type", ""),
        name=node.get("name", ""),
        duration_ms=duration,
        status=node.get("status", ""),
        error=node.get("error", False),
        data=node.get("data", ""),
        depth=depth,
        parent_type=node.get("parentType", ""),
        parent_name=node.get("parentName", ""),
    )

    children = node.get("children") or []
    stat.children_count = len(children)
    stats.append(stat)

    for child in children:
        walk(child, depth + 1, stats)

    return stats


def parse_data_kv(data: str) -> dict:
    result = {}
    if not data:
        return result
    for part in data.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            result[k.strip()] = v.strip()
    return result


# ─────────────────────────────────────────────
# 报告生成
# ─────────────────────────────────────────────


def format_duration(ms: float) -> str:
    if ms < 0:
        return "—"
    if ms >= 1000:
        return f"{ms / 1000:.2f}s"
    return f"{ms:.1f}ms"


def report(raw: dict) -> str:
    data = raw.get("data", raw)  # 兼容 {data: {...}} 和直接 {...}
    code = data.get("code", 200)
    lines = []

    # ── 基本信息 ──
    lines.append("## Logview 分析报告\n")
    lines.append(f"| 字段 | 值 |")
    lines.append(f"|------|----|")
    lines.append(f"| 服务 | `{data.get('domain', '?')}` |")
    lines.append(f"| 主机 | `{data.get('hostName', '?')}` |")
    lines.append(f"| IP | `{data.get('ipAddress', '?')}` |")
    lines.append(f"| 可用区 | `{data.get('zone', '?')}` |")
    lines.append(f"| 开始时间 | `{data.get('startTime', '?')}` |")
    lines.append(f"| 总耗时 | `{format_duration(data.get('durationInMills', -1))}` |")
    lines.append(f"| MessageId | `{data.get('messageId', '?')}` |")
    lines.append(f"| RootMessageId | `{data.get('rootMessageId', '?')}` |")
    lines.append(f"| TraceId | `{data.get('traceId', '?')}` |")
    lines.append(f"| 数据状态 | `{code}` {'✓' if code == 200 else '⚠️ 数据缺失/已过期'} |")
    lines.append("")

    if code != 200:
        msg = {1003: "数据缺失（在保留期内未找到）", 1004: "数据已过期归档"}.get(
            code, f"未知状态码 {code}"
        )
        lines.append(f"> **注意**: {msg}\n")
        return "\n".join(lines)

    message = data.get("message")
    if not message:
        lines.append("> 消息树为空，无法继续分析\n")
        return "\n".join(lines)

    stats = walk(message)
    transactions = [s for s in stats if s.duration_ms >= 0]
    events = [s for s in stats if s.duration_ms < 0]
    errors = [s for s in stats if s.error]

    # ── 统计摘要 ──
    lines.append("## 统计摘要\n")
    lines.append(f"| 指标 | 值 |")
    lines.append(f"|------|----|")
    lines.append(f"| 总节点数 | {len(stats)} |")
    lines.append(f"| Transaction 数 | {len(transactions)} |")
    lines.append(f"| Event 数 | {len(events)} |")
    lines.append(f"| 异常节点数 | **{len(errors)}** |")
    lines.append("")

    # ── 异常分析 ──
    if errors:
        lines.append("## 异常节点\n")
        for e in errors:
            lines.append(f"- **[{e.type}]** `{e.name}`")
            lines.append(f"  - 父节点: `{e.parent_type}` / `{e.parent_name}`")
        lines.append("")

    # ── 失败 Transaction ──
    failed = [s for s in transactions if s.status not in ("", "0", "success", "SUCCESS", "true")]
    if failed:
        lines.append("## 失败的 Transaction\n")
        for s in failed:
            lines.append(
                f"- **[{s.type}]** `{s.name}` — 耗时 {format_duration(s.duration_ms)} — status: `{s.status}`"
            )
            if s.data:
                lines.append(f"  - data: `{s.data}`")
        lines.append("")

    # ── 耗时 TOP10 ──
    top = sorted(transactions, key=lambda x: x.duration_ms, reverse=True)[:10]
    lines.append("## 耗时 TOP 10 节点\n")
    lines.append("| # | 类型 | 名称 | 耗时 | 状态 | SLA |")
    lines.append("|---|------|------|------|------|-----|")
    for i, s in enumerate(top, 1):
        kv = parse_data_kv(s.data)
        sla = kv.get("slaLevel", "—")
        strong = kv.get("strongDependence", "")
        sla_str = f"L{sla}" if sla != "—" else "—"
        if strong == "true":
            sla_str += " 强依赖"
        status_icon = "✓" if s.status in ("", "0", "success", "SUCCESS", "true") else "✗"
        lines.append(
            f"| {i} | `{s.type}` | `{s.name}` | {format_duration(s.duration_ms)} | {status_icon} | {sla_str} |"
        )
    lines.append("")

    # ── 调用链概览（前30节点） ──
    lines.append("## 调用链（树形结构）\n")
    lines.append("```")
    for s in stats[:30]:
        indent = "  " * s.depth
        duration_str = f" [{format_duration(s.duration_ms)}]" if s.duration_ms >= 0 else ""
        error_mark = " ⚠️" if s.error else ""
        fail_mark = (
            " ✗"
            if s.status not in ("", "0", "success", "SUCCESS", "true", "-1") and s.status
            else ""
        )
        lines.append(f"{indent}[{s.type}] {s.name}{duration_str}{error_mark}{fail_mark}")
    if len(stats) > 30:
        lines.append(f"  ... (共 {len(stats)} 个节点，仅显示前 30 个)")
    lines.append("```")
    lines.append("")

    # ── 性能瓶颈分析 ──
    total_ms = data.get("durationInMills", 0) or 0
    if total_ms > 0:
        lines.append("## 性能瓶颈分析\n")
        bottlenecks = [s for s in top if s.duration_ms / total_ms > 0.3]
        if bottlenecks:
            for s in bottlenecks:
                pct = s.duration_ms / total_ms * 100
                lines.append(
                    f"- `{s.type}` / `{s.name}` 占总耗时 **{pct:.1f}%** ({format_duration(s.duration_ms)})"
                )
        else:
            lines.append("_未发现明显瓶颈（单节点耗时均 < 总耗时30%）_")
        lines.append("")

    # ── 依赖健康 ──
    call_nodes = [s for s in transactions if s.type in ("Call", "PigeonCall")]
    if call_nodes:
        lines.append("## 下游依赖调用\n")
        lines.append("| 服务 | 耗时 | 状态 | SLA等级 | 强依赖 |")
        lines.append("|------|------|------|---------|--------|")
        for s in call_nodes:
            kv = parse_data_kv(s.data)
            sla = kv.get("slaLevel", "—")
            strong = kv.get("strongDependence", "—")
            status_icon = "✓" if s.status in ("", "0", "success", "SUCCESS", "true") else "✗"
            lines.append(
                f"| `{s.name}` | {format_duration(s.duration_ms)} | {status_icon} | {sla} | {strong} |"
            )
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="XRay Logview 分析工具")
    parser.add_argument("message_id", nargs="?", help="CAT MessageId")
    parser.add_argument(
        "--base-url",
        default="https://xray-ai.devops.xiaohongshu.com",
        help="xray 平台地址，默认 https://xray-ai.devops.xiaohongshu.com",
    )
    parser.add_argument("--json", help="直接读取本地 JSON 文件进行分析")
    parser.add_argument("--output", default="-", help="输出文件（默认 stdout）")
    args = parser.parse_args()

    if args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            raw = json.load(f)
    elif args.message_id:
        raw = fetch_logview(args.base_url, args.message_id)
    else:
        parser.print_help()
        print(
            "\n[ERROR] 必须提供 message_id，或使用 --json 指定本地文件",
            file=sys.stderr,
        )
        sys.exit(1)

    result = report(raw)

    if args.output == "-":
        print(result)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"报告已写入: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
