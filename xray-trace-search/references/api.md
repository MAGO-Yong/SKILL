# /analysisSearch 接口参考文档

## 接口信息

- **完整地址**: `POST https://xray-ai.devops.xiaohongshu.com/open/skill/tracing/analysisSearch`
- **Content-Type**: `application/json`
- **功能**: 批量查询指定服务+接口在某时间段内的 Span，返回精简 Span 列表 + 多维度聚合分析

支持两种搜索模式（通过 `mode` 字段指定）：

- **ERROR**（默认）— 查询异常 Span（status=1），可通过 `errorNames` 过滤异常类型
- **SLOW** — 查询慢 Span（按耗时降序），支持 `minDurationMs` 阈值 + `topN`
  截断，额外返回耗时统计和桶分布

---

## 请求参数

```json
{
  "app": "string",
  "endpoint": "string",
  "start": 1700000000,
  "end": 1700003600,
  "mode": "SLOW",
  "errorNames": ["NullPointerException"],
  "minDurationMs": 1000,
  "topN": 20,
  "limit": 500
}
```

### 参数说明

| 参数            | 类型           | 必填 | 适用模式   | 说明                                                                                           |
| --------------- | -------------- | ---- | ---------- | ---------------------------------------------------------------------------------------------- |
| `app`           | String         | 是   | 通用       | 服务/应用名                                                                                    |
| `endpoint`      | String         | 否   | 通用       | 格式：`transactionType.transactionName`，如 `Http./api/v1/user`、`Service.com.xxx.SomeService` |
| `start`         | Long           | 是   | 通用       | 秒级时间戳，开始时间                                                                           |
| `end`           | Long           | 是   | 通用       | 秒级时间戳，结束时间，必须 > start                                                             |
| `mode`          | String         | 否   | 通用       | `ERROR`（默认）/ `SLOW`，null 时降级为 ERROR（向后兼容）                                       |
| `limit`         | Integer        | 否   | 通用       | 默认 500，最大 1000                                                                            |
| `errorNames`    | List\<String\> | 否   | ERROR 模式 | 异常类名白名单，如 `["IOException", "TimeoutException"]`                                       |
| `minDurationMs` | Long           | 否   | SLOW 模式  | 耗时下限（毫秒），只返回 durationMs >= 该值的 Span，必须为正整数                               |
| `topN`          | Integer        | 否   | SLOW 模式  | 返回最慢的 Top N 条，默认 10，必须为正整数                                                     |

### 校验规则

- `end > start`
- `end - start <= 7 * 24 * 3600`（最大跨度 7 天）
- `limit ∈ (0, 1000]`
- ERROR 模式：固定只查询失败/异常 Span（status=1）
- SLOW 模式：`minDurationMs > 0`（若传），`topN > 0`（若传）

---

## 响应结构

```json
{
  "success": true,
  "code": "200",
  "data": {
    "total": 1234,
    "spans": [...],
    "traceIds": ["abc123", "def456"],
    "aggregation": {...}
  }
}
```

### `spans[]` — SpanAnalysisBrief 字段

| 字段              | 类型           | 说明                         |
| ----------------- | -------------- | ---------------------------- |
| `traceId`         | String         | 链路 ID                      |
| `segmentId`       | String         | Segment ID                   |
| `spanId`          | Integer        | Span ID                      |
| `app`             | String         | 所属服务                     |
| `transactionType` | String         | 事务类型（如 URL、RPC）      |
| `transactionName` | String         | 事务名（如 /api/v1/user）    |
| `startTimestamp`  | Instant        | Span 开始时间（微秒精度）    |
| `durationMs`      | Long           | 耗时（毫秒）                 |
| `podName`         | String         | Pod 名称                     |
| `ip`              | String         | Pod IP                       |
| `zone`            | String         | 所在机房                     |
| `downstreamIp`    | String         | 下游 IP                      |
| `downstreamZone`  | String         | 下游机房                     |
| `hasException`    | Boolean        | 是否有异常                   |
| `errorTypes`      | List\<String\> | 异常类型列表                 |
| `entry`           | String         | 来源入口                     |
| `acrossZone`      | Boolean        | 是否跨机房                   |
| `spanType`        | String         | ENTRY / EXIT / LOCAL         |
| `bizType`         | String         | RPC / CACHE / DB / MQ / HTTP |
| `readWriteFlag`   | Integer        | 1=读, 2=写                   |

