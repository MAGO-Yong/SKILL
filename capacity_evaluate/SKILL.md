---
name: capacity_evaluate
description: "查询单服务各可用区的容量评估详情，包括：(1) 算法评估结果（基于历史监控数据拟合QPS与CPU/RT等指标的数学关系，推算极限QPS）；(2) 压测评估结果（基于pod调权压测得出的实测极限QPS及历史压测记录）。核心用途：解释容量水位是怎么来的、极限QPS是如何计算的、当前buffer是多少、哪个指标是短板。触发词：容量怎么评估的、极限QPS怎么算的、水位怎么来的、算法评估、压测评估、容量buffer、单机极限QPS、容量评估结果、评估状态、压测结果、压测历史、短板指标。"
---

# Capacity Evaluate Skill

通过 `scripts/capacity_evaluate_tools.py` 查询单服务各可用区的容量评估详情，支持多区并发查询。

## 背景：容量水位是怎么计算的？

容量平台通过两种方式评估服务的极限 QPS，再结合当前流量计算水位：

**方式一：智能评估（算法）**
采集最近一周的监控数据（QPS、CPU、RT P99、GPU 等），建立性能指标与 QPS 的数学关系模型，根据配置的指标阈值推算服务的极限 QPS。多个指标取**短板**（最小值）作为最终极限 QPS。

**方式二：容量压测**
通过自动化逐步增加单 pod 权重，增加线上真实流量进行压测，直到触达配置的容量指标阈值，得到单 pod 的极限 QPS，乘以可用区实例数得到可用区极限 QPS。

**水位和 buffer 计算：**
```
极限 QPS  = 单 pod 极限 QPS × 实例数
水位      = 周峰值 QPS / 极限 QPS
buffer    = 极限 QPS / 周峰值 QPS - 1
```

## 重要：如何获取服务的可用区列表

接口是单区维度的，需先通过 `service_capacity_detail` skill 的 `service_config` 获取可用区列表：
```bash
python ../service_capacity_detail/scripts/capacity_detail_tools.py service_config \
    --service reclambdaservice-service-homefeed-recall
# 返回中的 service_info.zones 字段即为可用区列表
```

## 用法

