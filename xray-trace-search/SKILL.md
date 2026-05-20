---
name: xray-trace-search
description:
  '查询服务的 trace 链路数据，支持按服务名、时间范围、异常类名、pod、接口、耗时、traceId
  等多维度过滤。触发场景：(1) 用户提到某个服务某个接口的异常情况（如"分析 xxx 服务 /api/v1/foo
  接口的异常"、"查看 yyy 服务 queryXxx 接口报什么错"）——此时的"接口"指链路中的 endpoint，应使用本
  skill 做 trace 级别的接口异常聚合分析，而不是异常堆栈分析；(2) 具体的接口、trace
  搜索、链路查询、异常 trace、慢请求；(3) traceId 查询、错误链路、xray trace、调用链、pod
  异常、接口耗时；(4)
  用户说"分析某个服务的链路情况"、"查看服务链路"、"分析链路"等与服务链路相关的查询；(5)
  用户说"分析某接口的慢请求"、"查看耗时最长的请求"、"p99 耗时分析"等慢请求分析场景。'
metadata:
  category: trace
  subcategory: batch-search
  platform: xray
  trigger: service_name/endpoint/time_range/errorNames/mode
  input: [service, endpoint, st, et, mode, errorNames, minDurationMs, topN]
  output: [spans, traceIds, aggregation_analysis, durationStats]
  impl: http-api
---

# XRay Span 批量查询

> `{SKILL_DIR}` 为本 skill 所在目录的绝对路径，执行脚本时必须使用绝对路径。

## 概述

调用 `/analysisSearch` 接口，支持两种搜索模式：

| 模式              | 适用场景               | 查询目标              | 专有参数                |
| ----------------- | ---------------------- | --------------------- | ----------------------- |
| **ERROR**（默认） | 排查接口异常、报错分析 | 异常 Span（status=1） | `errorNames`            |
| **SLOW**          | 排查慢请求、耗时分析   | 慢 Span（按耗时降序） | `minDurationMs`、`topN` |

两种模式均输出：精简 Span 列表、去重 traceId 列表、多维度聚合分析。SLOW 模式额外返回：耗时统计（avg/p50/p90/p99）和耗时桶分布。

接口参数与响应字段详见 [references/api.md](references/api.md)。

---

## 工作流程

### Step 1：收集参数

**首先判断搜索模式**：

- 用户提到"慢请求"、"耗时分析"、"p99"、"响应慢"、"最慢" → 使用 **SLOW 模式**
- 用户提到"报错"、"异常"、"错误"、"exception" → 使用 **ERROR 模式**
- 未明确时默认使用 **ERROR 模式**

**必要参数：**

| 参数            | 必填 | 说明                                                                                                                                                        |
| --------------- | ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app`           | 是   | 服务名（必须严格使用用户提供的原始值，不得拆分、补全或修改任何字符）                                                                                        |
| `start` / `end` | 是   | 时间范围，支持自然语言，转为秒级时间戳                                                                                                                      |
| `endpoint`      | 否   | 格式：`transactionType.transactionName`，如 `Http./api/v1/user`、`Service.com.xxx.SomeService`（服务端 RPC）或 `Call.下游服务名.下游接口`（客户端出站 RPC） |

**ERROR 模式参数：**

| 参数         | 必填 | 说明                                |
| ------------ | ---- | ----------------------------------- |
| `errorNames` | 否   | 异常类型过滤，如 `TimeoutException` |

**SLOW 模式参数：**

| 参数            | 必填 | 说明                                                 |
| --------------- | ---- | ---------------------------------------------------- |
| `minDurationMs` | 否   | 耗时下限（毫秒），如 `1000` 表示只查 >= 1s 的慢 Span |
| `topN`          | 否   | 取最慢的前 N 条，默认 10                             |

**通用可选参数：**

| 参数    | 说明                          |
| ------- | ----------------------------- |
| `limit` | 返回条数，默认 500，最大 1000 |

**时间收集原则：**

- 若用户说"最近 1 小时"→ `end=now, start=now-3600`
- 若用户说"今天上午 10 点到 11 点"→ 转换为对应时间段秒级时间戳
- 若用户未说明时间 → 主动询问
- 若用户提供时间范围字符串，使用 `to_timestamp.py` 转换：
  ```bash
  python3 {SKILL_DIR}/scripts/to_timestamp.py --range "2024-03-25 14:00:00 - 2024-03-25 15:10:10"
  # 输出为秒级时间戳，不是毫秒，直接作为 --start / --end 参数值使用
  # 也支持: --range "now-1h - now" / --start "2024-03-25 14:00" --end "2024-03-25 15:00"
  ```

**endpoint 收集原则：**

- 若用户只说了接口路径（未提及调用下游）：
  - 以 `/` 开头（如 `/api/v1/user`）→ HTTP 接口，补充 `Http.` 前缀 → `Http./api/v1/user`
  - 其他形式（如 `com.xxx.SomeService`、`queryXxx`）→ 默认视为服务端 RPC，补充 `Service.` 前缀
- 若用户说**作为客户端调用下游**的 RPC 接口，前缀用 `Call.` → `Call.${下游服务名}.${下游接口}`
- 以上均无法判断时追问用户
- 若用户未提供 endpoint → 不传，查询整个服务

### Step 2：调用接口

使用 Bash 工具执行 `scripts/analysis_search.py`：

```bash
# ERROR 模式（默认）
python3 {SKILL_DIR}/scripts/analysis_search.py \
  --app "<服务名>" \
  --start <秒级时间戳> \
  --end <秒级时间戳> \
  [--endpoint "transactionType.transactionName"] \
  [--error-names "TimeoutException,IOException"] \
  [--limit 500]

