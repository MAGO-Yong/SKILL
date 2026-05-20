#!/usr/bin/env python3
"""
统一指标查询客户端
支持五种查询模式: system（模板指标）、pql（PromQL）、cat（Cat 指标）、cat-meta（Cat 元数据）、samples（Cat samples 下钻）
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "http://xray-ai.devops.xiaohongshu.com/open/skill/metric/proxy"
CAT_META_URL = "http://xray-ai.devops.xiaohongshu.com/open/skill/application/r/s/metas"
TIMEOUT = 120


def call_api(mode, payload):
    url = f"{BASE_URL}/{ENDPOINTS[mode]}"
    print(f"请求: POST {url}", file=sys.stderr)
    print(f"参数: {json.dumps(payload, ensure_ascii=False, indent=2)}", file=sys.stderr)
    print(file=sys.stderr)

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            if resp.status != 200:
                body = resp.read().decode("utf-8", errors="replace")
                print(f"错误: HTTP {resp.status} — {body[:500]}", file=sys.stderr)
                sys.exit(1)
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"错误: HTTP {e.code} — {body[:500]}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"请求异常: {e.reason}", file=sys.stderr)
        sys.exit(1)


def call_cat_meta_api(payload):
    url = f"{CAT_META_URL}?{urllib.parse.urlencode(payload)}"
    print(f"请求: GET {url}", file=sys.stderr)
    print(file=sys.stderr)

    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            if resp.status != 200:
                body = resp.read().decode("utf-8", errors="replace")
                print(f"错误: HTTP {resp.status} — {body[:500]}", file=sys.stderr)
                sys.exit(1)
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"错误: HTTP {e.code} — {body[:500]}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"请求异常: {e.reason}", file=sys.stderr)
        sys.exit(1)


def build_system_payload(args):
    if not args.metric_names:
        print("错误: system 模式必须提供 --metric-names", file=sys.stderr)
        sys.exit(1)
    if not args.app:
        print("错误: system 模式必须提供 --app", file=sys.stderr)
        sys.exit(1)

    payload = {
        "app": args.app,
        "start": args.start,
        "end": args.end,
        "metricNames": [m.strip() for m in args.metric_names.split(",")],
    }
    if args.view:
        payload["view"] = args.view
    if args.group_bys:
        payload["groupBys"] = [g.strip() for g in args.group_bys.split(",")]
    return payload


def build_pql_payload(args):
    if not args.pql:
        print("错误: pql 模式必须提供 --pql", file=sys.stderr)
        sys.exit(1)

    payload = {
        "pql": args.pql,
        "start": args.start,
        "end": args.end,
    }
    if args.app:
        payload["app"] = args.app
    if args.datasource:
        payload["datasource"] = args.datasource
    return payload


def build_cat_payload(args):
    if not args.app:
        print("错误: cat 模式必须提供 --app", file=sys.stderr)
        sys.exit(1)

    payload = {
        "app": args.app,
        "start": args.start,
        "end": args.end,
    }
    if args.theme:
        payload["theme"] = args.theme
    if args.metrics:
        payload["metrics"] = [m.strip() for m in args.metrics.split(",") if m.strip()]
    if args.metric:
        payload["metric"] = args.metric
    if args.type:
        payload["type"] = args.type
    if args.types:
        payload["types"] = [t.strip() for t in args.types.split(",")]
    if args.names:
        payload["names"] = [n.strip() for n in args.names.split(",")]
    if args.zones:
        payload["zones"] = [z.strip() for z in args.zones.split(",")]
    if args.ips:
        payload["ips"] = [i.strip() for i in args.ips.split(",")]
    if args.step:
        payload["step"] = args.step
    if args.group_bys:
        payload["groupBys"] = [g.strip() for g in args.group_bys.split(",")]
    return payload


def build_cat_meta_payload(args):
    if not args.app:
        print("错误: cat-meta 模式必须提供 --app", file=sys.stderr)
        sys.exit(1)

    payload = {"app": args.app}
    if args.theme:
        payload["theme"] = args.theme
    if args.type:
        payload["type"] = args.type
    return payload


def build_samples_payload(args):
    if not args.app:
        print("错误: samples 模式必须提供 --app", file=sys.stderr)
        sys.exit(1)
    if not args.type:
        print("错误: samples 模式必须提供 --type", file=sys.stderr)
        sys.exit(1)

    payload = {
        "app": args.app,
        "start": args.start,
        "end": args.end,
        "type": args.type,
    }
    if args.theme:
        payload["theme"] = args.theme
    if args.names:
        payload["names"] = [n.strip() for n in args.names.split(",")]
    if args.ips:
        payload["ips"] = [i.strip() for i in args.ips.split(",")]
    if args.success is not None:
        if args.success.lower() not in ("true", "false"):
            print(f"错误: --success 只接受 true 或 false，收到: {args.success}", file=sys.stderr)
            sys.exit(1)
        payload["success"] = args.success.lower() == "true"
    if args.min_duration:
        payload["minDuration"] = args.min_duration
    if args.max_duration:
        payload["maxDuration"] = args.max_duration
    return payload


BUILDERS = {
    "system": build_system_payload,
    "pql": build_pql_payload,
    "cat": build_cat_payload,
    "cat-meta": build_cat_meta_payload,
    "samples": build_samples_payload,
}

ENDPOINTS = {
    "system": "system",
    "pql": "pql",
    "cat": "cat",
    "samples": "cat/samples",
}


def main():
    parser = argparse.ArgumentParser(description="统一指标查询")
    parser.add_argument("--mode", required=True, choices=["system", "pql", "cat", "cat-meta", "samples"], help="查询模式")

    # 公共参数
    parser.add_argument("--app", help="服务名称")
    parser.add_argument("--start", help="开始时间 yyyy-MM-dd HH:mm:ss")
    parser.add_argument("--end", help="结束时间 yyyy-MM-dd HH:mm:ss")

    # system 模式
    parser.add_argument("--metric-names", help="指标名称列表，逗号分隔 (system 模式)")
    parser.add_argument("--view", help="查询视角: cluster/zone/container (system 模式)")
    parser.add_argument("--group-bys", help="分组维度，逗号分隔 (system 模式)")

    # pql 模式
    parser.add_argument("--pql", help="PromQL 表达式 (pql 模式)")
    parser.add_argument("--datasource", help="VMS 数据源名称 (pql 模式)")

    # cat 模式
    parser.add_argument("--theme", help="Cat 主题: transaction/event/problem (cat 模式)")
    parser.add_argument("--metric", help="Cat 单个指标: qps/avg/tp99/count/... (cat 模式)")
    parser.add_argument("--metrics", help="Cat 多个指标，逗号分隔，优先级高于 --metric (cat 模式)")
    parser.add_argument("--type", help="Cat 类型，单选: Call/Service/Http/URL (cat 模式)")
    parser.add_argument("--types", help="Cat 类型，多选，逗号分隔，与 --type 互斥 (cat 模式)")
    parser.add_argument("--names", help="接口名称列表，逗号分隔 (cat 模式)")
    parser.add_argument("--zones", help="机房列表，逗号分隔 (cat 模式)")
    parser.add_argument("--ips", help="IP 列表，逗号分隔 (cat 模式)")
    parser.add_argument("--step", type=int, help="步长(秒) (cat 模式)")

    # samples 模式
    parser.add_argument("--success", help="过滤成功/失败: true=只查成功, false=只查失败 (samples 模式)")
    parser.add_argument("--min-duration", type=int, dest="min_duration", help="最小耗时过滤(ms) (samples 模式)")
    parser.add_argument("--max-duration", type=int, dest="max_duration", help="最大耗时过滤(ms) (samples 模式)")

    args = parser.parse_args()

    if args.mode != "cat-meta" and (not args.start or not args.end):
        print(f"错误: {args.mode} 模式必须提供 --start 和 --end", file=sys.stderr)
        sys.exit(1)

    builder = BUILDERS[args.mode]
    payload = builder(args)
    result = call_cat_meta_api(payload) if args.mode == "cat-meta" else call_api(args.mode, payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
