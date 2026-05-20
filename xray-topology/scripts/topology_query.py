#!/usr/bin/env python3
"""
XRay 拓扑查询脚本
支持三种模式：
  - SERVICE（默认）: 查询服务拓扑，POST /searchAdvancedRpcTopology，时间单位秒
  - ENTRY          : 查询流量入口拓扑，POST /searchEntryTopology，时间单位毫秒
  - CAT            : 查询 CAT 拓扑（降级/树形），GET /application/topology/serviceTopology

用法：
    # SERVICE 模式
    python3 topology_query.py \\
        --mode SERVICE \\
        --app checkoutcenter-service-defaultunit \\
        --start 1776152576 \\
        --end 1776153476 \\
        [--service "com.xxx.SomeService.someMethod"] \\
        [--focus-option "direct_relations_each_direction_top10"]

    # ENTRY 模式
    python3 topology_query.py \\
        --mode ENTRY \\
        --entry "mall.xiaohongshu.com/api/store/sc" \\
        --start-ms 1776152789849 \\
        --end-ms 1776153689849 \\
        [--level app]

    # CAT 模式
    python3 topology_query.py \\
        --mode CAT \\
        --app checkoutcenter-service-defaultunit \\
        --start 1776067439 \\
        --end 1776153839 \\
        [--with-api false]
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error

BASE_URL = "https://xray-ai.devops.xiaohongshu.com/open/skill/tracing"
SERVICE_TOPO_URL = f"{BASE_URL}/searchAdvancedRpcTopology"
ENTRY_TOPO_URL = f"{BASE_URL}/searchEntryTopology"
CAT_TOPO_URL = (
    "http://xray-ai.devops.xiaohongshu.com/open/skill/application/topology/serviceTopology"
)


def http_post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 请求失败: {e}", file=sys.stderr)
        sys.exit(1)


def http_get(url: str, params: dict) -> dict:
    query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    full_url = f"{url}?{query}" if query else url
    req = urllib.request.Request(full_url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 请求失败: {e}", file=sys.stderr)
        sys.exit(1)


# ──────────────────────────────────────────────────────────────
# SERVICE 模式
# ──────────────────────────────────────────────────────────────


def query_service_topology(args):
    payload = {
        "app": args.app,
        "start": args.start,
        "end": args.end,
        "focusOption": args.focus_option,
        "preProcessEnum": args.pre_process,
        "perfTestInclude": args.perf_test,
    }
    if args.service:
        payload["service"] = args.service
    if args.entry_list:
        payload["entryList"] = args.entry_list.split(",")

    print(f"[INFO] 查询服务拓扑: app={args.app}", file=sys.stderr)
    resp = http_post(SERVICE_TOPO_URL, payload)

    if not resp.get("success"):
        print(f"[ERROR] 接口返回失败: {resp.get('message', '未知错误')}", file=sys.stderr)
        sys.exit(1)

    data = resp.get("data", {})
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    rows = data.get("rows", [])
    default_node_id = data.get("defaultNodeId")

    if not nodes:
        print(
            "[WARN] 服务拓扑无数据（nodes 为空），建议改用 --mode CAT 重查",
            file=sys.stderr,
        )
        print(json.dumps({"empty": True, "suggestion": "use --mode CAT"}))
        return

    print_service_topology(nodes, edges, rows, default_node_id, args.app)


def print_service_topology(nodes, edges, rows, default_node_id, app):
    node_map = {n["id"]: n for n in nodes}

    # 核心节点
    core_node = None
    if default_node_id and default_node_id in node_map:
        core_node = node_map[default_node_id]

    print(f"\n## 服务拓扑：{app}")
    print(f"{'=' * 60}")

    if core_node and core_node.get("withMetrics"):
        print(f"\n### 核心节点：{core_node.get('name')}")
        print(f"  - 调用次数 : {core_node.get('totalStr', core_node.get('total'))}")
        print(f"  - 平均耗时 : {core_node.get('avgDurationStr', core_node.get('avgDuration'))}")
        print(f"  - 最大耗时 : {core_node.get('maxDurationStr', core_node.get('maxDuration'))}")
        print(f"  - 错误次数 : {core_node.get('errorStr', core_node.get('error'))}")
        tags = core_node.get("tags", [])
        if tags:
            for tag in tags:
                print(f"  - 标签     : {tag.get('message', '')}")

    # 按 source/target 分类 edges
    upstream_edges = []  # edges 指向 core_node 的（source 不是 core，target 是 core）
    downstream_edges = []  # edges 从 core_node 出发的

    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        if tgt == default_node_id:
            upstream_edges.append(edge)
        elif src == default_node_id:
            downstream_edges.append(edge)

    # 上游来源
    if upstream_edges:
        upstream_edges.sort(key=lambda e: e.get("total", 0), reverse=True)
        print(f"\n### 上游来源（共 {len(upstream_edges)} 个）")
        print(f"  {'调用方':<40} {'调用次数':<15} {'平均耗时':<12} {'放大倍数'}")
        print(f"  {'-' * 40} {'-' * 15} {'-' * 12} {'-' * 10}")
        for edge in upstream_edges[:20]:  # 最多展示 20 条
            src_app = edge.get("sourceApp", "?")
            src_svc = edge.get("sourceService") or ""
            caller = f"{src_app}" + (f".{src_svc}" if src_svc else "")
            total_str = edge.get("totalStr", str(edge.get("total", 0)))
            avg_str = edge.get("avgDurationStr", "-")
            mag_str = edge.get("magnificationStr", "-")
            print(f"  {caller:<40} {total_str:<15} {avg_str:<12} {mag_str}")
            # 入口列表（最多 5 个）
            entry_set = list(edge.get("entrySet") or [])[:5]
            if entry_set:
                for entry in entry_set:
                    print(f"    ↳ {entry}")

    # 下游依赖
    if downstream_edges:
        downstream_edges.sort(key=lambda e: e.get("total", 0), reverse=True)
        print(f"\n### 下游依赖（共 {len(downstream_edges)} 个）")
        print(f"  {'被调用方':<40} {'类型':<8} {'调用次数':<15} {'平均耗时':<12} {'错误次数'}")
        print(f"  {'-' * 40} {'-' * 8} {'-' * 15} {'-' * 12} {'-' * 10}")
        for edge in downstream_edges[:30]:  # 最多展示 30 条
            tgt_app = edge.get("targetApp", "?")
            tgt_svc = edge.get("targetService") or ""
            callee = f"{tgt_app}" + (f".{tgt_svc}" if tgt_svc else "")
            edge_type = edge.get("edgeType", "-")
            total_str = edge.get("totalStr", str(edge.get("total", 0)))
            avg_str = edge.get("avgDurationStr", "-")
            error_str = edge.get("errorStr", "-")
            print(f"  {callee:<40} {edge_type:<8} {total_str:<15} {avg_str:<12} {error_str}")

    # 告警节点
    warn_nodes = [n for n in nodes if n.get("status") not in ("info", None)]
    if warn_nodes:
        print(f"\n### 健康告警节点（{len(warn_nodes)} 个）")
        for n in warn_nodes:
            tags = [t.get("message", "") for t in (n.get("tags") or [])]
            print(f"  - {n.get('name')}: {', '.join(tags)}")

    print(f"\n{'=' * 60}")


# ──────────────────────────────────────────────────────────────
# ENTRY 模式
# ──────────────────────────────────────────────────────────────


def query_entry_topology(args):
    entry_list = [e.strip() for e in args.entry.split(",")]
    payload = {
        "entryList": entry_list,
        "level": args.level,
        "startTime": args.start_ms,
        "endTime": args.end_ms,
        "summingAllSource": not args.split_source,
        "preProcessEnum": args.pre_process,
        "perfTestInclude": args.perf_test,
    }

    print(f"[INFO] 查询流量入口拓扑: entryList={entry_list}", file=sys.stderr)
    resp = http_post(ENTRY_TOPO_URL, payload)

    if not resp.get("success"):
        print(f"[ERROR] 接口返回失败: {resp.get('message', '未知错误')}", file=sys.stderr)
        sys.exit(1)

    data = resp.get("data", {})
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    default_node_id = data.get("defaultNodeId")

    if not nodes:
        print("[WARN] 流量入口拓扑无数据（nodes 为空）", file=sys.stderr)
        print(json.dumps({"empty": True}))
        return

    print(f"\n## 流量入口拓扑：{', '.join(entry_list)}")
    # 复用 SERVICE 模式的打印逻辑
    print_service_topology(nodes, edges, edges, default_node_id, ", ".join(entry_list))


# ──────────────────────────────────────────────────────────────
# CAT 模式
# ──────────────────────────────────────────────────────────────


def query_cat_topology(args):
    params = {
        "app": args.app,
        "withApi": str(args.with_api).lower(),
    }
    if args.start:
        params["startTime"] = args.start
    if args.end:
        params["endTime"] = args.end

    print(f"[INFO] 查询 CAT 拓扑: app={args.app}", file=sys.stderr)
    resp = http_get(CAT_TOPO_URL, params)

    if not resp.get("success"):
        print(f"[ERROR] 接口返回失败: {resp.get('message', '未知错误')}", file=sys.stderr)
        sys.exit(1)

    data = resp.get("data", {})
    topo_node = data.get("topologyNode", {})
    print_cat_topology(topo_node, args.app)


def print_cat_topology(node, app):
    print(f"\n## CAT 拓扑：{app}")
    print(f"{'=' * 60}")

    children = node.get("children", [])
    for section in children:
        section_id = section.get("id")
        if section_id == "upstream":
            items = section.get("children", [])
            print(f"\n### 上游（共 {len(items)} 个）")
            for item in items:
                call_type = item.get("callType", "RPC")
                print(f"  - [{call_type}] {item.get('name')}")
        elif section_id == "downstream":
            items = section.get("children", [])
            print(f"\n### 下游（共 {len(items)} 个）")
            for item in items:
                call_type = item.get("callType", "RPC")
                print(f"  - [{call_type}] {item.get('name')}")

    print(f"\n{'=' * 60}")
    print("[INFO] CAT 拓扑为树形结构，无性能指标。如需性能指标，请使用 SERVICE 模式。")


# ──────────────────────────────────────────────────────────────
# 参数解析
# ──────────────────────────────────────────────────────────────


def parse_args():
    parser = argparse.ArgumentParser(
        description="XRay 拓扑查询（支持 SERVICE / ENTRY / CAT 三种模式）"
    )
    parser.add_argument(
        "--mode",
        choices=["SERVICE", "ENTRY", "CAT"],
        default="SERVICE",
        help="查询模式（默认 SERVICE）",
    )

    # 时间参数
    parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="开始时间（秒级时间戳，SERVICE/CAT 模式，默认 now-1h）",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="结束时间（秒级时间戳，SERVICE/CAT 模式，默认 now）",
    )
    parser.add_argument(
        "--start-ms",
        type=int,
        dest="start_ms",
        default=None,
        help="开始时间（毫秒时间戳，ENTRY 模式，默认 now-1h）",
    )
    parser.add_argument(
        "--end-ms",
        type=int,
        dest="end_ms",
        default=None,
        help="结束时间（毫秒时间戳，ENTRY 模式，默认 now）",
    )

    # SERVICE / CAT 参数
    parser.add_argument("--app", help="服务名（SERVICE/CAT 模式必填）")
    parser.add_argument("--service", help="RPC 接口名（SERVICE 模式可选）")
    parser.add_argument(
        "--focus-option",
        dest="focus_option",
        default="direct_relations_each_direction_top10",
        help="关注维度（SERVICE 模式，默认 direct_relations_each_direction_top10）",
    )
    parser.add_argument(
        "--pre-process",
        dest="pre_process",
        default="RPC",
        choices=["RPC", "RPC_DATA", "RPC_DATA_IGNORE_OP"],
        help="调用类型过滤（默认 RPC）",
    )
    parser.add_argument(
        "--perf-test",
        dest="perf_test",
        default="UNION_PERF_TEST",
        choices=["UNION_PERF_TEST", "NO_PERF_TEST", "ONLY_PERF_TEST"],
        help="压测流量策略（默认 UNION_PERF_TEST）",
    )
    parser.add_argument(
        "--entry-list",
        dest="entry_list",
        help="额外入口列表，逗号分隔（SERVICE 模式可选）",
    )

    # ENTRY 参数
    parser.add_argument("--entry", help="HTTP 入口 URL，多个用逗号分隔（ENTRY 模式必填）")
    parser.add_argument(
        "--level",
        default="app",
        choices=["app", "service"],
        help="拓扑粒度（ENTRY 模式，默认 app）",
    )
    parser.add_argument(
        "--split-source",
        dest="split_source",
        action="store_true",
        default=False,
        help="区分调用来源（ENTRY 模式，默认合并所有来源）",
    )

    # CAT 参数
    parser.add_argument(
        "--with-api",
        dest="with_api",
        action="store_true",
        default=False,
        help="包含 API 维度（CAT 模式，默认 false）",
    )

    return parser.parse_args()


def apply_default_time(args):
    """若未提供时间参数，默认查最近 1 小时。"""
    now_s = int(time.time())
    now_ms = now_s * 1000
    if args.end is None:
        args.end = now_s
    if args.start is None:
        args.start = now_s - 3600
    if args.end_ms is None:
        args.end_ms = now_ms
    if args.start_ms is None:
        args.start_ms = now_ms - 3600 * 1000


def main():
    args = parse_args()
    apply_default_time(args)

    if args.mode == "SERVICE":
        if not args.app:
            print("[ERROR] SERVICE 模式必须提供 --app 参数", file=sys.stderr)
            sys.exit(1)
        query_service_topology(args)

    elif args.mode == "ENTRY":
        if not args.entry:
            print("[ERROR] ENTRY 模式必须提供 --entry 参数", file=sys.stderr)
            sys.exit(1)
        query_entry_topology(args)

    elif args.mode == "CAT":
        if not args.app:
            print("[ERROR] CAT 模式必须提供 --app 参数", file=sys.stderr)
            sys.exit(1)
        query_cat_topology(args)


if __name__ == "__main__":
    main()
