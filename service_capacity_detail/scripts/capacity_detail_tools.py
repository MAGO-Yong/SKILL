"""
Capacity Detail Skill - 单服务容量详情查询工具

用法：
    # 查询实时容量水位
    python capacity_detail_tools.py water_level \
        --service omega-hf-merger-merger-default \
        --zones all

    # 查询容量明细报表（天粒度）
    python capacity_detail_tools.py stat \
        --service omega-hf-merger-merger-default \
        --date 2024-01-15

    # 查询容量趋势（默认14天）
    python capacity_detail_tools.py trend \
        --service omega-hf-merger-merger-default
"""

import argparse
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Optional

import httpx

# ------------------------------------------------------------------
# 配置
# ------------------------------------------------------------------
_BASE_URL = os.environ.get("CAPACITY_PLATFORM_URL", "https://honghu.devops.xiaohongshu.com/api/v1/platform/open_api/capacity/detail")
_TIMEOUT = 30.0
_DEFAULT_TREND_DAYS = 14


def _build_headers() -> dict:
    return {"Content-Type": "application/json"}


def _yesterday() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def _days_ago(n: int) -> str:
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


# ------------------------------------------------------------------
# CapacityDetailClient
# ------------------------------------------------------------------

class CapacityDetailClient:
    """
    容量详情查询客户端，封装 capacity-platform /detail/* 接口。
    """

    def __init__(self, base_url: str = _BASE_URL, timeout: float = _TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get_water_level(
        self,
        service: str,
        zones: str = "all",
        date: Optional[str] = None,
        redstorm: bool = False,
    ) -> dict:
        """
        查询服务实时容量水位。

        :param service: 服务名
        :param zones: 可用区，逗号分隔，全选填 all
        :param date: 查询日期，格式 yyyy-MM-dd，不填为当天
        :param redstorm: 是否包含 redstorm 压测数据
        :return: 各可用区水位信息
        """
        params = {"zones": zones, "redstorm": str(redstorm).lower()}
        if date:
            params["date"] = date

        url = f"{self.base_url}/water-level/{service}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params, headers=_build_headers())
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 200:
            return {"error": data.get("message", "请求失败"), "code": data.get("code")}

        raw_zones = data.get("data", []) or []
        zones_result = []
        for z in raw_zones:
            entry = {
                "zone": z.get("zone"),
                "real_time_qps": z.get("real_time_qps"),
                "week_max_qps": z.get("week_max_qps"),
                "threshold_warning": z.get("threshold_warning"),
                "threshold_fatal": z.get("threshold_fatal"),
                "display": z.get("display"),
                "is_invalid": z.get("is_invalid", False),
                "reason": z.get("reason"),
            }
            if z.get("algorithm"):
                entry["algorithm"] = z["algorithm"]
            if z.get("pressure"):
                entry["pressure"] = z["pressure"]
            zones_result.append(entry)

        return {
            "service": service,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "zones": zones_result,
        }

    async def get_stat(
        self,
        service: str,
        zones: str = "all",
        date: Optional[str] = None,
        pressure_eval: bool = False,
        redstorm: bool = False,
    ) -> dict:
        """
        查询服务容量明细报表（天粒度统计分析）。

        :param service: 服务名
        :param zones: 可用区，逗号分隔，全选填 all
        :param date: 查询日期，格式 yyyy-MM-dd
        :param pressure_eval: True=算法水位，False=压测水位
        :param redstorm: 是否包含 redstorm 压测数据
        :return: 容量分析表格（headers + rows）
        """
        params = {
            "service": service,
            "zones": zones,
            "pressure_eval": str(pressure_eval).lower(),
            "redstorm": str(redstorm).lower(),
        }
        if date:
            params["date"] = date

        url = f"{self.base_url}/stat"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params, headers=_build_headers())
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 200:
            return {"error": data.get("message", "请求失败"), "code": data.get("code")}

        raw = data.get("data", {}) or {}
        headers = raw.get("headers", [])

        def _cell(c: dict) -> object:
            if c.get("diff") is not None:
                return {"value": c.get("value"), "diff": c.get("diff")}
            return c.get("value")

        rows = [
            [_cell(row.get(h) or {}) for h in headers]
            for row in (raw.get("stat_data", []) or [])
        ]
        return {
            "service": service,
            "date": date or _yesterday(),
            "headers": headers,
            "rows": rows,
        }

    async def get_trend(
        self,
        service: str,
        zones: str = "all",
        start: Optional[str] = None,
        end: Optional[str] = None,
        pressure_eval: bool = False,
        redstorm: bool = False,
    ) -> dict:
        """
        查询服务容量趋势（默认最近14天）。

        :param service: 服务名
        :param zones: 可用区，逗号分隔，全选填 all
        :param start: 起始日期，格式 yyyy-MM-dd，默认14天前
        :param end: 结束日期，格式 yyyy-MM-dd，默认昨天
        :param pressure_eval: True=算法水位，False=压测水位
        :param redstorm: 是否包含 redstorm 压测数据
        :return: 分组趋势图数据
        """
        if not start:
            start = _days_ago(_DEFAULT_TREND_DAYS)
        if not end:
            end = _yesterday()

        params = {
            "service": service,
            "zones": zones,
            "start": start,
            "end": end,
            "pressure_eval": str(pressure_eval).lower(),
            "redstorm": str(redstorm).lower(),
        }

        url = f"{self.base_url}/trend"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params, headers=_build_headers())
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 200:
            return {"error": data.get("message", "请求失败"), "code": data.get("code")}

        raw_groups = data.get("data", []) or []
        groups = []
        for g in raw_groups:
            charts = []
            for fm in g.get("fullMatrices", []):
                series = []
                for md in fm.get("matrixData", []):
                    legend = md.get("metric", {}).get("legend", "")
                    values_raw = md.get("values", [])
                    dates = [v.get("date") for v in values_raw]
                    values = [v.get("value") for v in values_raw]
                    series.append({"zone": legend, "dates": dates, "values": values})
                charts.append({
                    "title": fm.get("title"),
                    "unit": fm.get("unit"),
                    "series": series,
                })
            groups.append({"title": g.get("title"), "charts": charts})

        return {
            "service": service,
            "start": start,
            "end": end,
            "groups": groups,
        }

    async def get_radar_chart(
        self,
        service: str,
        zones: str = "all",
        date: Optional[str] = None,
        aggregation: str = "P95",
    ) -> dict:
        """
        查询服务资源特征雷达图（各资源维度的数值/分值，分值越高表示该服务在该类资源上越密集）。

        :param service: 服务名
        :param zones: 可用区，逗号分隔，全选填 all
        :param date: 查询日期，格式 yyyy-MM-dd，默认昨天
        :param aggregation: 聚合方式，P95 或 AVG
        :return: 雷达图元数据（指标定义+分级规则）及各可用区的指标值
        """
        params = {"zones": zones, "aggregation": aggregation}
        if date:
            params["date"] = date

        url = f"{self.base_url}/radar-chart/{service}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params, headers=_build_headers())
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 200:
            return {"error": data.get("message", "请求失败"), "code": data.get("code")}

        raw = data.get("data", {}) or {}
        return {
            "service": service,
            "date": date or _yesterday(),
            "aggregation": aggregation,
            "metadata": raw.get("metadata", {}),
            "data": raw.get("data", {}),
        }

    async def get_service_config(self, service: str) -> dict:
        """
        查询服务容量配置（评估指标阈值、自定义指标、压测配置、告警配置、服务基本信息）。

        :param service: 服务名
        :return: 服务完整配置，包含指标配置、压测配置、告警配置、服务基本信息
        """
        url = f"{self.base_url}/service-config"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params={"service": service}, headers=_build_headers())
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 200:
            return {"error": data.get("message", "请求失败"), "code": data.get("code")}

        raw = data.get("data", {}) or {}
        info = raw.get("serviceInfo", {}) or {}
        cfg = raw.get("serviceConfig", {}) or {}

        # 指标配置：区分内置指标和自定义指标
        metric_configs = []
        for pql in cfg.get("promqlConfigs", []):
            name = pql.get("name")
            threshold = pql.get("threshold")
            zone_thresholds = pql.get("zoneThresholds") or []
            entry = {
                "name": name,
                "type": pql.get("type"),          # default=内置指标, custom=自定义指标
                "source": pql.get("source"),       # vms=prometheus, cat=CAT
                "condition": pql.get("condition"), # gt=大于阈值触发, lt=小于阈值触发
                "threshold": threshold if threshold != -1.0 else None,
                "zone_thresholds": {zt["zone"]: zt["value"] for zt in zone_thresholds} if zone_thresholds else None,
            }
            # 自定义指标额外保留 pql 语句
            if pql.get("type") == "custom":
                entry["pql"] = pql.get("pql")
                entry["datasource"] = pql.get("datasource")
            metric_configs.append(entry)

        # 压测配置
        pressure_cfg = cfg.get("pressureConfig") or {}
        pressure = None
        if pressure_cfg:
            traffic = pressure_cfg.get("trafficStrategy") or {}
            pressure = {
                "zones": pressure_cfg.get("xhsZone", []),
                "enable_schedule": pressure_cfg.get("enableSchedule"),
                "crontab": pressure_cfg.get("crontab"),
                "crontab_desc": pressure_cfg.get("crontabDescription"),
                "next_execute_time": pressure_cfg.get("nextExecuteTime"),
                "adjust_wait_time": pressure_cfg.get("adjustWaitTime"),
                "pod_strategy": pressure_cfg.get("podStrategy"),
                "traffic_strategy": {
                    "name": traffic.get("name"),
                    "value": traffic.get("value"),
                    "zone_values": {zv["zone"]: zv["value"] for zv in (traffic.get("zoneValues") or [])},
                } if traffic else None,
            }

        # 告警配置
        alarm_cfg = cfg.get("alarmThreshold") or {}
        zone_alarm = {zt["zone"]: zt["value"] for zt in (alarm_cfg.get("zoneThresholds") or [])}

        # 目标水位配置
        wl_cfg = cfg.get("waterLevelConfig") or {}

        return {
            "service": service,
            "service_info": {
                "app": info.get("app"),
                "biz_line": info.get("bizLine"),
                "level": info.get("level"),
                "service_type": info.get("serviceTypeEnum"),
                "platform": info.get("platform"),
                "language": info.get("language"),
                "zones": info.get("zones", []),
                "cpu_num": info.get("cpuNum"),
                "gpu_card_num": info.get("gpuCardNum"),
                "owners": info.get("owners"),
            },
            "metric_configs": metric_configs,
            "buffer": cfg.get("buffer"),
            "alarm_enable": cfg.get("alarmEnable"),
            "alarm_threshold": alarm_cfg.get("threshold"),
            "alarm_zone_thresholds": zone_alarm if zone_alarm else None,
            "pressure_config": pressure,
            "water_level_config": wl_cfg if wl_cfg else None,
        }


