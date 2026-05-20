#!/usr/bin/env python3
"""调用 getAllEnableRule：GET /api/risk/rule/list，分页查询巡检项列表。"""

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

import requests

# 配置（可通过环境变量覆盖）
API_BASE = os.getenv("RISK_API_BASE_URL", "https://harisk.devops.xiaohongshu.com").rstrip("/")
API_PATH = os.getenv("RULE_API_PATH", "/api/risk/rule/list")
API_TOKEN = os.getenv("RISK_API_TOKEN", "")
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20


def _build_params(
    level=None,
    status=None,
    name=None,
    type=None,
    target_type=None,
    is_ha_specification=None,
    source=None,
    owner=None,
    page=None,
    page_size=None,
) -> dict:
    raw = {
        "level": level,
        "status": status,
        "name": name,
        "type": type,
        "targetType": target_type,
        "isHaSpecification": is_ha_specification,
        "source": source,
        "owner": owner,
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


def get_rules_list(params: Optional[Dict[str, Any]] = None) -> dict:
    """GET /rule/list，返回接口 JSON 对象。"""
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
    parser = argparse.ArgumentParser(description="查询巡检项列表（getAllEnableRule /rule/list）")
    parser.add_argument("--level", default=None, help="风险等级")
    parser.add_argument("--status", type=int, default=None, help="状态")
    parser.add_argument("--name", default=None, help="规则名称")
    parser.add_argument("--type", default=None, help="类型")
    parser.add_argument("--target-type", default=None, help="目标类型")
    parser.add_argument("--is-ha-specification", type=int, default=None, help="是否为HA规范")
    parser.add_argument("--source", default=None, help="来源")
    parser.add_argument("--owner", default=None, help="负责人")
    parser.add_argument("--page", type=int, default=None, help="page，默认见环境变量 PAGE 或 1")
    parser.add_argument("--page-size", type=int, default=None, help="pageSize，默认见环境变量 PAGE_SIZE 或 20")

    args = parser.parse_args()

    page = args.page if args.page is not None else int(os.getenv("PAGE", DEFAULT_PAGE))
    page_size = args.page_size if args.page_size is not None else int(os.getenv("PAGE_SIZE", DEFAULT_PAGE_SIZE))

    params = _build_params(
        level=args.level,
        status=args.status,
        name=args.name,
        type=args.type,
        target_type=args.target_type,
        is_ha_specification=args.is_ha_specification,
        source=args.source,
        owner=args.owner,
        page=page,
        page_size=page_size,
    )
    print(f"📤 请求 params: {params}")
    try:
        data = get_rules_list(params)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()