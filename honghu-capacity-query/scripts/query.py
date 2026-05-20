#!/usr/bin/env python3
"""
鸿鹄平台服务容量查询脚本

用法:
    python3 query.py '<JSON参数>'

参数说明（JSON格式）:
    serviceName   string   服务名称（必填）

示例:
    python3 query.py '{"serviceName":"arkfeedx-1-default"}'

输出: JSON 到 stdout
    成功: {"success": true, "data": {...}}
    失败: {"success": false, "error": "错误信息"}
"""

import json
import os
import sys
from typing import Any, Optional

try:
    import httpx
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "缺少依赖",
        "detail": "请安装 httpx: pip3 install httpx"
    }, ensure_ascii=False))
    sys.exit(1)


# 鸿鹄 API 配置
CAPACITY_API_URL = "http://honghu.devops.xiaohongshu.com/api/v1/platform/open_api/capacity/service_capacity"


def get_auth_token() -> str:
    """从环境变量获取鸿鹄 API Token"""
    token = os.environ.get("HONGHU_AUTH_TOKEN")
    if not token:
        raise RuntimeError(
            "未找到 HONGHU_AUTH_TOKEN 环境变量。\n"
            "请设置: export HONGHU_AUTH_TOKEN='your_token'\n"
            "Token 获取方式: 联系鸿鹄平台管理员"
        )
    return token


def format_capacity_data(data: dict) -> str:
    """格式化容量数据为可读文本"""
    lines = []

    # 检查返回结构
    if "code" in data and data["code"] == 200:
        water_level_list = data.get("data", [])

        if not water_level_list:
            return "无容量数据"

        if isinstance(water_level_list, list):
            # 添加总览
            lines.append("=" * 60)
            lines.append("📊 容量水位总览")
            lines.append("=" * 60)
            lines.append("")

            # 统计所有可用区
            total_zones = len(water_level_list)
            warning_zones = sum(1 for zone in water_level_list
                               if zone.get("realTimeWaterLevel", 0) >= zone.get("threshold_warning", 0.85))
            fatal_zones = sum(1 for zone in water_level_list
                             if zone.get("realTimeWaterLevel", 0) >= zone.get("threshold_fatal", 0.95))

            lines.append(f"可用区总数: {total_zones}")
            lines.append(f"告警区域数: {warning_zones} (水位 ≥ 85%)")
            lines.append(f"严重区域数: {fatal_zones} (水位 ≥ 95%)")
            lines.append("")

            # 遍历每个可用区
            for idx, zone_info in enumerate(water_level_list, 1):
                zone_name = zone_info.get("zone") or "未知"
                real_time_qps = zone_info.get("real_time_qps") or 0
                week_max_qps = zone_info.get("week_max_qps") or 0
                limit_qps = zone_info.get("limitQps") or 0
                real_time_water = zone_info.get("realTimeWaterLevel") or 0
                threshold_warning = zone_info.get("threshold_warning", 0.85)
                threshold_fatal = zone_info.get("threshold_fatal", 0.95)
                is_invalid = zone_info.get("is_invalid", False)
                display = zone_info.get("display") or "unknown"

                # 判断水位状态
                if is_invalid:
                    status = "❌ 数据异常"
                    status_emoji = "❌"
                elif real_time_water >= threshold_fatal:
                    status = "🔴 严重告警"
                    status_emoji = "🔴"
                elif real_time_water >= threshold_warning:
                    status = "⚠️  告警"
                    status_emoji = "⚠️"
                else:
                    status = "✅ 正常"
                    status_emoji = "✅"

                lines.append("-" * 60)
                lines.append(f"{status_emoji} 可用区 {idx}: {zone_name} ({status})")
                lines.append("-" * 60)
                lines.append("")

                # 实时指标
                lines.append("【实时指标】")
                lines.append(f"  实时 QPS:    {real_time_qps:>10,.0f}")
                lines.append(f"  最大 QPS:    {limit_qps:>10,.0f}")
                water_emoji = '🔴' if real_time_water >= threshold_fatal else '⚠️' if real_time_water >= threshold_warning else '✅'
                lines.append(f"  实时水位:    {real_time_water:>10.1%}  {water_emoji}")
                lines.append("")

                # 周峰值指标
                lines.append("【周峰值指标】")
                lines.append(f"  周峰值 QPS:  {week_max_qps:>10,.0f}")
                week_max_water = week_max_qps / limit_qps if limit_qps > 0 else 0
                lines.append(f"  周峰值水位:  {week_max_water:>10.1%}")
                lines.append("")

                # 阈值设置
                lines.append("【阈值设置】")
                lines.append(f"  告警阈值:    {threshold_warning:>10.1%}")
                lines.append(f"  严重阈值:    {threshold_fatal:>10.1%}")
                lines.append("")

                # 评估模型
                algorithm = zone_info.get("algorithm", {})
                pressure = zone_info.get("pressure", {})

                if algorithm or pressure:
                    lines.append("【评估模型】")
                    display_name = get_display_name(display)
                    lines.append(f"  当前采用:    {display_name}")

                    if algorithm:
                        lines.append(f"  算法评估:")
                        alg_limit = algorithm.get('limit') or 0
                        alg_rt = algorithm.get('realtime_water_level') or 0
                        alg_week = algorithm.get('week_max_water_level') or 0
                        lines.append(f"    - 限额:    {alg_limit:>10,.0f} QPS")
                        lines.append(f"    - 实时水位: {alg_rt:>9.1%}")
                        lines.append(f"    - 周峰水位: {alg_week:>9.1%}")

                    if pressure:
                        lines.append(f"  压测评估:")
                        prs_limit = pressure.get('limit') or 0
                        prs_rt = pressure.get('realtime_water_level') or 0
                        prs_week = pressure.get('week_max_water_level') or 0
                        lines.append(f"    - 限额:    {prs_limit:>10,.0f} QPS")
                        lines.append(f"    - 实时水位: {prs_rt:>9.1%}")
                        lines.append(f"    - 周峰水位: {prs_week:>9.1%}")
                    lines.append("")

                # 异常原因
                reason = zone_info.get("reason")
                if reason:
                    lines.append(f"【异常原因】")
                    lines.append(f"  {reason}")
                    lines.append("")

            # 添加总结建议
            lines.append("=" * 60)
            lines.append("💡 建议")
            lines.append("=" * 60)

            if fatal_zones > 0:
                lines.append("🔴 严重: 有可用区水位超过 95%，建议立即扩容！")
            elif warning_zones > 0:
                lines.append("⚠️  警告: 有可用区水位超过 85%，建议关注容量情况。")
            else:
                lines.append("✅ 所有可用区容量水位正常。")

        else:
            # 单个结果（非列表）
            lines.append(json.dumps(water_level_list, indent=2, ensure_ascii=False))
    else:
        # 如果返回结构不是预期的，显示原始数据
        lines.append(json.dumps(data, indent=2, ensure_ascii=False))

    return "\n".join(lines) if lines else "无数据"


