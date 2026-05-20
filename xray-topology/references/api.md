# XRay 拓扑 API 参考

## 目录

1. [接口总览](#接口总览)
2. [SERVICE 模式：服务拓扑](#service-模式服务拓扑)
3. [ENTRY 模式：流量入口拓扑](#entry-模式流量入口拓扑)
4. [CAT 模式：CAT 拓扑（降级）](#cat-模式cat-拓扑降级)
5. [响应结构：节点与边](#响应结构节点与边)
6. [枚举值说明](#枚举值说明)

---

## 接口总览

| 模式    | HTTP 方法 | URL                                     | 代码位置                                            |
| ------- | --------- | --------------------------------------- | --------------------------------------------------- |
| SERVICE | POST      | `/searchAdvancedRpcTopology`            | `EntryTopologyController#searchAdvancedRpcTopology` |
| ENTRY   | POST      | `/searchEntryTopology`                  | `EntryTopologyController#searchEntryTopology`       |
| CAT     | GET       | `/application/topology/serviceTopology` | `TopologyController#topology`                       |

---

## SERVICE 模式：服务拓扑

**接口**：`POST /searchAdvancedRpcTopology`

**请求体**（JSON）：

| 字段              | 类型            | 必填 | 说明                                                   |
| ----------------- | --------------- | ---- | ------------------------------------------------------ |
| `app`             | String          | 是   | 服务名，不可为空                                       |
| `start`           | Long            | 是   | 开始时间，**单位：秒**                                 |
| `end`             | Long            | 是   | 结束时间，**单位：秒**                                 |
| `service`         | String          | 否   | RPC 接口名；传 `"-"` 或 `"NONE_SPECIFIED"` 等价于不传  |
| `entryList`       | List\<String\>  | 否   | 入口 URL 列表；为空时使用服务所有入口                  |
| `focusOption`     | FocusOption     | 否   | 关注维度，默认 `direct_relations_each_direction_top10` |
| `preProcessEnum`  | PreProcessEnum  | 否   | 调用类型，默认 `RPC`                                   |
| `perfTestInclude` | PerfTestInclude | 否   | 压测流量策略，默认 `UNION_PERF_TEST`                   |

**请求示例**：

```json
{
  "app": "checkoutcenter-service-defaultunit",
  "focusOption": "direct_relations_each_direction_top10",
  "preProcessEnum": "RPC",
  "start": 1776152576,
  "end": 1776153476,
  "perfTestInclude": "UNION_PERF_TEST"
}
```

---

## ENTRY 模式：流量入口拓扑

**接口**：`POST /searchEntryTopology`

**请求体**（JSON）：

| 字段               | 类型            | 必填 | 说明                                                |
| ------------------ | --------------- | ---- | --------------------------------------------------- |
| `entryList`        | List\<String\>  | 是   | HTTP 入口 URL 列表（不含协议头）                    |
| `startTime`        | long            | 是   | 开始时间，**单位：毫秒**                            |
| `endTime`          | long            | 是   | 结束时间，**单位：毫秒**                            |
| `level`            | TopologyLevel   | 是   | `app`（应用级）或 `service`（接口级）               |
| `summingAllSource` | boolean         | 否   | 默认 `true`（合并所有调用方）；`false` 时区分调用方 |
| `preProcessEnum`   | PreProcessEnum  | 否   | 调用类型，默认 `RPC_DATA`                           |
| `perfTestInclude`  | PerfTestInclude | 否   | 压测流量策略，默认 `UNION_PERF_TEST`                |

**请求示例**：

```json
{
  "entryList": ["edith-liruoqi3.sl.beta.xiaohongshu.com/api/sns/v4/search/trending"],
  "level": "app",
  "startTime": 1776152789849,
  "endTime": 1776153689849,
  "summingAllSource": false,
  "preProcessEnum": "RPC",
  "perfTestInclude": "UNION_PERF_TEST"
}
```

---

## CAT 模式：CAT 拓扑（降级）

**接口**：`GET /application/topology/serviceTopology`

**Query 参数**：

| 参数        | 类型    | 必填 | 说明                                         |
| ----------- | ------- | ---- | -------------------------------------------- |
| `app`       | String  | 是   | 服务名                                       |
| `withApi`   | boolean | 否   | 默认 `false`（服务级拓扑）；`true` 为 API 级 |
| `startTime` | Long    | 否   | 开始时间（秒或毫秒，服务端自动解析）         |
| `endTime`   | Long    | 否   | 结束时间                                     |
| `withZone`  | boolean | 否   | 默认 `false`；`true` 时填充节点区域信息      |
| `date`      | String  | 否   | 日期字符串（代码接收但未使用）               |

**请求示例**：

```
GET /application/topology/serviceTopology?withApi=false&startTime=1776067439&endTime=1776153839&app=checkoutcenter-service-defaultunit
```

---

## 响应结构：节点与边

### SERVICE / ENTRY 模式共同响应体

**外层包装** `BaseResponse<EntryTopologyResponse>`：

```json
{
  "success": true,
  "code": "200",
  "cat_id": "...",
  "trace_id": "...",
  "data": { ... }
}
```

**`data`（EntryTopologyResponse）**：

| 字段            | 类型                   | 说明                                        |
| --------------- | ---------------------- | ------------------------------------------- |
| `nodes`         | List\<NodeWithMetric\> | 拓扑节点列表                                |
| `edges`         | List\<EdgeWithMetric\> | 拓扑边列表                                  |
| `rows`          | List\<EdgeWithMetric\> | 表格行（与 edges 内容一致，可用于表格展示） |
| `defaultNodeId` | String                 | 默认高亮节点 ID（对应请求中的 app+service） |

**`NodeWithMetric` 字段**：

| 字段                                                          | 类型              | 说明                                               |
| ------------------------------------------------------------- | ----------------- | -------------------------------------------------- |
| `id`                                                          | String            | 节点唯一 ID                                        |
| `name`                                                        | String            | 节点名称（通常是服务名或接口名）                   |
| `app`                                                         | String            | 所属服务名                                         |
| `service`                                                     | String            | RPC 接口名（service 粒度下有值）                   |
| `nodeType`                                                    | String            | 节点类型（如 `Service`）                           |
| `status`                                                      | String            | 健康状态：`info`（正常）/ `warn`/ `error` 等       |
| `withMetrics`                                                 | boolean           | 是否有性能指标；`false` 的节点（如虚拟节点）无指标 |
| `total`                                                       | double            | 调用次数（单位：次/时间段）                        |
| `avgDuration`                                                 | double            | 平均耗时（ms）                                     |
| `maxDuration`                                                 | long              | 最大耗时（ms）                                     |
| `error`                                                       | double            | 错误次数                                           |
| `examplar`                                                    | String            | 样本 Trace ID（可用于 logview 分析）               |
| `inDegree`                                                    | int               | 入度（被多少上游直接调用）                         |
| `outDegree`                                                   | int               | 出度（依赖多少下游）                               |
| `tags`                                                        | List\<NodeTagVO\> | 节点标签，含 `color` 和 `message`                  |
| `totalStr` / `errorStr` / `avgDurationStr` / `maxDurationStr` | String            | 格式化展示字符串                                   |

**`EdgeWithMetric` 字段**：

| 字段                                                                               | 类型          | 说明                                                  |
| ---------------------------------------------------------------------------------- | ------------- | ----------------------------------------------------- |
| `source`                                                                           | String        | 边起点节点 ID                                         |
| `sourceApp`                                                                        | String        | 调用方服务名                                          |
| `sourceService`                                                                    | String        | 调用方接口名（接口级别时有值）                        |
| `target`                                                                           | String        | 边终点节点 ID                                         |
| `targetApp`                                                                        | String        | 被调用方服务名                                        |
| `targetService`                                                                    | String        | 被调用方接口名（接口级别时有值）                      |
| `edgeType`                                                                         | String        | 调用类型：`Service`（RPC）/ `Redis` / `SQL` / `MQ` 等 |
| `total`                                                                            | double        | 调用次数                                              |
| `avgDuration`                                                                      | double        | 平均耗时（ms）                                        |
| `maxDuration`                                                                      | long          | 最大耗时（ms）                                        |
| `error`                                                                            | double        | 错误次数                                              |
| `magnification`                                                                    | Double        | 放大倍数（相对于入口流量的比例，1.0=100%）            |
| `examplar`                                                                         | String        | 样本 Trace ID                                         |
| `entrySet`                                                                         | Set\<String\> | 构造该边的流量入口 URL 集合                           |
| `magnificationStr` / `totalStr` / `avgDurationStr` / `maxDurationStr` / `errorStr` | String        | 格式化展示字符串                                      |

### CAT 模式响应体

**外层** `Result<TopologyReportVO>`：

```json
{
  "success": true,
  "code": 200,
  "data": {
    "topologyNode": { ... },
    "endpoints": [ ... ]
  }
}
```

**`TopologyReportVO`**：

| 字段           | 说明                                            |
| -------------- | ----------------------------------------------- |
| `topologyNode` | 拓扑树根节点（含 upstream/downstream 两个子树） |
| `endpoints`    | 服务的入口端点列表                              |

**`TopologyNode` 字段**：

| 字段              | 类型                 | 说明                                                   |
| ----------------- | -------------------- | ------------------------------------------------------ |
| `id`              | String               | 节点标识（如服务名，或 `"upstream"` / `"downstream"`） |
| `name`            | String               | 展示名                                                 |
| `treeServiceName` | String               | 服务树标准名                                           |
| `nonStandardName` | String               | Consul 原始名（被 K8s 名替换前的旧名）                 |
| `callType`        | String               | 调用类型：`RPC` / `Redis` / `SQL` 等                   |
| `ebpfTopo`        | boolean              | 是否为 eBPF 拓扑边                                     |
| `zones`           | Set\<String\>        | 部署区域（withZone=true 时填充）                       |
| `children`        | List\<TopologyNode\> | 子节点（递归树结构）                                   |

---

## 枚举值说明

### FocusOption（关注维度）

| 值                                      | 说明                           |
| --------------------------------------- | ------------------------------ |
| `direct_relations_each_direction_top10` | 默认：上下游各 Top 10 直接关系 |
| `all_direct_relations`                  | 所有直接上下游关系             |
| `all_relations_of_entry_list`           | 入口涉及的全部关系             |
| `all_down_stream`                       | 入口涉及的所有下游             |

### PreProcessEnum（调用类型过滤）

| 值                   | 说明                              |
| -------------------- | --------------------------------- |
| `RPC`                | 仅跨进程 RPC 调用（不含数据访问） |
| `RPC_DATA`           | RPC + 数据访问（Redis/SQL/MQ 等） |
| `RPC_DATA_IGNORE_OP` | RPC + 数据访问，但忽略操作名      |

### PerfTestInclude（压测流量策略）

| 值                | 说明                          |
| ----------------- | ----------------------------- |
| `UNION_PERF_TEST` | 默认：正常流量 + 压测流量合并 |
| `NO_PERF_TEST`    | 仅正常流量，过滤压测流量      |
| `ONLY_PERF_TEST`  | 仅压测流量                    |

### TopologyLevel（拓扑粒度，仅 ENTRY 模式）

| 值        | 说明                              |
| --------- | --------------------------------- |
| `app`     | 应用级：节点粒度为服务名          |
| `service` | 接口级：节点粒度细化到 RPC 方法名 |