```bash
# 算法评估（多区）
python scripts/capacity_evaluate_tools.py algorithm \
    --name reclambdaservice-service-homefeed-recall \
    --zones alhz1,alsh1,qcsh4

# 压测评估（多区）
python scripts/capacity_evaluate_tools.py pressure \
    --name reclambdaservice-service-homefeed-recall \
    --zones alhz1,alsh1,qcsh4 \
    --date 2026-03-23
```

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--name` | 是 | - | 服务名 |
| `--zones` | 是 | - | 可用区，逗号分隔，如 alhz1,alsh1 |
| `--date` | 否 | 昨天 | 查询日期，格式 yyyy-MM-dd |

## 输出结构

### algorithm 输出

```json
{
  "service": "reclambdaservice-service-homefeed-recall",
  "date": "2026-03-23",
  "zones": [
    {
      "zone": "alhz1",
      "result": [
        {"key": "POD_LIMIT_QPS", "label": "单机极限QPS", "value": "1234.5", "status": "normal"},
        {"key": "ZONE_LIMIT_QPS", "label": "可用区极限QPS", "value": "98760", "status": "normal"},
        {"key": "WATER_LEVEL", "label": "水位", "value": "72.3%", "status": "normal"},
        {"key": "BUFFER", "label": "buffer", "value": "38.3%", "status": "normal"},
        {"key": "REPLICAS", "label": "实例数", "value": "80", "status": "normal"},
        {"key": "DATE", "label": "评估日期", "value": "2026-03-23", "status": "normal"}
      ],
      "figures": [
        {
          "header": "QPS vs CPU利用率",
          "metrics": {
            "CPU阈值": "70% （系统推荐）",
            "极限QPS估计值（单机）": "1234.5",
            "拟合模型": "LINEAR",
            "拟合状态": "NORMAL",
            "评估有效": "true",
            "验证集误差(valid_mape)": "0.0312",
            "外推偏差(bias_perc)": "0.0218",
            "训练集R²": "0.9541"
          }
        },
        {
          "header": "QPS vs 耗时 P99",
          "metrics": {
            "耗时阈值": "200ms",
            "极限QPS估计值（单机）": "1050.0",
            "拟合模型": "APPROX_MMC_QUEUE",
            "拟合状态": "NORMAL",
            "评估有效": "true",
            "验证集误差(valid_mape)": "0.0480",
            "外推偏差(bias_perc)": "0.0310",
            "训练集R²": "0.8823"
          }
        }
      ]
    }
  ]
}
```

### pressure 输出

```json
{
  "service": "reclambdaservice-service-homefeed-recall",
  "date": "2026-03-23",
  "zones": [
    {
      "zone": "alhz1",
      "result": [
        {"key": "POD_LIMIT_QPS", "label": "单机极限QPS", "value": "1200.0", "status": "normal"},
        {"key": "ZONE_LIMIT_QPS", "label": "可用区极限QPS", "value": "96000", "status": "normal"},
        {"key": "WATER_LEVEL", "label": "水位", "value": "74.1%", "status": "normal"},
        {"key": "BUFFER", "label": "buffer", "value": "34.9%", "status": "normal"},
        {"key": "REPLICAS", "label": "实例数", "value": "80", "status": "normal"},
        {"key": "DATE", "label": "最近压测日期", "value": "2026-03-20", "status": "normal"}
      ],
      "records": {
        "headers": ["压测日期", "单机极限QPS", "可用区极限QPS", "buffer", "建议实例数"],
        "rows": []
      }
    }
  ]
}
```

## 字段含义说明

### result cells

| key | 含义 |
|-----|------|
| `POD_LIMIT_QPS` | 单 pod 极限 QPS，算法评估为模型推算值，压测评估为实测值 |
| `ZONE_LIMIT_QPS` | 可用区极限 QPS = 单机极限 QPS × 实例数 |
| `WATER_LEVEL` | 水位 = 周峰值 QPS / 可用区极限 QPS |
| `BUFFER` | buffer = 可用区极限 QPS / 周峰值 QPS - 1 |
| `REPLICAS` | 当前可用区实例数 |
| `DATE` | 算法评估日期 / 最近一次压测日期 |
| `STATUS` | 评估状态（仅在极限 QPS 无效时出现，说明评估失败原因） |

### figures（仅 algorithm）

每个 figure 对应一个性能指标（CPU/RT/GPU 等）与 QPS 的拟合关系图（Bokeh HTML，无法直接渲染）。包含两个字段：

- `metrics`：人类可读的文本描述（阈值、极限QPS、拟合模型、拟合质量指标等）
- `metric_detail`：结构化的原始数据（`qps_limit`、`metric_limit`、`model`、`fitting_status`、`effective`、`valid_mape`、`bias_perc`、`train_r2`）

**评估准确性判断**（满足任一即为准确）：
- `valid_mape < 0.05`（验证集平均拟合误差 < 5%）
- `bias_perc < 0.05`（外推偏差 < 5%）

两者均不满足时，该指标极限 QPS 可信度低，建议以压测数据为准。

### records（仅 pressure）

历史压测记录表，按时间倒序，包含每次压测的单机极限 QPS、可用区极限 QPS、buffer、建议实例数等。

## AI 分析指引

**调用前置步骤**：先调用 `service_config` 获取 `service_info.zones`，再传入 `--zones` 并发查询所有区。

### 算法评估分析

- `figures` 中各指标的 `metric_detail.qps_limit` 取最小值即为短板指标，这是当前容量瓶颈所在；`metric_detail.effective = true` 的指标即为最终生效的短板指标
- `fitting_status` 不为 `NORMAL`，说明该指标拟合失败，不参与极限 QPS 计算
- **准确性判断**：`valid_mape < 0.05` 或 `bias_perc < 0.05` 满足任一即为准确；两者均不满足时，极限 QPS 可信度低，建议以压测数据为准
- RT（耗时）指标没有显著拐点是正常现象，此时该指标无法作为评估结果，不参与极限 QPS 计算
- 算法评估基于历史数据，若近期有性能变化（版本发布、流量模式变化），评估结果可能滞后

### 压测评估分析

- `DATE`（最近压测日期）距今 > 14 天，压测数据可信度下降
- `records` 中历史压测的单机极限 QPS 波动 > 20%，说明服务性能不稳定
- 压测评估是线上真实流量压测，比算法评估更可信，但有一定滞后性

### 跨区对比

- 各区 `POD_LIMIT_QPS` 差异 > 20%，可能是机型规格不同或各区流量模式差异
- 各区 buffer 差异大，说明流量分配不均，某些区容量更紧张
