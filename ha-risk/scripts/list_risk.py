#!/usr/bin/env python3
"""调用 getAllEnableRule：GET /v2/risk/list，分页查询风险规则检查结果。"""

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

import requests

# 配置（可通过环境变量覆盖）
API_BASE = os.getenv("RISK_API_BASE_URL", "https://haplus.devops.xiaohongshu.com").rstrip("/")
API_PATH = os.getenv("RISK_API_PATH", "/v2/risk/list")
API_TOKEN = os.getenv("RISK_API_TOKEN", "")
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20


def _build_params(
    user_email=None,
    scene_id=None,
    rule_id=None,
    product_id=None,
    result=None,
    is_white=None,
    service_name=None,
    status=None,
    start_time=None,
    end_time=None,
    within_the_plan=None,
    page=None,
    page_size=None,
) -> dict:
    raw = {
        "userEmail": user_email,
        "sceneId": scene_id,
        "ruleId": rule_id,
        "productId": product_id,
        "result": result,
        "isWhite": is_white,
        "serviceName": service_name,
        "status": status,
        "startTime": start_time,
        "endTime": end_time,
        "withinThePlan": within_the_plan,
        "page": page,
        "pageSize": page_size,
    }
    out = {}
    for k, v in raw.items():
        if v is None:
            continue
        if isinstance(v, bool):
            out[k] = str(v).lower()
        else:
            out[k] = v
    return out


def get_risk_list(params: Optional[Dict[str, Any]] = None) -> dict:
    """GET /v2/risk/list，返回接口 JSON 对象。"""
    if not API_BASE:
        raise ValueError("请设置环境变量 RISK_API_BASE_URL（例如 https://host:port）")

    url = f"{API_BASE}{API_PATH}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"

    p = params or {}
    resp = requests.get(url, params=p, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="查询风险规则列表（getAllEnableRule /v2/risk/list）")
    parser.add_argument("--user-email", default=None, help="用户邮箱")
    parser.add_argument("--scene-id", type=int, default=None, help="场景ID")
    parser.add_argument("--rule-id", type=int, default=None, help="规则ID")
    parser.add_argument("--product-id", type=int, default=None, help="业务线ID")
    parser.add_argument("--result", default=None, help="巡检结果 pass 通过 或 fail 风险")
    parser.add_argument("--service-name", default=None, help="资源名称")
    parser.add_argument("--status", type=int, default=None, help="状态")
    parser.add_argument("--start-time", default=None, help="startTime")
    parser.add_argument("--end-time", default=None, help="endTime")
    parser.add_argument(
        "--within-the-plan",
        default="false",
        choices=("true", "false"),
        help="withinThePlan",
    )
    parser.add_argument("--page", type=int, default=None, help="page，默认见环境变量 PAGE 或 1")
    parser.add_argument("--page-size", type=int, default=None, help="pageSize，默认见环境变量 PAGE_SIZE 或 20")

    args = parser.parse_args()

    within = None
    if args.within_the_plan is not None:
        within = args.within_the_plan == "true"

    page = args.page if args.page is not None else int(os.getenv("PAGE", DEFAULT_PAGE))
    page_size = args.page_size if args.page_size is not None else int(os.getenv("PAGE_SIZE", DEFAULT_PAGE_SIZE))

    params = _build_params(
        user_email=args.user_email,
        scene_id=args.scene_id,
        rule_id=args.rule_id,
        product_id=args.product_id,
        result=args.result,
        service_name=args.service_name,
        status=args.status,
        start_time=args.start_time,
        end_time=args.end_time,
        within_the_plan=within,
        page=page,
        page_size=page_size,
    )
    print(f"📤 请求 params: {params}")
    try:
        data = get_risk_list(params)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
