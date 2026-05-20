---
name: xray-ai-trace-analysis
description: "Langfuse AI 链路分析工具。查询 Langfuse observation 数据，对 AI/LLM 调用链路进行拓扑重建、性能瓶颈定位、Token 与成本分析、错误异常检测。支持单条 trace 分析、双 trace 对比分析、会话（session）多 trace 分析，以及灵活的通用 observation 查询。触发词:AI链路分析、Langfuse数据分析、Langfuse分析、LLM链路分析、langfuse trace、AI trace分析、LLM调用链、Agent链路、模型调用分析、会话分析、session分析 典型触发:\"分析一下这条AI链路\"、\"Langfuse trace分析\"、\"LLM调用链有问题\"、\"Agent链路排查\"、\"模型调用报错了帮我看看\"、\"分析一下这个session\"、\"看看这个会话的调用情况\" 不应触发:\"Java链路追踪\"、\"微服务调用链\"、\"RPC链路超时\"、\"分布式tracing\""
metadata:
  category: trace
  subcategory: ai-trace
  platform: xray
  trigger: project_id/trace_id/session_id/query/time_range
  input: [project_id, trace_id, session_id, query, from, to, trace_limit]
  output: [analysis_report, prompt_file, raw_data]
  impl: python-script
---

# Langfuse AI 链路分析

## 公共参数

| 参数 | 说明 | 必须 |
|------|------|------|
| `--project_id <id>` | Langfuse 项目 ID | 首次必须，后续自动读取 |
| `--save_project_id <id>` | 保存/更新 project_id（同时用于当次查询） | 可选 |
| `--from` / `--to` | 时间范围（ISO 8601 UTC） | 可选，各模式有不同默认值 |

- project_id 首次提供后自动持久化，后续无需重复输入。未提供且无保存配置时需主动询问用户
- **`--project_id` 和 `--save_project_id` 不要同时传**，二选一即可。首次使用 `--save_project_id`，后续两个都不传
- **时间转换**：用户描述的时间默认为北京时间（UTC+8），传参时必须转为 UTC。例如用户说"上午10点"即北京时间 10:00，应传 `--from 2026-04-13T02:00:00Z`

## 模式选择（三选一）

**判断口诀：用户想"查数据"、"分析链路"还是"分析会话"？**

| | 数据查询（`--query`） | 链路分析（`--trace_id`） | 会话分析（`--session_id`） |
|---|---|---|---|
| **目的** | 查数据/统计/排查/浏览列表 | 对某条 trace 做深度链路分析 | 对某个 session 的所有 trace 做整体分析 |
| **粒度** | Observation 级 | 单条 trace 全部节点 | 多条 trace + 会话级趋势 |
| **示例** | "最近有多少报错"、"按模型统计成本" | "分析一下这条链路" | "分析一下这个 session"、"看看这个会话的调用" |

- 没有 trace_id 时，先用 `--query` 帮用户发现值得分析的 trace（见下方 Trace 发现），再用 `--trace_id` 分析
- 用户提到"会话/session"且提供了 session_id → 使用 `--session_id` 模式

### Trace 发现

当用户想分析链路但没有 trace_id 时，依次执行以下探索性查询，汇总结果后让用户选择：

```bash
# 1. 最近报错的 observations
--query '{"filter":[{"column":"level","operator":"=","value":"ERROR"}],"order_by":[{"column":"start_time","order":"desc"}]}'

# 2. 耗时最长的链路（根 span）
--query '{"filter":[{"column":"parent_observation_id","operator":"is null"}],"order_by":[{"column":"date_diff(\'millisecond\', start_time, end_time)","order":"desc"}]}'

# 3. 模型 input/output 最长的 observations
--query '{"filter":[{"column":"type","operator":"=","value":"GENERATION"}],"order_by":[{"column":"length(input)","order":"desc"}]}'
```

从结果中提取不重复的 trace_id，附带关键上下文（name、level、耗时、cost）呈现给用户，用户选定后进入 `--trace_id` 深度分析。

---

## 模式 1：数据查询（--query）

灵活查询 observation 数据。先阅读 `<skill_dir>/references/api.md` 了解接口字段和操作符，然后构建 JSON。

```bash
python3 <skill_dir>/scripts/query_langfuse_trace.py --query '<JSON>'
```

