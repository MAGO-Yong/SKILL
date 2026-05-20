# Observation Query API

**接口**: `POST /api/public/openapi/{projectId}/observation/query`
**认证**: `Authorization: Bearer <ADMIN_API_KEY>`

## 请求体

```json
{
  "from": "ISO 8601",        // 必须，起始时间
  "to": "ISO 8601",          // 必须，结束时间
  "select": [...],           // 可选，不传则 SELECT *
  "filter": [...],           // 可选，WHERE 条件
  "group_by": [...],         // 可选
  "having": [...],           // 可选，需配合 group_by，schema 同 filter
  "order_by": [{"column": "...", "order": "asc|desc"}],
  "limit": 10,               // 可选，1~200，默认 10
  "offset": 0                // 可选
}
```

## 可用字段

### 基础字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | String | Observation ID |
| `trace_id` | String | 所属 Trace ID |
| `project_id` | String | 项目 ID（自动过滤） |
| `type` | String | `GENERATION` / `SPAN` / `EVENT` |
| `name` | String | 节点名称 |
| `parent_observation_id` | String | 父节点 ID（根节点为 NULL） |
| `start_time` / `end_time` | DateTime | 起止时间 |
| `completion_start_time` | DateTime | 首 token 时间 |
| `level` | String | `DEFAULT` / `DEBUG` / `WARNING` / `ERROR` |
| `status_message` | String | 状态/错误消息 |
| `input` / `output` | String | 输入/输出（JSON 字符串） |
| `provided_model_name` | String | 模型名称 |
| `total_cost` | Float64 | 总成本 |
| `environment` | String | 环境标识 |
| `user_id` / `session_id` | String | 用户/会话 ID |
| `prompt_name` / `prompt_version` | String/Int | Prompt 信息 |
| `version` / `source_name` | String | 版本/来源 |
| `internal_model_id` / `prompt_id` | String | 内部 ID |
| `created_at` / `updated_at` / `event_ts` | DateTime | 时间戳 |
| `is_deleted` | Int | 删除标记 |

### Map 字段（通过 `column['key']` 语法访问）

| 字段 | 类型 | 常见 key | 用途 |
|------|------|----------|------|
| `metadata` | Map(String, String) | 用户自定义 | `metadata['env']`, `metadata['user_type']` |
| `usage_details` | Map(String, UInt64) | `input`, `output`, `total` | Token 用量 |
| `provided_usage_details` | Map(String, UInt64) | 同上 | 用户上报的 Token 用量 |
| `cost_details` | Map(String, Float64) | `input`, `output` | 成本明细 |
| `provided_cost_details` | Map(String, Float64) | 同上 | 用户上报的成本 |
| `model_parameters` | Map(String, String) | `temperature`, `max_tokens`, `top_p` | 模型参数 |

Map 字段可用于 select、filter、group_by：

```json
"select": ["metadata['env']", "usage_details['input'] as input_tokens"]
"filter": [{"column": "metadata['env']", "operator": "=", "value": "production"}]
"group_by": ["metadata['env']"]
```

## filter 操作符

| 操作符 | value 类型 | 操作符 | value 类型 |
|--------|------------|--------|------------|
| `=` / `!=` | string/number/boolean | `in` / `not in` | Array |
| `>` / `<` / `>=` / `<=` | string/number | `like` / `not like` | string（`%`通配） |
| `is null` / `is not null` | 无需 value | | |

## select 表达式

```json
["name", "trace_id"]                                  // 直接列名
["count() as cnt", "sum(total_cost) as cost"]         // 聚合（需 group_by）
["toDate(start_time) as date"]                        // ClickHouse 函数
["usage_details['input'] as input_tokens"]            // Map 下标
```

## 响应格式

```json
{
  "data": [{ "id": "...", "trace_id": "...", ... }],
  "meta": { "total_rows": 42, "query_time_ms": 120 }
}
```

## 常用查询示例

```json
// 查询某 trace 的所有 observation
{"filter": [{"column": "trace_id", "operator": "=", "value": "trace-xxx"}],
 "order_by": [{"column": "start_time", "order": "asc"}]}

// 查询错误的 GENERATION 节点
{"filter": [{"column": "type", "operator": "=", "value": "GENERATION"},
            {"column": "level", "operator": "=", "value": "ERROR"}],
 "select": ["trace_id", "name", "start_time", "status_message", "provided_model_name"]}

// 按模型统计调用次数和成本
{"select": ["provided_model_name", "count() as cnt", "sum(total_cost) as cost"],
 "filter": [{"column": "type", "operator": "=", "value": "GENERATION"}],
 "group_by": ["provided_model_name"],
 "order_by": [{"column": "cost", "order": "desc"}]}

// 按 metadata 过滤
{"filter": [{"column": "metadata['env']", "operator": "=", "value": "production"}]}

// 高成本调用
{"filter": [{"column": "total_cost", "operator": ">", "value": 0.05}],
 "select": ["trace_id", "name", "provided_model_name", "total_cost"],
 "order_by": [{"column": "total_cost", "order": "desc"}]}

// 按 input 内容模糊搜索
{"filter": [{"column": "input", "operator": "like", "value": "%关键词%"}]}
```

## 注意事项

- `from`/`to` 必填，时间过滤基于 `start_time` 字段
- `project_id` 通过 URL 路径传入，自动加入 WHERE
- Map 字段的 key 是动态的，不确定时先查询几条数据查看
- `limit` 最大 200，默认 10
