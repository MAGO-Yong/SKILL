---
name: honghu-capacity-query
description: 查询鸿鹄平台服务容量水位信息。支持查询指定服务的资源使用情况、容量阈值等。当用户询问"查询容量"、"服务容量"、"容量水位"、"鸿鹄容量"、"查容量"、"容量查询"时触发。
---

# 鸿鹄容量查询 Skill

通过鸿鹄平台 API 查询服务的容量水位情况，包括实时 QPS、容量限额、水位百分比等信息。

## 快速使用

```bash
HONGHU_AUTH_TOKEN=<token> python3 scripts/query.py '{
  "serviceName": "arkfeedx-1-default"
}'
```

## 参数说明

| 参数 | 说明 | 示例值 | 必填 |
|------|------|--------|------|
| `serviceName` | 服务名称 | `"arkfeedx-1-default"`, `"arkproxy-service-share"` | 是 |

## 认证配置

从环境变量读取，**不支持硬编码**：

```bash
export HONGHU_AUTH_TOKEN="your_auth_token"
```

Token 获取方式：联系鸿鹄平台管理员获取 API Token

## 常用场景

**查询服务容量水位**
```bash
python3 scripts/query.py '{
  "serviceName": "arkfeedx-1-default"
}'
```

**查询共享服务容量**
```bash
python3 scripts/query.py '{
  "serviceName": "arkproxy-service-share"
}'
```

## 输出格式

脚本输出 JSON 到 stdout：

**成功响应：**
```json
{
  "success": true,
  "serviceName": "arkfeedx-1-default",
  "data": {
    "code": 200,
    "data": [
      {
        "zone": "zone1",
        "real_time_qps": 50000,
        "week_max_qps": 80000,
        "limitQps": 100000,
        "realTimeWaterLevel": 0.5,
        "threshold_warning": 0.85,
        "threshold_fatal": 0.95
      }
    ]
  },
  "formatted": "格式化的可读文本"
}
```

**失败响应：**
```json
{
  "success": false,
  "error": "HTTP错误: 401",
  "detail": "认证失败"
}
```

## 返回字段说明

### 容量指标

| 字段 | 说明 |
|------|------|
| `zone` | 可用区名称 |
| `real_time_qps` | 实时 QPS |
| `week_max_qps` | 周峰值 QPS |
| `limitQps` | 容量限额（QPS） |
| `realTimeWaterLevel` | 实时水位百分比 |
| `threshold_warning` | 告警阈值（默认 0.85） |
| `threshold_fatal` | 严重告警阈值（默认 0.95） |

### 水位状态判断

- **正常** ✅: 水位 < 85%
- **告警** ⚠️: 85% ≤ 水位 < 95%
- **严重告警** 🔴: 水位 ≥ 95%

## 使用场景

1. **容量规划**: 评估当前容量使用情况，制定扩容计划
2. **资源监控**: 实时监控服务容量水位，及时发现容量瓶颈
3. **扩缩容决策**: 基于容量数据做出扩缩容决策
4. **故障预防**: 提前发现容量告警，避免容量不足导致的故障

