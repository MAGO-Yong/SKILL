"""
Capacity Evaluate Skill - 容量评估结果查询工具

用法：
    # 查询算法评估结果（需先通过 service_config 获取区列表）
    python capacity_evaluate_tools.py algorithm \
        --name reclambdaservice-service-homefeed-recall \
        --zones alhz1,alsh1,qcsh4

    # 查询压测评估结果
    python capacity_evaluate_tools.py pressure \
        --name reclambdaservice-service-homefeed-recall \
        --zones alhz1,alsh1 \
        --date 2026-03-23
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import httpx

# ------------------------------------------------------------------
# 配置
# ------------------------------------------------------------------
_BASE_URL = os.environ.get("CAPACITY_PLATFORM_URL", "https://honghu.devops.xiaohongshu.com/api/v1/platform/open_api/capacity/detail")
_TIMEOUT = 30.0


def _build_headers() -> dict:
    return {"Content-Type": "application/json"}


def _yesterday() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def _parse_cells(raw_cells: list) -> list:
    return [
        {
            "key": cell.get("key"),
            "label": cell.get("label"),
            "value": cell.get("value"),
            "status": cell.get("status", "normal"),
        }
        for cell in raw_cells
    ]


def _parse_figures(raw_figures: list) -> list:
    """
    提取 figures 中的关键信息。
    - encode_figure 是 Bokeh HTML 交互图，去掉不返回
    - metrics 是 Map<String, String>，人类可读的文本描述
    - metric_detail 是结构化的 MetricEstimateResult，含拟合质量指标
    """
    result = []
    for fig in raw_figures:
        entry = {
            "header": fig.get("header"),
            "metrics": fig.get("metrics") or {},
        }
        detail = fig.get("metric_detail")
        if detail:
            eval_data = detail.get("eval") or {}
            entry["metric_detail"] = {
                "metric_name": detail.get("metric_name"),
                "qps_limit": detail.get("qps_limit"),
                "metric_limit": detail.get("metric_limit"),
                "model": detail.get("model"),
                "fitting_status": detail.get("fitting_status"),
                "effective": detail.get("effective"),
                "valid_mape": eval_data.get("test_mape"),       # 验证集误差，< 0.05 为准确
                "bias_perc": eval_data.get("limit_bias_perc"),  # 外推偏差，< 0.05 为准确
                "train_r2": eval_data.get("train_r2_score"),
            }
        result.append(entry)
    return result


# ------------------------------------------------------------------
# CapacityEvaluateClient
# ------------------------------------------------------------------

class CapacityEvaluateClient:

    def __init__(self, base_url: str = _BASE_URL, timeout: float = _TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def _fetch_algorithm(self, client: httpx.AsyncClient, name: str, zone: str, date: Optional[str]) -> dict:
        params = {"name": name, "zone": zone}
        if date:
            params["date"] = date
        resp = await client.get(
            f"{self.base_url}/evaluate/algorithm",
            params=params,
            headers=_build_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 200:
            return {"zone": zone, "error": data.get("message", "请求失败")}

        raw = data.get("data", {}) or {}
        entry = {
            "zone": zone,
            "result": _parse_cells(raw.get("result") or []),
        }
        if raw.get("figures"):
            entry["figures"] = _parse_figures(raw["figures"])
        if raw.get("figuresMap"):
            entry["figures_map"] = {
                gpu_type: _parse_figures(figs)
                for gpu_type, figs in raw["figuresMap"].items()
            }
        return entry

    async def _fetch_pressure(self, client: httpx.AsyncClient, name: str, zone: str, date: Optional[str]) -> dict:
        params = {"name": name, "zone": zone}
        if date:
            params["date"] = date
        resp = await client.get(
            f"{self.base_url}/evaluate/pressure",
            params=params,
            headers=_build_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 200:
            return {"zone": zone, "error": data.get("message", "请求失败")}

        raw = data.get("data", {}) or {}
        records_raw = raw.get("records", {}) or {}
        return {
            "zone": zone,
            "result": _parse_cells(raw.get("result") or []),
            "records": {
                "headers": records_raw.get("headers", []),
                "rows": records_raw.get("stat_data", []),
            },
        }

    async def _fetch_all(self, fetch_fn, name: str, zones: List[str], date: Optional[str]) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            results = await asyncio.gather(*[fetch_fn(client, name, zone, date) for zone in zones])
        return {
            "service": name,
            "date": date or _yesterday(),
            "zones": list(results),
        }

    async def get_algorithm(self, name: str, zones: List[str], date: Optional[str] = None) -> dict:
        """
        查询算法评估结果（多区并发）。
        服务的可用区列表请先通过 service_capacity_detail 的 service_config 获取。
        """
        return await self._fetch_all(self._fetch_algorithm, name, zones, date)

    async def get_pressure(self, name: str, zones: List[str], date: Optional[str] = None) -> dict:
        """查询压测评估结果（多区并发）。"""
        return await self._fetch_all(self._fetch_pressure, name, zones, date)


# ------------------------------------------------------------------
# CLI 入口
# ------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="容量评估结果查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--base-url", default=_BASE_URL, help="capacity-platform 服务地址")
    sub = parser.add_subparsers(dest="cmd", required=True)

    for cmd, help_text in [("algorithm", "查询算法评估结果"), ("pressure", "查询压测评估结果")]:
        p = sub.add_parser(cmd, help=help_text)
        p.add_argument("--name", required=True, help="服务名")
        p.add_argument("--zones", required=True, help="可用区，逗号分隔，如 alhz1,alsh1")
        p.add_argument("--date", default=None, help="查询日期，格式 yyyy-MM-dd，默认昨天")

    return parser


async def _run(args: argparse.Namespace) -> dict:
    zones = [z.strip() for z in args.zones.split(",") if z.strip()]
    client = CapacityEvaluateClient(base_url=args.base_url)
    if args.cmd == "algorithm":
        return await client.get_algorithm(name=args.name, zones=zones, date=args.date)
    elif args.cmd == "pressure":
        return await client.get_pressure(name=args.name, zones=zones, date=args.date)


if __name__ == "__main__":
    args = _build_parser().parse_args()
    result = asyncio.run(_run(args))
    print(json.dumps(result, ensure_ascii=False, indent=2))