**重要规则**：
- **不要在 JSON 中传 `select`**，默认返回所有列。仅在用户明确要求聚合统计（group_by）时才指定 `select`
- **不要在 JSON 中传 `limit`**，默认 10 条。仅在用户明确要求更多数据时才指定（最大 200）
- **不要在 JSON 中传 `from`/`to`**，默认最近 1 小时。仅在用户指定时间范围时才传
- **查询时间跨度不得超过 7 天**，超出会报错。如用户需要更长范围，应拆分为多次查询
- JSON 中只传用户明确要求的字段（`filter`、`order_by` 等），其余全部使用默认值

**耗时查询**：observations 表没有耗时字段，需用 ClickHouse 表达式 `date_diff('millisecond', start_time, end_time)` 计算。该表达式可用于 filter、order_by、select：

```bash
# 查询耗时超过 5 秒的 observations（筛选）
--query '{"filter":[{"column":"date_diff(\'millisecond\', start_time, end_time)","operator":">","value":5000}]}'

# 按耗时降序排列（排序）
--query '{"order_by":[{"column":"date_diff(\'millisecond\', start_time, end_time)","order":"desc"}]}'

# 耗时 > 3 秒 + 按耗时降序（筛选 + 排序组合）
--query '{"filter":[{"column":"date_diff(\'millisecond\', start_time, end_time)","operator":">","value":3000}],"order_by":[{"column":"date_diff(\'millisecond\', start_time, end_time)","order":"desc"}]}'

# 统计各 name 的平均耗时（聚合）
--query '{"select":["name","avg(date_diff(\'millisecond\', start_time, end_time)) as avg_latency_ms","count() as cnt"],"group_by":["name"],"order_by":[{"column":"avg_latency_ms","order":"desc"}]}'
```

> **注意**：不要使用 `end_time - start_time`，DateTime64 类型不支持直接减法，会报错。始终使用 `date_diff()`。

**示例**：

```bash
# 查询某用户的错误调用（只需传 filter）
--query '{"filter":[{"column":"user_id","operator":"=","value":"user_4"},{"column":"level","operator":"=","value":"ERROR"}]}'

# 按模型统计（需要聚合，此时才传 select + group_by）
--query '{"select":["provided_model_name","count() as cnt","sum(total_cost) as cost"],"filter":[{"column":"type","operator":"=","value":"GENERATION"}],"group_by":["provided_model_name"]}'

# 浏览最近的 trace 入口列表（仅当用户明确提到"链路入口/根节点/trace列表"时才加 parent_observation_id is null）
--query '{"filter":[{"column":"parent_observation_id","operator":"is null"}],"order_by":[{"column":"start_time","order":"desc"}]}'
```

> **注意**：`parent_observation_id IS NULL` 仅筛选链路入口（根 span）。只有用户明确要求查看"链路入口"、"根节点"、"trace 列表"等场景时才添加此条件，普通查询不要自动加。

**输出与展示**：
- stdout → JSON 统计摘要（type/level/model 分布、成本统计），渲染为易读格式给用户
- `<skill_dir>/tmp/observations.json` → 完整结果，格式如下：
  ```json
  {"query_time_ms": 96, "total_rows": 10, "time_range": {"from": "...", "to": "..."}, "data": [{observation}, ...]}
  ```
  每个 observation 包含 `id`、`trace_id`、`type`、`name`、`start_time`、`end_time`、`level`、`input`、`output`、`total_cost`、`metadata` 等字段
- **trace_id 必须完整展示，禁止截断**，方便用户复制后进入模式 2 进行深度分析
- 可根据结果引导用户进一步分析某条 trace

---

## 模式 2：链路分析（--trace_id）

对单条或两条 trace 进行完整链路分析。**默认最近 3 天**。

```bash
# 单 trace
python3 <skill_dir>/scripts/query_langfuse_trace.py --trace_id <id>

# 双 trace 对比
python3 <skill_dir>/scripts/query_langfuse_trace.py --trace_id <id_a> --trace_id_b <id_b>
```

**输出文件**（保存在 `<skill_dir>/tmp/`）：
| 文件 | 用途 |
|------|------|
| `langfuse_trace_prompt.txt` | 关键字段 + 分析提示词，直接读取进行分析 |
| `langfuse_trace.json` | 完整原始数据（含 input/output），按需通过 id 查找详情 |

`langfuse_trace.json` 格式（单 trace）：
```json
{"trace_id": "...", "total_observations": 8, "query_time_ms": 137, "observations": [{observation}, ...]}
```
双 trace 对比时为数组 `[{trace_a}, {trace_b}]`。通过 `observations[].id` 定位具体节点查看 input/output。