### `aggregation` — 通用维度（ERROR / SLOW 均返回）

| 字段                         | Key 格式                          | 说明                 |
| ---------------------------- | --------------------------------- | -------------------- |
| `spanNameDistribution`       | `transactionType:transactionName` | 哪个接口最集中       |
| `downstreamIpDistribution`   | `ip`                              | 访问哪个下游集群最多 |
| `entryDistribution`          | `entry`                           | 来自哪个入口         |
| `podDistribution`            | `podName:ip`                      | 是否单 POD 热点      |
| `crossZoneRatio`             | 百分比                            | 跨机房调用占比       |
| `zoneDistribution`           | `zone`                            | 集中机房             |
| `downstreamZoneDistribution` | `downstreamZone`                  | 下游哪个机房         |
| `errorTypeDistribution`      | `errorType`                       | 异常类型分布         |

所有分布类字段均为 `Map<String, Long>`，按 count 降序排列。

### `aggregation` — SLOW 模式专有字段

| 字段                         | 类型               | 说明                                                  |
| ---------------------------- | ------------------ | ----------------------------------------------------- |
| `durationStats`              | Object             | 耗时统计摘要（见下）                                  |
| `durationBucketDistribution` | Map\<String,Long\> | 耗时桶分布，key 为桶区间（如 `1-3s`），按固定顺序返回 |

#### `durationStats` 字段

| 字段    | 类型 | 说明             |
| ------- | ---- | ---------------- |
| `count` | int  | 采样 Span 数量   |
| `avgMs` | long | 平均耗时（毫秒） |
| `minMs` | long | 最小耗时（毫秒） |
| `maxMs` | long | 最大耗时（毫秒） |
| `p50Ms` | long | P50 耗时（毫秒） |
| `p90Ms` | long | P90 耗时（毫秒） |
| `p99Ms` | long | P99 耗时（毫秒） |

#### `durationBucketDistribution` 桶边界

| 桶 key      | 耗时范围      |
| ----------- | ------------- |
| `0-100ms`   | < 100ms       |
| `100-500ms` | 100ms ~ 500ms |
| `500ms-1s`  | 500ms ~ 1s    |
| `1-3s`      | 1s ~ 3s       |
| `3-5s`      | 3s ~ 5s       |
| `5-10s`     | 5s ~ 10s      |
| `10s+`      | >= 10s        |

计数为 0 的桶不返回。

---

## 示例请求

```bash
# ERROR 模式（默认，兼容旧调用）
python3 <skill_dir>/scripts/analysis_search.py \
  --app xray-server \
  --start 1711339200 \
  --end 1711342800 \
  --endpoint "Http./api/trace/search" \
  --error-names "TimeoutException" \
  --limit 200

# SLOW 模式
python3 <skill_dir>/scripts/analysis_search.py \
  --app xray-server \
  --start 1711339200 \
  --end 1711342800 \
  --mode SLOW \
  --endpoint "Service.com.xxx.SomeService" \
  --min-duration-ms 1000 \
  --top-n 20
```

## 注意事项

- `endpoint` 使用第一个 `.` 分割：左侧为 `transactionType`，右侧为 `transactionName`
- SLOW 模式下 `topN` 截断发生在服务端，实际返回 Span 数 = min(topN, limit, total)
- `limit` 仅控制返回的 Span 数量，`total` 是实际命中总数
- `mode=null` 与 `mode=ERROR` 行为完全一致（向后兼容）
- SLOW 模式查询的 Span 不限 status，慢但成功的请求同样会返回
