---
name: service_capacity_detail
description: "查询单个服务维度的容量详情信息（区别于场景维度），包括：(1) 实时容量水位（各可用区的实时QPS、周峰值QPS、水位百分比、告警阈值）；(2) 天粒度容量明细报表（CPU/内存/QPS/水位等多维度统计分析表格）；(3) 容量趋势图（资源利用率、流量及水位、资源用量、可用性等多组时序数据，默认14天）；(4) 服务资源特征雷达图（CPU/内存/网络IO/磁盘IO/内存延迟/内存带宽等维度的数值与分级，分值越高表示该服务在该类资源上越密集）。触发词：服务容量水位、服务容量明细、服务容量趋势、服务水位、单服务水位查询、服务容量分析、服务容量报表、极限QPS、压测水位、算法水位、服务维度容量、资源特征、资源密集型、雷达图、CPU密集、内存密集、网络密集、IO密集。"
---

# Capacity Detail Skill

通过 `scripts/capacity_detail_tools.py` 查询单服务的容量详情，支持四种查询模式。

## 用法

### 查询实时容量水位

```bash
python scripts/capacity_detail_tools.py water_level \
    --service omega-hf-merger-merger-default \
    --zones all
```

指定日期和可用区：
```bash
python scripts/capacity_detail_tools.py water_level \
    --service omega-hf-merger-merger-default \
    --zones alhz1,alsh1 \
    --date 2026-03-21
```

### 查询容量明细报表（天粒度统计分析）

```bash
python scripts/capacity_detail_tools.py stat \
    --service omega-hf-merger-merger-default
```

带过滤条件：
```bash
python scripts/capacity_detail_tools.py stat \
    --service omega-hf-merger-merger-default \
    --zones alhz1,alsh1 \
    --date 2026-03-21 \
    --pressure-eval
```

### 查询容量趋势（默认14天）

```bash
python scripts/capacity_detail_tools.py trend \
    --service omega-hf-merger-merger-default
```

指定时间范围：
```bash
python scripts/capacity_detail_tools.py trend \
    --service omega-hf-merger-merger-default \
    --start 2026-03-01 \
    --end 2026-03-21 \
    --zones alhz1,alsh1
```

### 查询服务资源特征雷达图

```bash
python scripts/capacity_detail_tools.py radar_chart \
    --service omega-vf-inv-2-searcher-default
```

指定聚合方式和日期：
```bash
python scripts/capacity_detail_tools.py radar_chart \
    --service omega-vf-inv-2-searcher-default \
    --aggregation P95 \
    --date 2026-03-22 \
    --zones alhz1,alsh1
```

## 参数说明

### water_level（实时容量水位）

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--service` | 是 | - | 服务名 |
| `--zones` | 否 | all | 可用区，逗号分隔，全选填 all |
| `--date` | 否 | - | 查询日期，格式 yyyy-MM-dd，不填为当天 |
| `--redstorm` | 否 | false | 是否包含 redstorm 压测数据 |

### stat（容量明细报表）

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--service` | 是 | - | 服务名 |
| `--zones` | 否 | all | 可用区，逗号分隔 |
| `--date` | 否 | - | 查询日期，格式 yyyy-MM-dd |
| `--pressure-eval` | 否 | false | true=算法水位，false=压测水位 |
| `--redstorm` | 否 | false | 是否包含 redstorm 压测数据 |

### trend（容量趋势）

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--service` | 是 | - | 服务名 |
| `--zones` | 否 | all | 可用区，逗号分隔 |
| `--start` | 否 | 14天前 | 起始日期，格式 yyyy-MM-dd |
| `--end` | 否 | 昨天 | 结束日期，格式 yyyy-MM-dd |
| `--pressure-eval` | 否 | false | true=算法水位，false=压测水位 |
| `--redstorm` | 否 | false | 是否包含 redstorm 压测数据 |

### radar_chart（资源特征雷达图）

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--service` | 是 | - | 服务名 |
| `--zones` | 否 | all | 可用区，逗号分隔 |
| `--date` | 否 | 昨天 | 查询日期，格式 yyyy-MM-dd |
| `--aggregation` | 否 | P95 | 聚合方式，P95 或 AVG |