# ------------------------------------------------------------------
# CLI 入口
# ------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="单服务容量详情查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--base-url", default=_BASE_URL, help="capacity-platform 服务地址")

    sub = parser.add_subparsers(dest="cmd", required=True)

    # --- water_level ---
    p1 = sub.add_parser("water_level", help="查询实时容量水位")
    p1.add_argument("--service", required=True, help="服务名")
    p1.add_argument("--zones", default="all", help="可用区，逗号分隔，默认 all")
    p1.add_argument("--date", default=None, help="查询日期，格式 yyyy-MM-dd")
    p1.add_argument("--redstorm", action="store_true", help="是否包含 redstorm 压测数据")

    # --- stat ---
    p2 = sub.add_parser("stat", help="查询容量明细报表（天粒度统计分析）")
    p2.add_argument("--service", required=True, help="服务名")
    p2.add_argument("--zones", default="all", help="可用区，逗号分隔，默认 all")
    p2.add_argument("--date", default=None, help="查询日期，格式 yyyy-MM-dd")
    p2.add_argument("--pressure-eval", action="store_true", help="使用算法水位（默认压测水位）")
    p2.add_argument("--redstorm", action="store_true", help="是否包含 redstorm 压测数据")

    # --- trend ---
    p3 = sub.add_parser("trend", help="查询容量趋势（默认最近14天）")
    p3.add_argument("--service", required=True, help="服务名")
    p3.add_argument("--zones", default="all", help="可用区，逗号分隔，默认 all")
    p3.add_argument("--start", default=None, help="起始日期，格式 yyyy-MM-dd，默认14天前")
    p3.add_argument("--end", default=None, help="结束日期，格式 yyyy-MM-dd，默认昨天")
    p3.add_argument("--pressure-eval", action="store_true", help="使用算法水位（默认压测水位）")
    p3.add_argument("--redstorm", action="store_true", help="是否包含 redstorm 压测数据")

    # --- radar_chart ---
    p4 = sub.add_parser("radar_chart", help="查询服务资源特征雷达图")
    p4.add_argument("--service", required=True, help="服务名")
    p4.add_argument("--zones", default="all", help="可用区，逗号分隔，默认 all")
    p4.add_argument("--date", default=None, help="查询日期，格式 yyyy-MM-dd，默认昨天")
    p4.add_argument("--aggregation", default="P95", choices=["P95", "AVG"], help="聚合方式，默认 P95")

    # --- service_config ---
    p5 = sub.add_parser("service_config", help="查询服务容量配置（评估指标、阈值、告警配置、服务基本信息）")
    p5.add_argument("--service", required=True, help="服务名")

    return parser


async def _run(args: argparse.Namespace) -> dict:
    client = CapacityDetailClient(base_url=args.base_url)
    if args.cmd == "water_level":
        return await client.get_water_level(
            service=args.service,
            zones=args.zones,
            date=args.date,
            redstorm=args.redstorm,
        )
    elif args.cmd == "stat":
        return await client.get_stat(
            service=args.service,
            zones=args.zones,
            date=args.date,
            pressure_eval=args.pressure_eval,
            redstorm=args.redstorm,
        )
    elif args.cmd == "trend":
        return await client.get_trend(
            service=args.service,
            zones=args.zones,
            start=args.start,
            end=args.end,
            pressure_eval=args.pressure_eval,
            redstorm=args.redstorm,
        )
    elif args.cmd == "radar_chart":
        return await client.get_radar_chart(
            service=args.service,
            zones=args.zones,
            date=args.date,
            aggregation=args.aggregation,
        )
    elif args.cmd == "service_config":
        return await client.get_service_config(service=args.service)


if __name__ == "__main__":
    args = _build_parser().parse_args()
    result = asyncio.run(_run(args))
    print(json.dumps(result, ensure_ascii=False, indent=2))