**stdout**：`SUCCESS` / `EMPTY` / `ERROR`

### 分析流程

1. 读取 `<skill_dir>/tmp/langfuse_trace_prompt.txt`，按 6 个维度分析：
   - 调用链拓扑（树状图）→ 性能瓶颈（TOP N / TTFT）→ Token 与成本 → 错误异常 → 模型使用 → 优化建议
2. 需查看 input/output 详情时从 `<skill_dir>/tmp/langfuse_trace.json` 按 id 查找

### 报告格式

**单 trace**：概览 → 调用链拓扑 → 性能分析 → Token与成本 → 异常分析 → 优化建议

**双 trace 对比**：概览对比 → 拓扑差异 → 性能差异 → 成本差异 → 模型差异 → 异常差异 → 结论与建议

---

## 模式 3：会话分析（--session_id）

对某个 session 下的所有 trace 进行整体分析。**默认最近 1 天，最多 20 条 trace**。

> **OpenClaw 环境提示**：当本 skill 运行在 OpenClaw 或基于 OpenClaw 开发的 Agent 产品（如 Lobi）中时，可直接获取当前会话的 session_id 作为 `--session_id` 参数，无需向用户索要。获取步骤：
> 1. 调用 `session_status` 工具，从返回结果中获取当前会话的 `sessionKey`
> 2. 调用 `sessions_list` 工具，通过 `agentKey` 查找对应的 `session_id`
> 3. 将获取到的 `session_id` 作为 `--session_id` 参数传入本脚本
>
> 当用户说"获取当前会话 trace 数据"、"分析当前会话"等时，按上述步骤自动获取 session_id 并执行查询。

```bash
# 基本用法
python3 <skill_dir>/scripts/query_langfuse_trace.py --session_id <session_id>

# 自定义 trace 数量上限
python3 <skill_dir>/scripts/query_langfuse_trace.py --session_id <session_id> --trace_limit 10

# 指定时间范围
python3 <skill_dir>/scripts/query_langfuse_trace.py --session_id <session_id> --from 2026-04-15T00:00:00Z --to 2026-04-16T00:00:00Z
```

**执行流程**（脚本自动完成，无需手动操作）：
1. 通过 `session_id` + `parent_observation_id IS NULL` 查询该会话的所有链路入口（根 span），获取 trace_id 列表及根 span 概要信息
2. 使用 `trace_id IN [...]` 一次性批量查询所有 observations（最多 2000 条）
3. 按 trace_id 分组，提取关键字段，计算 session 级和 trace 级摘要
4. 生成分析数据文件

**输出文件**（保存在 `<skill_dir>/tmp/`）：
| 文件 | 用途 |
|------|------|
| `langfuse_session_prompt.txt` | 会话概览 + Trace 时间线 + 各 trace 关键数据 + 分析提示词 |
| `langfuse_session.json` | 完整原始数据（含 input/output），按 trace 分组 |

`langfuse_session.json` 格式：
```json
{
  "session_id": "...",
  "trace_count": 5,
  "total_observations": 120,
  "query_time_ms": 250,
  "time_range": {"from": "...", "to": "..."},
  "traces": [
    {"trace_id": "...", "total_observations": 24, "observations": [...]},
    ...
  ]
}
```

**stdout**：`SUCCESS` / `EMPTY` / `ERROR`

### 分析流程

1. 读取 `<skill_dir>/tmp/langfuse_session_prompt.txt`，按以下维度分析：

**会话级分析**：
- **会话流程**：按时间线梳理用户的交互过程，每条 trace 做了什么、间隔多久
- **性能趋势**：各 trace 的耗时变化，是否逐渐变慢/波动异常
- **成本趋势**：各 trace 的成本分布和累计成本
- **错误分析**：哪些 trace 有错误，错误是否有聚集趋势
- **模型使用**：各 trace 使用的模型是否一致

**单 trace 分析**（对异常 trace 重点展开）：
- 调用链拓扑 → 性能瓶颈 → 错误根因

2. 需查看 input/output 详情时从 `<skill_dir>/tmp/langfuse_session.json` 按 trace_id + id 查找

### 报告格式

Session 概览（基本信息、Trace 时间线表格）→ 会话流程分析 → 性能趋势 → 成本分析 → 错误分析 → 异常 trace 深入分析 → 综合建议