### service_config（服务容量配置）

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--service` | 是 | - | 服务名 |

## 输出结构

### water_level 输出

```json
{
  "service": "omega-hf-merger-merger-default",
  "date": "2024-01-15",
  "zones": [
    {
      "zone": "alhz1",
      "real_time_qps": 1200.5,
      "week_max_qps": 3500.0,
      "threshold_warning": 0.85,
      "threshold_fatal": 0.95,
      "display": "pressure",
      "algorithm": {
        "realtime_limit": 5000,
        "limit": 5000,
        "realtime_water_level": 0.24,
        "week_max_water_level": 0.70
      },
      "pressure": {
        "realtime_limit": 4800,
        "limit": 4800,
        "realtime_water_level": 0.25,
        "week_max_water_level": 0.73
      }
    }
  ]
}
```

### stat 输出

```json
{
  "service": "merchantlambdaservice-service-homefeed-flsnotes-firstrank",
  "date": "2026-03-20",
  "headers": ["可用区", "本日实例数", "周峰值水位", "预估极限QPS", "周峰值QPS[本周-上周]", "周峰值CPU[本周-上周]", "日峰值QPS[本日-上日]", "日峰值CPU[本日-上日]", "日均值CPU利用率[本日-上日]", "日峰值内存使用率[本日-上日]", "最近一次压测日期", "日峰值磁盘IO（MB/s）[本日-上日]", "日峰值网络IO（MB/s）[本日-上日]", "日峰值内存延迟（ns）[本日-上日]", "CPU核数", "内存总量（GB）", "压测链接", "周峰值QPS时间"],
  "rows": [
    [
      "alhz1",
      "78",
      "102.3%",
      "79689",
      {"value": "81534", "diff": "-2226"},
      {"value": "104%", "diff": "+10%"},
      {"value": "80966", "diff": "-274"},
      {"value": "95%", "diff": "0%"},
      {"value": "80%", "diff": "0%"},
      {"value": "35%", "diff": "0%"},
      "2026-03-20",
      "0.1",
      "840.3",
      "163.1",
      "4524.0",
      "3120.0",
      "https://honghu.devops.xiaohongshu.com/pressureRecord?...",
      "2026-03-16 12:40:00"
    ]
  ]
}
```

### trend 输出

```json
{
  "service": "omega-hf-merger-merger-default",
  "start": "2024-01-01",
  "end": "2024-01-14",
  "groups": [
    {
      "title": "资源利用率",
      "charts": [
        {
          "title": "CPU(峰值)",
          "unit": "%",
          "series": [
            {
              "zone": "alhz1",
              "dates": ["2024-01-01", "2024-01-02"],
              "values": ["45.2", "47.8"]
            }
          ]
        }
      ]
    }
  ]
}
```

### radar_chart 输出

```json
{
  "service": "omega-vf-inv-2-searcher-default",
  "date": "2026-03-22",
  "aggregation": "P95",
  "metadata": { "...": "..." },
  "data": {
    "alhz1": [
      {"indicatorKey": "cpu_p95", "value": 72.5},
      {"indicatorKey": "mem_p95", "value": 45.2}
    ]
  }
}
```

### service_config 输出

```json
{
  "service": "lse-note-level-1-merger-default",
  "service_info": {
    "app": "lse-note-level-1",
    "biz_line": "search",
    "level": "S0",
    "service_type": "AUTOBOTS_LSE",
    "platform": "LSE",
    "language": "C++",
    "zones": ["qcnj2", "rcsh1", "alhz1", "alsh1-gray", "alsg1"],
    "cpu_num": 30.0,
    "gpu_card_num": 0.0,
    "owners": "zhangsan,lisi"
  },
  "metric_configs": [
    {
      "name": "cpu_avg",
      "type": "default",
      "source": "vms",
      "condition": "gt",
      "threshold": 0.6,
      "zone_thresholds": null
    },
    {
      "name": "rt_p99",
      "type": "default",
      "source": "vms",
      "condition": "gt",
      "threshold": 200.0,
      "zone_thresholds": {"alhz1": 180.0, "alsh1": 220.0}
    },
    {
      "name": "my_custom_metric",
      "type": "custom",
      "source": "vms",
      "condition": "gt",
      "threshold": 0.8,
      "zone_thresholds": null,
      "pql": "sum(rate(my_metric{service=\"foo\"}[1m]))",
      "datasource": "vms-app"
    }
  ],
  "buffer": 0.2,
  "alarm_enable": true,
  "alarm_threshold": 0.9,
  "alarm_zone_thresholds": null,
  "pressure_config": {
    "zones": ["alhz1", "alsh1"],
    "enable_schedule": true,
    "crontab": "0 2 * * 1",
    "crontab_desc": "每周一凌晨2点",
    "next_execute_time": "2026-03-30 02:00:00",
    "adjust_wait_time": 120,
    "pod_strategy": "intelligent",
    "traffic_strategy": {
      "name": "step-up-step",
      "value": 10,
      "zone_values": {}
    }
  },
  "water_level_config": {
    "daily": {"default": 1.0, "zoneConfig": {}},
    "activity": {"default": 1.2, "zoneConfig": {}}
  }
}
```

## 字段含义说明

### display 字段（water_level）

决定该可用区应以哪套水位为准：

- `"pressure"` — 展示压测水位（基于 pod 调权压测得出的极限 QPS）
- `"algorithm"` — 展示算法水位（基于历史数据算法推算的极限 QPS）

两种方式都是合法的容量评估手段，结果同等置信。`display` 由容量平台根据服务配置自动决定，分析时直接使用 `display` 指向的子对象数据即可，无需对评估方式本身做额外说明或质疑。

### algorithm / pressure 子对象字段

| 字段 | 说明 |
|------|------|
| `realtime_limit` | 当前实时极限 QPS（当前机器数对应的容量上限） |
| `limit` | 极限 QPS |
| `realtime_water_level` | 实时水位 = 实时 QPS / realtime_limit，取值 0~1 |
| `week_max_water_level` | 周峰值水位 = 周峰值 QPS / limit，取值 0~1 |

### 水位健康判断

以 `display` 指向的子对象的 `realtime_water_level` 为准，结合顶层阈值字段：

| 水位范围 | 状态 | 说明            |
|---------|----|---------------|
| < `threshold_warning` | 正常 | 容量充裕          |
| `threshold_warning` ≤ 水位 < `threshold_fatal` | 警告 | 需关注，建议扩容评估    |
| ≥ `threshold_fatal` | 危险 | 已触达危险水位，需立即处理 |

向用户描述时，`threshold_warning` 称为"警告水位线"，`threshold_fatal` 称为"危险水位线"，避免直接使用字段名。

### radar_chart 字段说明

`metadata.indicators` 定义了各资源维度的指标 key、单位、取值范围和 5 级分级规则。`data` 按可用区返回每个指标的实际值。

**分值越高，表示该服务在该类资源上越密集**（如 CPU 分值 5 级 = CPU 密集型服务）。

| indicatorKey | 资源类型 | 单位 | 说明 |
|---|---|---|---|
| `cpu_p95` / `cpu_avg` | CPU | percentunit (0-100) | CPU 利用率 |
| `mem_p95` / `mem_avg` | 内存 | percentunit (0-100) | 内存利用率 |
| `network_io_p95` / `network_io_avg` | 网络 IO | Mb/s（per core） | 每核网络 IO，归一化后衡量网络密集程度 |
| `disk_io_p95` / `disk_io_avg` | 磁盘 IO | MB/s | 磁盘读写 IO |
| `mem_latency` | 内存延迟 | ns | 内存访问延迟，越高表示内存访问压力越大 |
| `mem_bandwidth` | 内存带宽 | MB/s（per core） | 每核内存带宽，越高表示内存带宽越紧张 |
| `gpu_p95` / `gpu_avg` | GPU | percentunit (0-100) | GPU 利用率（仅 GPU 服务） |
| `gpu_mem_p95` | GPU 内存 | percentunit (0-100) | GPU 显存利用率（仅 GPU 服务） |

`threshold_warning` 和 `threshold_fatal` 典型值为 0.85 和 0.95，但各服务可能不同，以实际返回值为准。

### is_invalid 字段（water_level）

- `true`：该可用区数据无效（可能未配置或数据缺失），`reason` 字段说明原因，分析时跳过该区
- `false`：数据正常

### stat rows 格式说明

`rows` 是二维列表，每行按 `headers` 顺序排列，`rows[i][j]` 对应 `headers[j]` 列。

- 有环比数据的格：`{"value": "81534", "diff": "-2226"}`，`diff` 为环比变化值
- 无环比数据的格：直接是值字符串，如 `"alhz1"`

### trend 中 series.zone 字段

该字段实际为图例名（legend），通常是可用区名称，但也可能是聚合标签（如 `"all"`），不一定与 `--zones` 参数一一对应。

### pressure_eval 参数含义

- `false`（默认）— 使用**压测水位**：以实际压测得出的极限 QPS 计算水位
- `true` — 使用**算法水位**：以算法推算的极限 QPS 计算水位

两者都是合法的评估方式，结果同等置信，选择哪种取决于服务是否有压测记录。

### metric_configs 字段（service_config）

`metric_configs` 是服务配置的容量评估指标列表，决定了算法评估和压测评估的判断依据。

| 字段 | 含义 |
|------|------|
| `name` | 指标名，内置指标如 `cpu_avg`、`rt_p99`、`gpu_avg`；自定义指标为用户自定义名称 |
| `type` | `default`=内置指标，`custom`=自定义指标（有 `pql` 字段） |
| `source` | `vms`=Prometheus 数据源，`cat`=CAT 监控数据源 |
| `condition` | `gt`=指标超过阈值时触发（如 CPU > 60%），`lt`=指标低于阈值时触发（如成功率 < 99%） |
| `threshold` | 全局阈值，`null` 表示未配置（不参与评估） |
| `zone_thresholds` | 分区阈值，覆盖全局阈值；各区对延迟敏感度不同时会分区配置 |
| `pql` | 仅自定义指标有，Prometheus 查询语句 |

**分析要点：**
- 配置了多个指标时，算法评估取所有指标极限 QPS 的**短板**
- `threshold` 为 `null` 的指标不参与评估，仅作监控用途
- 有 `zone_thresholds` 的指标说明各区容量标准不同，分析时需按区对应阈值
- 存在 `custom` 类型指标，说明服务有特殊的容量瓶颈（非标准 CPU/RT），需关注该指标的含义

### pressure_config 字段（service_config）

| 字段 | 含义 |
|------|------|
| `zones` | 配置了压测的可用区（未在此列表中的区无压测数据） |
| `enable_schedule` | 是否开启定时压测 |
| `crontab` / `crontab_desc` | 定时压测的执行计划 |
| `next_execute_time` | 下次压测时间 |
| `pod_strategy` | pod 选择策略：`random`=随机、`intelligent`=智能选择、`intelligent-gpu`=GPU智能选择 |
| `traffic_strategy.name` | 加压策略：`default`=固定步长、`step-up-step`=阶梯加压、`binary`=二分查找 |
| `traffic_strategy.value` | 加压步长参数（含义随策略不同） |

**分析要点：**
- `enable_schedule: false` 说明未开启定时压测，压测数据可能较旧
- `zones` 列表不完整（少于服务实际部署区），说明部分区没有压测数据，水位来自算法评估

## 典型使用场景

| 用户问题 | 推荐接口 | 说明 |
|---------|---------|------|
| 当前水位是否安全？ | `service_config` + `water_level` | 先了解服务配置和阈值，再看实时水位 |
| 最近趋势如何，有没有上涨？ | `trend` | 默认14天趋势，观察 CPU/QPS/水位走势 |
| 昨天各区详细数据 | `stat` | 天粒度统计，含 CPU/内存/QPS/水位多维度 |
| 全面分析服务容量健康度 | `service_config` + `water_level` + `stat` + `trend` | 标准容量风险诊断流程 |
| 容量是否在持续恶化？ | `trend` | 观察水位趋势是否持续上升 |
| 这个服务是什么类型，有什么特点？ | `service_config` | 了解服务等级、平台、语言、CPU 规格等基本信息 |
| 这个服务是 CPU 密集还是内存密集？ | `radar_chart` | 按需调用，查看资源特征画像 |
| 内存延迟/网络IO/磁盘IO 情况如何？ | `radar_chart` | 按需调用，查看具体资源维度指标 |
| 服务是否具备容灾能力？ | `service_config` + `water_level` + `stat` | 基于现有数据推算容灾场景下的水位，无需额外接口 |

## AI 分析指引

> 分析时应尽量调用多个接口组合使用，单一接口只能给出片面结论。完整容量风险诊断建议依次调用 service_config → water_level → stat → trend。`radar_chart` 仅在用户明确关注资源特征（如"这个服务是 CPU 密集还是内存密集"、"内存延迟高不高"）时按需调用，常规容量风险分析不需要请求。

---

### 第零步：先查服务配置（service_config）

**在做任何容量分析之前，先调用 `service_config` 获取服务的基本配置**，后续所有分析都应结合配置信息进行。

关键字段及其对分析的影响：

| 字段 | 含义 | 对分析的影响 |
|------|------|------------|
| `metric_configs` | 容量评估指标列表（含阈值、类型、分区阈值） | 理解极限 QPS 是由哪些指标决定的，有自定义指标时需额外关注 |
| `alarm_threshold` | 水位告警阈值 | 即 `threshold_fatal` 的来源，说明告警触发条件时引用此值 |
| `level` | 服务等级（S0/S1/S2/S3） | S0/S1 为核心服务，容量风险影响更大 |
| `service_type` / `platform` | 服务类型和所属平台 | 不同类型服务的资源特征不同 |
| `buffer` | 容量缓冲比例 | 若 > 0，说明极限 QPS 计算时已预留 buffer，水位阈值相应更保守 |
| `pressure_config.zones` | 已配置压测的可用区 | 不在此列表的区无压测数据，水位来自算法评估 |
| `pressure_config.enable_schedule` | 是否开启定时压测 | `false` 说明压测需手动触发，数据可能较旧 |
| `zones`（service_info） | 服务部署的所有可用区 | 用于后续多区并发查询（water_level、capacity_evaluate 等） |

**`metric_thresholds` 各指标的单位说明**（threshold 值的含义因指标类型而异）：

| 指标类型 | 代表指标 | threshold 单位 | 示例 |
|---------|---------|--------------|------|
| CPU / 内存 / GPU / 磁盘利用率 | `cpu_avg`, `cpu_p95`, `mem_p95`, `gpu_avg` 等 | `percent`，0~1 小数 | `0.6` = 60% |
| 服务端/上游 RT | `rt_p99`, `rt_p95`, `client_rt_p99` 等 | `ns`（纳秒） | `500000000` = 500ms |
| 模型延迟指标 | `ttft_p99`, `e2e_p99`, `tpot_p99` 等 | `ms`（毫秒） | `200` = 200ms |
| 磁盘IO / 网络IO / 内存带宽 | `disk_io`, `network_io`, `mem_bandwidth` | `B/s`（字节/秒） | `104857600` = 100MB/s |
| 流量指标 | `qps`, `tps`, `rps` | 原始数值（次/秒） | `5000` = 5000 QPS |
| 成功率 | `availability`, `client_availability` 等 | `percent`，0~1 小数 | `0.999` = 99.9% |
| 线程池 / bthread | `thread_pool_usage`, `bthread_worker_usage` | `percent`，0~1 小数 | `0.8` = 80% |

**示例**：若 `metric_thresholds.cpu_avg.threshold = 0.6`，则分析 CPU 时应以 60% 为健康上限；若 `rt_p99.threshold = 500000000`，则 RT P99 健康上限为 500ms。

---

### water_level 分析

**第一步：数据有效性**
- 过滤 `is_invalid: true` 的可用区，说明原因（通常是实例数为 0 或未配置）
- 若所有区均无效，说明服务可能未部署或数据缺失，停止分析

**第二步：读取正确的水位**
- 以 `display` 字段为准，取对应子对象（`pressure` 或 `algorithm`）的数据
- 优先关注 `week_max_water_level`（周峰值水位）而非 `realtime_water_level`——前者反映最坏情况，是容量规划的核心指标
- `realtime_water_level` 反映当前瞬时状态，不能单独作为容量健康的判断依据

**第三步：健康状态判断**

| 周峰值水位 | 状态 | 分析结论                  |
|-----------|----|-----------------------|
| < `threshold_warning` | 正常 | 容量充裕，有安全余量            |
| `threshold_warning` ≤ 水位 < `threshold_fatal` | 警告 | 峰值期间容量紧张，建议评估扩容       |
| ≥ `threshold_fatal` | 危险 | 已触达危险水位线，存在过载风险，需立即处理 |

**第四步：深度分析**
- **跨区对比**：各区水位是否均衡？若某区明显偏高，可能存在流量分配不均，需结合 `real_time_qps` 和 `week_max_qps` 判断（alsh1-gray 为灰度区，水位通常偏低，不参与对比）
- **realtime_limit vs limit 差异**：`realtime_limit` 基于当前实例数计算，`limit` 基于天维度缓存（昨天）的实例数。若两者差距大，说明服务近期有扩缩容

---

### stat 分析

**核心指标优先级**（从高到低）：

1. **周峰值QPS & 周峰值QPS时间**：关注峰值出现的时间点，判断是否为业务高峰（如午高峰、晚高峰）还是异常毛刺；结合上周周峰值对比，判断流量是否在增长

**环比分析**（`diff` 字段）：
- `diff_color: 1` 表示环比上涨，需判断是否为异常增长
- 周峰值QPS 环比上涨 > 10%，需结合业务背景解释原因（活动、版本发布等）
- CPU 环比上涨但 QPS 持平，可能存在性能劣化，需排查

**跨区对比**：
- 各区实例数差异大，说明流量分配不均或各区规格不同
- 各区 CPU 利用率差异 > 20%，需关注是否有区域性问题或机型差异

---

### trend 分析

trend 接口返回天粒度时序数据，是判断长期趋势、发现劣化、预测风险的核心依据。

**分析框架**：先看趋势方向 → 再看变化幅度 → 最后判断风险时间窗口

#### QPS 长期趋势与预测

- 判断 QPS 整体走势：增长 / 下跌 / 平稳 / 周期性波动（工作日 vs 周末）
- **未来预测**：基于近 14 天数据做线性外推，给出未来 7 天和 30 天的 QPS 预测值，并附 ±10% 浮动区间
  - 若趋势有加速迹象（斜率增大），需说明预测可能偏保守
  - 若近期有明显跳升（版本发布/活动），需排除异常点后重新拟合

#### 性能劣化判断

以下信号组合出现时，判定存在性能劣化：
- **CPU 劣化**：QPS 持平或下降，但 CPU 利用率持续上升（单位 QPS 消耗 CPU 增加）
- **RT 劣化**（如 trend 中有 RT 指标）：RT 持续上升，且与 QPS 增长不成比例
- **可用性劣化**：可用性下降，且与水位高峰时间吻合，说明容量不足已影响稳定性

劣化判断后，需结合水位趋势估算**何时触达安全水位阈值**：
- 若水位在 N 天内从 X% 线性增长到 Y%，计算触达 `threshold_warning` 的剩余天数
- 公式：`剩余天数 = (threshold_warning - 当前水位) / 日均增长率`

#### 资源利用率组（CPU/内存）

- 持续上升：结合斜率估算何时触达告警阈值，给出预警时间
- 突然跳升后平稳：通常对应版本发布或流量迁入，需确认是否正常
- CPU 上升但内存平稳：计算密集型负载增加；内存上升但 CPU 平稳：可能有内存泄漏风险

#### 资源用量组（CPU总量/内存总量）

- 用量突增/突降对应扩缩容动作，可还原近期容量变更历史
- 扩容后水位下降幅度是否符合预期（扩容比例 ≈ 水位下降比例）

#### 分区差异与机型性能差异

- 同一服务各区 CPU 利用率差异 > 20%，可能原因：
  1. 流量分配不均（需检查调度策略）
  2. 各区机型规格不同（CPU 主频/核数差异导致相同 QPS 下 CPU 利用率不同）
  3. 某区存在局部问题（如 GC 频繁、连接池满）
- 若各区 QPS 相近但 CPU 差异大，优先怀疑机型差异，建议对比各区实例规格

---

### radar_chart 分析

radar_chart 反映服务的资源特征画像，用于理解服务属于哪类资源密集型，**不直接给出扩容建议**。

---

### 综合分析与操作建议

#### 扩缩容建议

**扩容触发条件**（满足任一）：
- 周峰值水位 ≥ `threshold_warning`（通常 85%）
- 安全余量 < 15%（极限QPS - 周峰值QPS）/ 极限QPS
- trend 显示水位持续上升，预计 14 天内触达告警阈值

**扩容量估算**：
- 目标水位建议控制在 60%~70%（留有充足余量应对突发）
- 扩容比例 = 当前水位 / 目标水位 - 1
- 例：当前水位 90%，目标 65%，需扩容约 38%（即当前实例数 × 1.38）

**缩容触发条件**（同时满足）：
- 周峰值水位持续 < 40% 超过 7 天
- trend 显示 QPS 无增长趋势
- 无近期大促或活动计划

**缩容量估算**：
- 目标水位建议不超过 65%
- 缩容比例 = 1 - 当前水位 / 目标水位

#### 常见问题模式

| 现象组合 | 可能原因 | 建议动作 |
|---------|---------|---------|
| 水位高 + CPU 高 + 趋势上升 | 真实容量不足，流量增长 | 立即扩容，评估极限 QPS |
| 水位正常 + CPU 持续上升 | 性能劣化，单机处理能力下降 | 排查性能回归，检查近期变更 |
| 各区水位差异大（alsh1-gray 除外） | 流量分配不均或机型差异 | 检查流量调度策略及各区机型规格 |
| 趋势平稳但周峰值水位 > 85% | 长期高水位，无安全余量 | 制定扩容计划，避免突发流量打穿 |

---

### 容灾能力评估

容灾评估不需要额外接口，基于 `water_level`（各区实例数、极限QPS、水位）和 `stat`（各区实例数、周峰值QPS）数据推算。

#### 核心计算逻辑

**所需数据**（从已有接口获取）：
- 各区实例数：`stat` 中的"本日实例数"，或 `water_level` 中的 `REPLICAS`
- 各区极限 QPS：`water_level` 中 `display` 指向的 `limit`
- 各区周峰值 QPS：`water_level` 中的 `week_max_qps`
- 单机极限 QPS：`极限QPS / 实例数`

**场景一：单 pod 挂掉**

```
容灾后实例数     = 当前实例数 - 1
容灾后极限 QPS   = 单机极限 QPS × 容灾后实例数
容灾后水位       = 周峰值 QPS / 容灾后极限 QPS
```

对每个可用区独立计算，判断单 pod 故障后该区水位是否超过告警阈值。

**场景二：单可用区挂掉**

流量会重新分配到其他存活区，需要估算流量承接比例：

```
# 假设流量按各区实例数比例重新分配（等比承接）
存活区承接流量比例 = 存活区实例数 / 全部实例数
存活区新增流量     = 故障区周峰值 QPS × (存活区实例数 / 其他存活区实例数之和)
存活区容灾后水位   = (存活区周峰值 QPS + 存活区新增流量) / 存活区极限 QPS
```

逐一模拟每个区挂掉的场景，找出最危险的故障区（即该区挂掉后其他区压力最大）。

#### 容灾能力判定标准

| 容灾后水位 | 判定 | 说明 |
|-----------|------|------|
| < `threshold_warning` | 具备容灾能力 | 故障后仍有安全余量 |
| `threshold_warning` ≤ 水位 < `threshold_fatal` | 容灾能力偏弱 | 故障后处于警告区间，存在风险 |
| ≥ `threshold_fatal` | 不具备容灾能力 | 故障后水位超限，可能引发级联故障 |

#### 分析输出建议

给出以下结论：
1. **单 pod 容灾**：各区是否均能承受单 pod 故障，列出最脆弱的区（容灾后水位最高的区）
2. **单区容灾**：哪些区挂掉后其他区能承接，哪些区挂掉后会导致整体超限
3. **最危险故障区**：哪个区挂掉影响最大
4. **容灾缺口**：若不具备容灾能力，需要扩容多少实例才能满足容灾要求

**容灾扩容量估算**：
```
目标：容灾后水位 ≤ threshold_warning（如 85%）
所需极限 QPS = 容灾场景下的总流量 / threshold_warning
所需实例数   = 所需极限 QPS / 单机极限 QPS
需新增实例数 = 所需实例数 - 当前实例数
```

#### 注意事项

- 流量重分配假设为等比承接，实际取决于负载均衡策略，结论仅供参考
- alsh1-gray 为灰度区，流量极少，通常不参与容灾计算
- 若各区实例数差异较大，单区故障的影响差异也会很大，需逐区分析
- 容灾评估基于周峰值 QPS（最坏情况），若故障发生在低峰期实际影响会更小
