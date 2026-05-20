#!/usr/bin/env python3
"""
RCM changeScore APIs: 产品线汇总、按操作人变更明细、变更不合规详情、RiskFree 覆盖缺口。
时间参数为 Unix 毫秒；未指定时间时默认东八区（UTC+8）「截至昨天结束的最近 7 天」。
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

# 默认自然日边界按东八区计算（与接口侧常见口径一致）
TZ_UTC8 = timezone(timedelta(hours=8))
TZ_UTC = timezone(timedelta(0))

# 明细里形如 ...+00:00 的尾缀
_TIME_TZ_SUFFIX = re.compile(r"([+-])(\d{2}):(\d{2})$")

DEFAULT_BASE = "https://rcm.devops.beta.xiaohongshu.com"
PATH_PRODUCT_LINE = "/api/changeScore/productLine"
PATH_NON_COMPLIANT = "/api/changeScore/nonCompliantChanges"
PATH_RISKFREE_GAPS = "/api/changeScore/riskFreeCoverageGaps"
PATH_OPERATOR = "/api/changeScore/operator"
PATH_USERS_BATCH = "/api/users/batchGet"
PATH_USERS_BY_SIGNATURE_ZH = "/api/users/bySignatureZh"

# 单次 batchGet 邮箱数量上限（避免请求体过大）
_USERS_BATCH_CHUNK = 80


def default_last_7_days_until_yesterday_end_ms():
    # type: () -> Tuple[int, int]
    """东八区日历：截至「东八区昨天」结束的最近 7 天 — 首日 00:00:00 至昨日 23:59:59.999（毫秒 UTC 时间戳）。"""
    now = datetime.now(TZ_UTC8)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    from_dt = yesterday_start - timedelta(days=6)
    to_dt = yesterday_start.replace(hour=23, minute=59, second=59, microsecond=999000)
    return (int(from_dt.timestamp() * 1000), int(to_dt.timestamp() * 1000))


def fetch_change_score_list(path, query, base_url=DEFAULT_BASE, timeout_s=60.0):
    # type: (str, Dict[str, str], str, float) -> Dict[str, Any]
    """GET /api/changeScore/* 并校验 code==200、data 为列表。"""
    base = base_url.rstrip("/")
    q = urllib.parse.urlencode(query)
    url = "{}?{}".format(base + path, q)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise SystemExit("HTTP {}: {}".format(e.code, e.reason)) from e
    except urllib.error.URLError as e:
        raise SystemExit("Request failed: {}".format(e.reason)) from e

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        raise SystemExit("Invalid JSON response: {}".format(e)) from e

    if payload.get("code") != 200:
        msg = payload.get("message") or payload.get("msg") or "unknown error"
        raise SystemExit("API error code={}: {}".format(payload.get("code"), msg))

    data = payload.get("data")
    if not isinstance(data, list):
        raise SystemExit("Response missing list field 'data'")
    return payload


def _http_get_json_object(url, timeout_s=60.0):
    # type: (str, float) -> Dict[str, Any]
    """GET JSON，校验 code==200，返回整份 payload。"""
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise SystemExit("HTTP {}: {}".format(e.code, e.reason)) from e
    except urllib.error.URLError as e:
        raise SystemExit("Request failed: {}".format(e.reason)) from e
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        raise SystemExit("Invalid JSON response: {}".format(e)) from e
    if payload.get("code") != 200:
        msg = payload.get("message") or payload.get("msg") or "unknown error"
        raise SystemExit("API error code={}: {}".format(payload.get("code"), msg))
    return payload


def _email_from_by_signature_zh_data(data):
    # type: (Dict[str, Any]) -> str
    """从 bySignatureZh 的 data 中取用于 RCM 查询的邮箱（须含 @）。"""
    for key in ("workEmail", "redMail", "operator"):
        v = data.get(key)
        if isinstance(v, str):
            t = v.strip()
            if t and "@" in t:
                return t
    return ""


def fetch_user_by_signature_zh(signature_zh, base_url=DEFAULT_BASE, timeout_s=60.0):
    # type: (str, str, float) -> Tuple[str, Dict[str, Any]]
    """
    GET /api/users/bySignatureZh?signatureZh=...
    返回 (工作邮箱, data 对象)。
    """
    sig = (signature_zh or "").strip()
    if not sig:
        raise SystemExit("署名为空")
    base = base_url.rstrip("/")
    q = urllib.parse.urlencode({"signatureZh": sig})
    url = "{}?{}".format(base + PATH_USERS_BY_SIGNATURE_ZH, q)
    payload = _http_get_json_object(url, timeout_s=timeout_s)
    data = payload.get("data")
    if not isinstance(data, dict):
        raise SystemExit("bySignatureZh: 响应缺少对象 data")
    # operator 常为工号/英文名（无 @），须优先用 workEmail / redMail 等工作邮箱
    em = _email_from_by_signature_zh_data(data)
    if not em:
        raise SystemExit(
            "bySignatureZh: 未解析到含 @ 的工作邮箱（请检查 workEmail / redMail）"
        )
    return (em, data)


def _operator_input_looks_like_email(s):
    # type: (str) -> bool
    t = (s or "").strip()
    return bool(t) and ("@" in t) and (not t.startswith("@"))


def resolve_operator_query_input(raw, base_url=DEFAULT_BASE, timeout_s=60.0):
    # type: (str, str, float) -> Tuple[str, Optional[Dict[str, Any]]]
    """
    --operator 可为邮箱或中文署名。
    署名时调用 bySignatureZh，返回 (邮箱, data)；邮箱时第二项为 None。
    """
    raw = (raw or "").strip()
    if not raw:
        raise SystemExit("operator 参数为空")
    if _operator_input_looks_like_email(raw):
        return (raw.strip(), None)
    email, meta = fetch_user_by_signature_zh(raw, base_url, timeout_s)
    return (email, meta)


def _label_from_signature_zh_data(d):
    # type: (Dict[str, Any]) -> str
    """bySignatureZh 的 data -> 与 batchGet displayName 同类的展示串。"""
    show = (d.get("showName") or "").strip()
    if show:
        return show
    red = (d.get("redName") or "").strip()
    un = (d.get("userName") or "").strip()
    if red and un:
        return "{}({})".format(red, un)
    if un:
        return un
    if red:
        return red
    return ""


def _user_record_to_display_label(u):
    # type: (Dict[str, Any]) -> str
    """接口字段 -> 「署名(真名)」：优先 displayName，否则 sname(name)。"""
    dn = (u.get("displayName") or "").strip()
    if dn:
        return dn
    sname = (u.get("sname") or "").strip()
    name = (u.get("name") or "").strip()
    if sname and name:
        return "{}({})".format(sname, name)
    if name:
        return name
    if sname:
        return sname
    em = (u.get("email") or "").strip()
    return em if em else "-"


def fetch_users_batch_display_map(emails, base_url=DEFAULT_BASE, timeout_s=60.0, chunk_size=_USERS_BATCH_CHUNK):
    # type: (List[str], str, float, int) -> Dict[str, str]
    """
    POST /api/users/batchGet，返回 email.lower() -> 展示文案。
    请求失败或未命中时，展示文案回退为原邮箱。
    """
    identity = {}  # type: Dict[str, str]
    seen = set()
    ordered = []  # type: List[str]
    for e in emails:
        if not e or not isinstance(e, str):
            continue
        raw = e.strip()
        if "@" not in raw:
            continue
        lk = raw.lower()
        if lk in seen:
            continue
        seen.add(lk)
        ordered.append(raw)
        identity[lk] = raw

    if not ordered:
        return {}

    base = base_url.rstrip("/")
    url = base + PATH_USERS_BATCH
    result = dict(identity)

    try:
        for i in range(0, len(ordered), chunk_size):
            chunk = ordered[i : i + chunk_size]
            body = json.dumps({"emails": chunk}, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                resp_body = resp.read().decode("utf-8")
            payload = json.loads(resp_body)
            if payload.get("code") != 200:
                msg = payload.get("message") or payload.get("msg") or "unknown error"
                raise ValueError("batchGet code={}: {}".format(payload.get("code"), msg))
            data = payload.get("data")
            if not isinstance(data, list):
                raise ValueError("batchGet missing list data")
            for u in data:
                if not isinstance(u, dict):
                    continue
                em = u.get("email")
                if not isinstance(em, str) or not em.strip():
                    continue
                lk = em.strip().lower()
                result[lk] = _user_record_to_display_label(u)
    except Exception as ex:
        print(
            "警告: 用户 batchGet 失败 ({}), 操作人展示回退为邮箱".format(ex),
            file=sys.stderr,
        )
        return identity

    return result


def collect_unique_operator_emails(rows):
    # type: (List[Dict[str, Any]]) -> List[str]
    out = []  # type: List[str]
    seen = set()
    for r in rows:
        if not isinstance(r, dict):
            continue
        op = r.get("operator")
        if isinstance(op, str) and "@" in op:
            raw = op.strip()
            lk = raw.lower()
            if lk not in seen:
                seen.add(lk)
                out.append(raw)
    return out


def apply_operator_display_to_payload(payload, op_map):
    # type: (Dict[str, Any], Dict[str, str]) -> Dict[str, Any]
    """为 data[] 增加 operatorDisplay；保留原 operator 邮箱。"""
    out = json.loads(json.dumps(payload))
    data = out.get("data")
    if not isinstance(data, list):
        return out
    for item in data:
        if not isinstance(item, dict):
            continue
        em = item.get("operator")
        if isinstance(em, str) and em.strip():
            lk = em.strip().lower()
            item["operatorDisplay"] = op_map.get(lk, em.strip())
    return out


def resolve_time_range(from_ms, to_ms, parser):
    # type: (Optional[int], Optional[int], argparse.ArgumentParser) -> Tuple[int, int]
    if (from_ms is None) ^ (to_ms is None):
        parser.error(
            "请同时提供 --from-time 与 --to-time，或两者都省略以使用默认（东八区昨天结束的最近 7 天）"
        )
    if from_ms is None and to_ms is None:
        from_ms, to_ms = default_last_7_days_until_yesterday_end_ms()
        print(
            "使用默认时间范围（东八区 UTC+8）：截至昨天结束的最近 7 天，"
            "fromTime={} toTime={}".format(from_ms, to_ms),
            file=sys.stderr,
        )
    assert from_ms is not None and to_ms is not None
    return (from_ms, to_ms)


def _fmt_pct(v: Any) -> str:
    if v is None:
        return "-"
    if isinstance(v, (int, float)):
        return "{:.4g}".format(v)
    return str(v)


def _trunc(s, max_len):
    # type: (Any, int) -> str
    t = "" if s is None else str(s)
    if len(t) <= max_len:
        return t
    return t[: max_len - 3] + "..."


def _strptime_api_datetime_body(body):
    # type: (str) -> Optional[datetime]
    """解析无时区后缀的日期时间主体为 naive datetime。"""
    body = body.strip()
    if not body:
        return None
    if "." in body:
        base, _, frac = body.partition(".")
        frac6 = (frac + "000000")[:6]
        composed = base + "." + frac6
        if "T" in composed:
            try:
                return datetime.strptime(composed, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                pass
        try:
            return datetime.strptime(composed, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            pass
    if "T" in body:
        try:
            return datetime.strptime(body, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass
    try:
        return datetime.strptime(body, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _parse_api_time_to_cst_aware(s):
    # type: (str) -> Optional[datetime]
    """
    将接口返回的时间字符串解析为「东八区」的 aware datetime。
    - 带 Z 或 ±HH:MM：按该时区解析后转为东八区；
    - 无时区后缀：按东八区墙钟时间理解（不位移）。
    """
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    if s.endswith("Z"):
        naive = _strptime_api_datetime_body(s[:-1].rstrip())
        if naive is None:
            return None
        return naive.replace(tzinfo=TZ_UTC).astimezone(TZ_UTC8)
    m = _TIME_TZ_SUFFIX.search(s)
    if m:
        body = s[: m.start()].rstrip()
        sign = 1 if m.group(1) == "+" else -1
        oh, om = int(m.group(2)), int(m.group(3))
        naive = _strptime_api_datetime_body(body)
        if naive is None:
            return None
        src_tz = timezone(timedelta(hours=sign * oh, minutes=sign * om))
        return naive.replace(tzinfo=src_tz).astimezone(TZ_UTC8)
    naive = _strptime_api_datetime_body(s)
    if naive is None:
        return None
    return naive.replace(tzinfo=TZ_UTC8)


def _format_detail_time_cst(value, max_len):
    # type: (Any, int) -> str
    """表格单元格：明细时间格式化为东八区 `YYYY-MM-DD HH:MM:SS`。"""
    if value is None:
        return _trunc("-", max_len)
    if not isinstance(value, str):
        value = str(value)
    dt_cst = _parse_api_time_to_cst_aware(value)
    if dt_cst is None:
        return _trunc(value, max_len)
    out = dt_cst.strftime("%Y-%m-%d %H:%M:%S")
    return _trunc(out, max_len)


def _start_time_to_cst_iso_string(s):
    # type: (str) -> str
    """JSON 输出：转为带东八区偏移的 ISO 字符串（毫秒三位）。"""
    dt_cst = _parse_api_time_to_cst_aware(s)
    if dt_cst is None:
        return s
    ms = dt_cst.microsecond // 1000
    return dt_cst.strftime("%Y-%m-%dT%H:%M:%S") + ".{:03d}+08:00".format(ms)


def rewrite_payload_start_times_cst(payload):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """为 data[] 中每条记录的 startTime 重写为东八区 ISO 字符串。"""
    out = json.loads(json.dumps(payload))
    data = out.get("data")
    if not isinstance(data, list):
        return out
    for item in data:
        if not isinstance(item, dict):
            continue
        st = item.get("startTime")
        if isinstance(st, str) and st.strip():
            item["startTime"] = _start_time_to_cst_iso_string(st)
    return out


def print_scores_table(rows):
    # type: (List[Dict[str, Any]]) -> None
    col_w = [20, 18, 20]
    for r in rows:
        pl = str(r.get("productLine") or "")
        col_w[0] = max(col_w[0], len(pl))
    line = "{}  {}  {}".format(
        "产品线".ljust(col_w[0]),
        "变更合规率%".rjust(col_w[1]),
        "RiskFree覆盖率%".rjust(col_w[2]),
    )
    print(line)
    print("-" * len(line))
    for r in rows:
        pl = str(r.get("productLine") or "")
        cr = _fmt_pct(r.get("complianceRate"))
        rf = _fmt_pct(r.get("riskFreeCoverage"))
        print(
            "{}  {}  {}".format(
                pl.ljust(col_w[0]),
                cr.rjust(col_w[1]),
                rf.rjust(col_w[2]),
            )
        )


def print_non_compliant_table(rows, op_map=None):
    # type: (List[Dict[str, Any]], Optional[Dict[str, str]]) -> None
    cols = [
        ("资源", "resourceName", 28),
        ("变更类型", "changeTypeCn", 18),
        ("不合规原因", "nonComplianceReason", 22),
        ("操作人", "operator", 22),
        ("开始时间", "startTime", 22),
        ("链接", "changeUrl", 40),
    ]
    widths = [w for _, _, w in cols]
    sep = "  "
    header = sep.join(h.ljust(widths[i]) for i, (h, _, _) in enumerate(cols))
    print(header)
    print("-" * len(header))
    for r in rows:
        cells = []
        for i, (_, key, w) in enumerate(cols):
            raw = r.get(key)
            if key == "changeUrl":
                cells.append(_trunc(raw, w).ljust(w))
            elif key == "startTime":
                cells.append(_format_detail_time_cst(raw, w).ljust(w))
            elif key == "operator":
                if isinstance(raw, str) and raw.strip() and op_map:
                    label = op_map.get(raw.strip().lower(), raw.strip())
                else:
                    label = raw
                cells.append(_trunc(label, w).ljust(w))
            else:
                cells.append(_trunc(raw, w).ljust(w))
        print(sep.join(cells))


def _fmt_qualified(v):
    # type: (Any) -> str
    if v is True:
        return "是"
    if v is False:
        return "否"
    return "-"


def print_operator_table(rows, op_map=None):
    # type: (List[Dict[str, Any]], Optional[Dict[str, str]]) -> None
    cols = [
        ("资源", "resourceName", 24),
        ("操作人", "operator", 18),
        ("系统", "changeSystemCn", 12),
        ("变更类型", "changeTypeCn", 12),
        ("合规", "_qualified", 6),
        ("不合规原因", "nonComplianceReason", 18),
        ("开始时间", "startTime", 20),
        ("链接", "changeUrl", 32),
    ]
    widths = [w for _, _, w in cols]
    sep = "  "
    header = sep.join(h.ljust(widths[i]) for i, (h, _, _) in enumerate(cols))
    print(header)
    print("-" * len(header))
    for r in rows:
        line_parts = []
        for _, key, w in cols:
            if key == "_qualified":
                s = _fmt_qualified(r.get("qualified"))
            elif key == "startTime":
                s = _format_detail_time_cst(r.get("startTime"), w)
            elif key == "operator":
                v = r.get("operator")
                if isinstance(v, str) and v.strip() and op_map:
                    s = _trunc(op_map.get(v.strip().lower(), v.strip()), w)
                else:
                    s = _trunc(v, w)
            else:
                v = r.get(key)
                s = _trunc(v, w)
            line_parts.append(s.ljust(w))
        print(sep.join(line_parts))


def print_riskfree_gaps_table(rows):
    # type: (List[Dict[str, Any]]) -> None
    cols = [
        ("资源", "resourceName", 30),
        ("类型", "resourceType", 12),
        ("产品线", "haProductLineCn", 10),
        ("场景", "haSceneCn", 10),
        ("规则数", "ruleCount", 8),
        ("开始时间", "startTime", 20),
        ("缺口原因", "gapReason", 28),
    ]
    widths = [w for _, _, w in cols]
    sep = "  "
    header = sep.join(h.ljust(widths[i]) for i, (h, _, _) in enumerate(cols))
    print(header)
    print("-" * len(header))
    for r in rows:
        line_parts = []
        for i, (_, key, w) in enumerate(cols):
            v = r.get(key)
            if key == "ruleCount" and v is not None:
                s = str(v)
            elif key == "startTime":
                s = _format_detail_time_cst(v, w)
            else:
                s = _trunc(v, w)
            line_parts.append(s.ljust(w))
        print(sep.join(line_parts))


def main():
    # type: () -> None
    p = argparse.ArgumentParser(
        description="查询 RCM 变更合规：产品线汇总 / 操作人变更明细 / 不合规列表 / RiskFree 覆盖缺口",
    )
    p.add_argument(
        "--fetch",
        choices=("scores", "operator", "non-compliant", "riskfree-gaps"),
        default="scores",
        help="scores=产品线汇总；operator=按操作人变更明细；non-compliant=产品线不合规详情；riskfree-gaps=RiskFree 未覆盖详情",
    )
    p.add_argument(
        "--operator",
        dest="operator",
        default=None,
        help="操作人：工作邮箱 user@xiaohongshu.com，或中文署名（如 从之）；署名将先调 bySignatureZh 换邮箱",
    )
    p.add_argument(
        "--product-line",
        dest="product_line",
        default=None,
        help="产品线编码（如 rec），与 non-compliant、riskfree-gaps 同时使用",
    )
    p.add_argument(
        "--from-time",
        type=int,
        default=None,
        dest="from_time",
        help="开始时间（毫秒，fromTime）；省略则与 --to-time 同时省略，使用默认区间（东八区自然日）",
    )
    p.add_argument(
        "--to-time",
        type=int,
        default=None,
        dest="to_time",
        help="结束时间（毫秒，toTime）；省略则与 --from-time 同时省略，使用默认区间（东八区自然日）",
    )
    p.add_argument(
        "--base-url",
        default=DEFAULT_BASE,
        help="API 根地址（默认: {}）".format(DEFAULT_BASE),
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="输出完整 JSON；明细会重写 startTime 为东八区；operator/non-compliant 增加 operatorDisplay",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="HTTP 超时秒数",
    )
    args = p.parse_args()

    if args.fetch in ("non-compliant", "riskfree-gaps") and not args.product_line:
        p.error("--fetch {} 时必须提供 --product-line（如 rec）".format(args.fetch))
    if args.fetch == "operator" and not args.operator:
        p.error("--fetch operator 时必须提供 --operator（邮箱或中文署名）")

    from_ms, to_ms = resolve_time_range(args.from_time, args.to_time, p)

    if from_ms > to_ms:
        print("警告: from-time 大于 to-time", file=sys.stderr)

    operator_query_email = None  # type: Optional[str]
    operator_sig_meta = None  # type: Optional[Dict[str, Any]]
    if args.fetch == "operator":
        operator_query_email, operator_sig_meta = resolve_operator_query_input(
            args.operator, base_url=args.base_url, timeout_s=args.timeout
        )
        if operator_sig_meta is not None:
            print(
                "已通过署名解析操作人邮箱: 「{}」 -> {}".format(
                    args.operator.strip(), operator_query_email
                ),
                file=sys.stderr,
            )

    if args.fetch == "scores":
        query = {"fromTime": str(from_ms), "toTime": str(to_ms)}
        path = PATH_PRODUCT_LINE
    elif args.fetch == "operator":
        query = {
            "operator": operator_query_email,
            "fromTime": str(from_ms),
            "toTime": str(to_ms),
        }
        path = PATH_OPERATOR
    elif args.fetch == "non-compliant":
        query = {
            "productLine": args.product_line,
            "fromTime": str(from_ms),
            "toTime": str(to_ms),
        }
        path = PATH_NON_COMPLIANT
    else:
        query = {
            "productLine": args.product_line,
            "fromTime": str(from_ms),
            "toTime": str(to_ms),
        }
        path = PATH_RISKFREE_GAPS

    payload = fetch_change_score_list(
        path,
        query,
        base_url=args.base_url,
        timeout_s=args.timeout,
    )

    op_map = {}  # type: Dict[str, str]
    op_map_prefill = {}  # type: Dict[str, str]
    if args.fetch == "operator" and operator_sig_meta and operator_query_email:
        lab = _label_from_signature_zh_data(operator_sig_meta)
        if lab:
            op_map_prefill[operator_query_email.strip().lower()] = lab

    if args.fetch in ("operator", "non-compliant"):
        emails = collect_unique_operator_emails(payload.get("data") or [])
        if emails:
            op_map = fetch_users_batch_display_map(
                emails, base_url=args.base_url, timeout_s=args.timeout
            )
        for lk, lab in op_map_prefill.items():
            if lab:
                op_map[lk] = lab

    if args.as_json:
        to_dump = payload
        if args.fetch in ("operator", "non-compliant", "riskfree-gaps"):
            to_dump = rewrite_payload_start_times_cst(payload)
        if args.fetch in ("operator", "non-compliant"):
            to_dump = apply_operator_display_to_payload(to_dump, op_map)
        print(json.dumps(to_dump, ensure_ascii=False, indent=2))
        return

    data = payload.get("data") or []
    if args.fetch == "scores":
        print_scores_table(data)
    elif args.fetch == "operator":
        print_operator_table(data, op_map)
    elif args.fetch == "non-compliant":
        print_non_compliant_table(data, op_map)
    else:
        print_riskfree_gaps_table(data)


if __name__ == "__main__":
    main()