# SLOW 模式
python3 {SKILL_DIR}/scripts/analysis_search.py \
  --app "<服务名>" \
  --start <秒级时间戳> \
  --end <秒级时间戳> \
  --mode SLOW \
  [--endpoint "transactionType.transactionName"] \
  [--min-duration-ms 1000] \
  [--top-n 20] \
  [--limit 500]
```

**参数映射：**

| 脚本参数            | 对应字段        | 说明                                         |
| ------------------- | --------------- | -------------------------------------------- |
| `--app`             | `app`           | 服务名（必填，原样使用用户输入值，禁止修改） |
| `--start`           | `start`         | 开始时间秒级时间戳（必填）                   |
| `--end`             | `end`           | 结束时间秒级时间戳（必填）                   |
| `--mode`            | `mode`          | ERROR / SLOW，不传默认 ERROR                 |
| `--endpoint`        | `endpoint`      | 接口过滤（选填）                             |
| `--error-names`     | `errorNames`    | 逗号分隔的异常类型（选填，ERROR 模式）       |
| `--min-duration-ms` | `minDurationMs` | 耗时下限毫秒（选填，SLOW 模式）              |
| `--top-n`           | `topN`          | 最慢 Top N 截断（选填，SLOW 模式）           |
| `--limit`           | `limit`         | 返回条数，默认 500（选填）                   |

### Step 3：解析并输出结果

#### 1. 概览

- 命中 Span 总数（`total`）、返回 Span 数、去重 traceId 数

#### 2. SLOW 模式专有（有数据才展示）

- **耗时统计** `durationStats`：展示 avg / min / max / p50 / p90 / p99
- **耗时桶分布** `durationBucketDistribution`：展示各桶（`0-100ms` ~ `10s+`）的 Span 数量

#### 3. 通用聚合分析（按 count 降序，有数据才展示）

- **异常类型分布** `errorTypeDistribution`
- **接口分布** `spanNameDistribution`
- **Pod 分布** `podDistribution`
- **机房分布** `zoneDistribution` / `downstreamZoneDistribution`
- **跨机房占比** `crossZoneRatio`
- **下游集群分布** `downstreamIpDistribution`
- **入口分布** `entryDistribution`

#### 4. Span 列表摘要（取前 10 条展示）

每条展示：`traceId`、`durationMs`、`spanType`、`errorTypes`、`podName`、`zone`

#### 5. traceId 列表

列出所有去重后的 traceId，并在列表展示后**主动询问用户**：

> 已找到 N 个 traceId，是否需要进一步分析？
>
> 1. **单链路分析**（xray-single-trace-analysis）：针对某条 traceId 做异常 Span 定位与根因分析
> 2. **日志查询**（xray-log-query）：根据 traceId 查询关联的应用日志详情
> 3. 不需要，结束

根据用户选择：

- 选择 1 → 调用 `xray-single-trace-analysis` skill
- 选择 2 → 调用 `xray-log-query` skill
- 选择 3 → 结束

---

## 注意事项

- **服务名原样透传**：`--app` 参数必须严格使用用户提供的原始服务名，禁止修改任何字符
- ERROR 模式固定只查异常 Span（status=1）；SLOW 模式不限 status，慢但成功的请求也会返回
- `total` 是命中总数，`spans` 列表受 `limit` 限制，两者可能不同
- SLOW 模式下 `topN` 截断发生在服务端，实际返回数 = min(topN, limit, total)
- 若 `total` 远大于 `limit`，提示用户缩小时间范围或增加过滤条件
- `endpoint` 用第一个 `.` 分割，`transactionName` 中的 `.` 不影响
- 最大查询时间跨度为 7 天
