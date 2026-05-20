#!/usr/bin/env python3
"""
XRay Span 批量查询脚本
调用 /analysisSearch 接口，支持两种模式：
  - ERROR（默认）: 查询异常 Span（status=1），可按 errorNames 过滤
  - SLOW         : 查询慢 Span（按耗时降序），可设定 minDurationMs 阈值 + topN 截断，
                   额外返回 durationStats（avg/p50/p90/p99）和耗时桶分布

用法：
    # ERROR 模式（默认，与旧版兼容）
    python3 analysis_search.py \
        --app xray-server \
        --start 1711339200 \
        --end 1711342800 \
        [--endpoint "Http./api/trace/search"] \
        [--error-names "TimeoutException,IOException"] \
        [--limit 500]

    # SLOW 模式
    python3 analysis_search.py \
        --app xray-server \
        --start 1711339200 \
        --end 1711342800 \
        --mode SLOW \
        [--endpoint "Service.com.xxx.SomeService"] \
        [--min-duration-ms 1000] \
        [--top-n 20] \
        [--limit 500]
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

API_URL = "https://xray-ai.devops.xiaohongshu.com/open/skill/tracing/analysisSearch"
TOP_N = 10  # Span 列表展示条数


def parse_args():
    parser = argparse.ArgumentParser(description="XRay Span 批量查询（支持 ERROR / SLOW 两种模式）")
    parser.add_argument("--app", required=True, help="服务名（必填）")
    parser.add_argument(
        "--start", required=True, type=int, help="开始时间（秒级 Unix 时间戳，必填）"
    )
    parser.add_argument("--end", required=True, type=int, help="结束时间（秒级 Unix 时间戳，必填）")
    parser.add_argument(
        "--endpoint",
        default=None,
        help="接口，格式 transactionType.transactionName（选填）",
    )
    # 搜索模式
    parser.add_argument(
        "--mode",
        default=None,
        choices=["ERROR", "SLOW"],
        help="搜索模式：ERROR（异常 Span，默认）/ SLOW（慢 Span）",
    )
    # ERROR 模式参数
    parser.add_argument(
        "--error-names",
        default=None,
        help="[ERROR 模式] 异常类型过滤，逗号分隔，如 TimeoutException,IOException",
    )
    # SLOW 模式参数
    parser.add_argument(
        "--min-duration-ms",
        type=int,
        default=None,
        help="[SLOW 模式] 耗时下限（毫秒），只返回 durationMs >= 该值的 Span",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="[SLOW 模式] 返回最慢的 Top N 条 Span，默认 10",
    )
    # 通用参数
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="返回条数上限，默认 500，最大 1000（选填）",
    )
    return parser.parse_args()


def build_payload(args):
    payload = {
        "app": args.app,
        "start": args.start,
        "end": args.end,
        "limit": min(args.limit, 1000),
    }
    if args.endpoint:
        payload["endpoint"] = args.endpoint
    if args.mode:
        payload["mode"] = args.mode

    effective_mode = args.mode or "ERROR"

    if effective_mode == "ERROR":
        if args.error_names:
            payload["errorNames"] = [e.strip() for e in args.error_names.split(",") if e.strip()]
    elif effective_mode == "SLOW":
        if args.min_duration_ms is not None:
            payload["minDurationMs"] = args.min_duration_ms
        if args.top_n is not None:
            payload["topN"] = args.top_n

    return payload


def call_api(payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[ERROR] 网络错误: {e.reason}", file=sys.stderr)
        sys.exit(1)


def fmt_dist(dist, top=10):
    """格式化分布 Map，取前 top 条，按 count 降序（API 已排序）。"""
    if not dist:
        return "  (无数据)"
    lines = []
    for i, (k, v) in enumerate(dist.items()):
        if i >= top:
            lines.append(f"  ... (共 {len(dist)} 项)")
            break
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def print_duration_stats(stats):
    """输出 SLOW 模式的耗时统计摘要。"""
    if not stats:
        return
    print("\n【耗时统计】")
    print(f"  采样数 : {stats.get('count', '-')}")
    print(f"  avg    : {stats.get('avgMs', '-')} ms")
    print(f"  min    : {stats.get('minMs', '-')} ms")
    print(f"  max    : {stats.get('maxMs', '-')} ms")
    print(f"  p50    : {stats.get('p50Ms', '-')} ms")
    print(f"  p90    : {stats.get('p90Ms', '-')} ms")
    print(f"  p99    : {stats.get('p99Ms', '-')} ms")


def print_duration_buckets(buckets):
    """输出 SLOW 模式的耗时桶分布。"""
    if not buckets:
        return
    print("\n【耗时分布】")
    for bucket, cnt in buckets.items():
        print(f"  {bucket}: {cnt}")


def print_results(resp, mode):
    if not resp.get("success"):
        print(
            f"[ERROR] 接口返回失败: code={resp.get('code')}, msg={resp.get('message')}",
            file=sys.stderr,
        )
        sys.exit(1)

    data = resp.get("data", {})
    total = data.get("total", 0)
    spans = data.get("spans", [])
    trace_ids = data.get("traceIds", [])
    agg = data.get("aggregation", {})

    effective_mode = mode or "ERROR"

    # --- 1. 概览 ---
    print("=" * 60)
    print(f"【概览】(模式: {effective_mode})")
    print(f"  命中 Span 总数  : {total}")
    print(f"  返回 Span 数    : {len(spans)}")
    print(f"  去重 traceId 数 : {len(trace_ids)}")

    # --- 2. SLOW 模式：耗时统计 + 桶分布 ---
    if effective_mode == "SLOW":
        print_duration_stats(agg.get("durationStats"))
        print_duration_buckets(agg.get("durationBucketDistribution"))

    # --- 3. 通用聚合分析 ---
    print("\n【聚合分析】")
    sections = [
        ("异常类型分布", "errorTypeDistribution"),
        ("接口分布", "spanNameDistribution"),
        ("Pod 分布", "podDistribution"),
        ("本端机房分布", "zoneDistribution"),
        ("下游机房分布", "downstreamZoneDistribution"),
        ("下游集群分布", "downstreamIpDistribution"),
        ("入口分布", "entryDistribution"),
    ]
    for label, key in sections:
        val = agg.get(key)
        if val:
            print(f"\n  [{label}]")
            print(fmt_dist(val))

    cross_zone = agg.get("crossZoneRatio")
    if cross_zone is not None:
        print(f"\n  [跨机房占比] {cross_zone:.2f}%")

    # --- 4. Span 列表摘要（前 TOP_N 条）---
    label = "慢 Span" if effective_mode == "SLOW" else "异常 Span"
    print(f"\n【{label}列表（前 {TOP_N} 条）】")
    for i, span in enumerate(spans[:TOP_N]):
        errs = ", ".join(span.get("errorTypes") or []) or "-"
        duration = span.get("durationMs", "-")
        print(
            f"  [{i + 1}] traceId={span.get('traceId')} | "
            f"duration={duration}ms | "
            f"type={span.get('spanType')} | "
            f"pod={span.get('podName')} | "
            f"zone={span.get('zone')} | "
            f"errors={errs}"
        )

    # --- 5. traceId 列表 ---
    print(f"\n【去重 traceId 列表（共 {len(trace_ids)} 条）】")
    for tid in trace_ids:
        print(f"  {tid}")

    if trace_ids:
        print("\n提示：可将 traceId 传入 xray-single-trace-analysis 做单链路深度分析。")

    print("=" * 60)


def main():
    args = parse_args()
    payload = build_payload(args)

    print(f"[INFO] 查询参数: {json.dumps(payload, ensure_ascii=False)}", file=sys.stderr)
    resp = call_api(payload)
    print_results(resp, args.mode)


if __name__ == "__main__":
    main()
