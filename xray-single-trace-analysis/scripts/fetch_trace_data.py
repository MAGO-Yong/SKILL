#!/usr/bin/env python3
"""根据 trace_id 请求链路分析接口并输出 JSON 数据。"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict
from urllib import error, parse, request

DEFAULT_ANALYSIS_URL = "https://xray-ai.devops.xiaohongshu.com/open/skill/tracing/traceid/analysis"


def parse_bool(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return "true"
    if normalized in {"false", "0", "no", "n"}:
        return "false"
    raise argparse.ArgumentTypeError("布尔值仅支持 true/false (或 1/0, yes/no)。")


def parse_header(raw: str) -> tuple[str, str]:
    if ":" not in raw:
        raise argparse.ArgumentTypeError("header 必须为 KEY:VALUE 格式。")
    key, value = raw.split(":", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        raise argparse.ArgumentTypeError("header 的 KEY 不能为空。")
    return key, value


def build_headers(extra_headers: list[str]) -> Dict[str, str]:
    headers: Dict[str, str] = {
        "Accept": "application/json",
        "xray_ticket": "pass",
    }

    for header in extra_headers:
        key, value = parse_header(header)
        headers[key] = value

    return headers


def fetch_trace_data(args: argparse.Namespace) -> dict:
    query = {
        "traceid": args.trace_id,
        "recoverTime": args.recover_time,
        "showMQConsumer": args.show_mq_consumer,
    }
    url = f"{args.base_url}?{parse.urlencode(query)}"
    headers = build_headers(args.header)

    req = request.Request(url=url, headers=headers, method="GET")
    with request.urlopen(req, timeout=args.timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError(f"接口返回不是合法 JSON: {exc}") from exc


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="根据 trace_id 请求链路分析接口并输出 JSON。")
    parser.add_argument("trace_id", help="要查询的 trace id")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_ANALYSIS_URL,
        help=f"链路分析接口地址（默认: {DEFAULT_ANALYSIS_URL}）",
    )
    parser.add_argument(
        "--recover-time",
        type=parse_bool,
        default="true",
        help="recoverTime 参数（默认: true）",
    )
    parser.add_argument(
        "--show-mq-consumer",
        type=parse_bool,
        default="true",
        help="showMQConsumer 参数（默认: true）",
    )
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        help="附加请求头，格式 KEY:VALUE，可重复传入",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15,
        help="请求超时时间（秒），默认 15",
    )
    parser.add_argument(
        "--output",
        help="可选：将返回 JSON 保存到指定文件路径",
    )
    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    try:
        data = fetch_trace_data(args)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"[HTTP {exc.code}] {detail}", file=sys.stderr)
        return 3
    except error.URLError as exc:
        print(f"[NETWORK ERROR] {exc.reason}", file=sys.stderr)
        return 4

    output_text = json.dumps(data, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_text)
            f.write("\n")

    print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