def get_display_name(display: str) -> str:
    """获取评估模型的中文名称"""
    display_map = {
        "algorithm": "算法评估",
        "pressure": "压测评估",
        "unknown": "未知"
    }
    return display_map.get(display, display)


def query_service_capacity(service_name: str) -> dict:
    """查询服务容量水位"""

    # 获取认证信息
    try:
        auth_token = get_auth_token()
    except RuntimeError as e:
        return {
            "success": False,
            "error": "认证配置错误",
            "detail": str(e)
        }

    # 构建请求头
    headers = {
        "Authorization": auth_token,
        "accept": "application/json"
    }

    # 构建查询参数
    params = {
        "serviceName": service_name
    }

    # 发送请求
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                CAPACITY_API_URL,
                headers=headers,
                params=params
            )
            response.raise_for_status()
            result = response.json()

            # 格式化输出
            formatted_text = format_capacity_data(result)

            return {
                "success": True,
                "serviceName": service_name,
                "data": result,
                "formatted": formatted_text
            }

    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP错误: {e.response.status_code}",
            "detail": e.response.text if hasattr(e.response, 'text') else str(e)
        }
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "请求超时",
            "detail": "鸿鹄 API 响应超时，请稍后重试"
        }
    except Exception as e:
        return {
            "success": False,
            "error": "查询失败",
            "detail": str(e)
        }


def main():
    # 解析命令行参数
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "缺少参数",
            "detail": "用法: python3 query.py '<JSON参数>'"
        }, ensure_ascii=False))
        sys.exit(1)

    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({
            "success": False,
            "error": "参数解析失败",
            "detail": str(e)
        }, ensure_ascii=False))
        sys.exit(1)

    # 验证必填参数
    if "serviceName" not in params:
        print(json.dumps({
            "success": False,
            "error": "缺少必填参数",
            "detail": "缺少: serviceName"
        }, ensure_ascii=False))
        sys.exit(1)

    # 执行查询
    result = query_service_capacity(params["serviceName"])

    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()