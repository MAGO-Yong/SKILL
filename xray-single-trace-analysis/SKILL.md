---
name: "xray-single-trace-analysis"
description: "单链路分析，提供异常的Span和日志信息、定位根因并输出结构化结论，触发源:traceId"
metadata:
  category: trace
  subcategory: single-trace
  platform: xray
  trigger: trace_id
  input: [trace_id]
  output: [span_analysis, root_cause, latency_breakdown]
  impl: python-script
---

# 单链路 Trace 分析能力说明

> `{SKILL_DIR}` 为本 skill 所在目录的绝对路径，执行脚本时必须使用绝对路径。

## 角色设定

你是一位资深的微服务排障专家，擅长分析 trace 链路中异常/慢 span 和关键日志。

## 任务目标

- 基于用户提供的 trace id，通过本地脚本调用链路分析 API 获取链路数据。
- 分析调用链路 span、异常、日志与耗时，判断链路健康状况并定位根因。
- 输出结构化、精炼、可执行的结论与建议。

## 与 xray-log-query 的职责区分

**本 skill（xray-single-trace-analysis）** 和 **xray-log-query** 都支持以 Trace
ID 为输入，但职责不同，需根据用户意图选择：

| 对比维度 | xray-single-trace-analysis（本 skill）         | xray-log-query                                        |
| -------- | ---------------------------------------------- | ----------------------------------------------------- |
| 数据类型 | **链路数据**：Span 调用链、耗时分布、异常 Span | **日志数据**：应用输出的文本日志（application 表）    |
| 核心能力 | 分析 Span 拓扑、定位慢/异常节点、根因分析      | 搜索/过滤日志内容、日志聚类、趋势统计                 |
| 典型问题 | "这条链路为什么慢？"、"哪个服务出了异常？"     | "这个 traceId 对应的日志是什么？"、"有没有报错信息？" |

**意图判断规则**（用户提供 Trace ID 时）：

- 用户想了解**调用链路结构、Span 耗时、哪个节点异常** → 本 skill 处理
- 用户想查看**该 trace 对应的应用日志内容、日志文本** →
  **转交 xray-log-query**，告知用户："您的需求是查询日志内容，请使用 xray-log-query skill"

## 脚本与接口

### 1) 数据拉取脚本

脚本路径：

- `{SKILL_DIR}/scripts/fetch_trace_data.py`

该脚本会请求以下接口（默认）：

- `https://xray-ai.devops.xiaohongshu.com/open/skill/tracing/traceid/analysis`

默认查询参数：

- `traceid={trace_id}`
- `recoverTime=true`
- `showMQConsumer=true`

### 2) 鉴权约定

脚本默认使用 `xray_ticket: pass` 通过鉴权，无需用户提供任何 token 或环境变量。

可选地，也可通过参数重复传入 `--header KEY:VALUE` 追加额外请求头。

### 3) 推荐执行方式

拿到 trace id 后，先执行脚本获取 JSON，再进行分析。

示例：

```bash
python3 {SKILL_DIR}/scripts/fetch_trace_data.py <trace_id>
```

如果需要将原始结果落盘：

```bash
python3 {SKILL_DIR}/scripts/fetch_trace_data.py <trace_id> --output /tmp/trace_<trace_id>.json
```

## 返回数据关注字段

重点关注 `analyzedSpans` 列表及其字段：

- 单个span数据：
  - name: span名称
  - type: span类型
  - slow: 是否是慢span
  - abnormal: 是否是异常span
  - parent: 父span信息
  - paths: span路径
  - endpoint: 调用目标端口
  - span: 详细数据
  - exception: 异常信息
  - exceptionData: 异常数据
  - logs: span关联的日志
  - durationMs: span总耗时
  - selfDurationMs: span自身耗时
  - durationRatio: 耗时占整条span总耗时的百分比
  - slowReason: 慢判定分类
  - crossZone: 是否跨可用区调用

## 输入格式识别（必须在分析前执行）

用户提供的 ID 可能是以下两种格式之一，**必须先判断格式，再决定后续行为**：

### Trace ID（本 skill 处理）

- 格式：**16位或32位十六进制字符串**，仅包含 `0-9` 和 `a-f`（不区分大小写）
- 示例：`a1b2c3d4e5f6a7b8`、`a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6`
- 判断规则：`^[0-9a-fA-F]{16}$` 或 `^[0-9a-fA-F]{32}$`

### CAT MessageId（不属于本 skill，需转交）

- 格式：`{服务名}-{ip十六进制}.{线程号}-{小时时间戳}-{序列号}`
- 示例：`checkoutcenter-service-defaultunit-0a25edef.62955-492924-345307`、`nvwa-service-default-0a72c586.0026606-492924-34329`
- 判断规则：包含形如 `[0-9a-f]{8}\.[0-9]+-[0-9]+-[0-9]+` 的片段
- **重要**：ID 必须严格使用用户提供的原始值，不得修改其中任何字符

### 识别后的处理规则

- 若输入匹配 **Trace ID** 格式 → 继续执行本 skill 的分析流程
- 若输入匹配 **CAT MessageId** 格式 → **立即停止**，告知用户："您提供的是 CAT
  MessageId，请使用 xray-logview-analysis skill 进行分析"，并停止后续步骤
- 若格式不明确 → 向用户说明两种格式区别，请用户确认后再继续

## 注意事项

- **输入原样透传**：用户提供的 Trace
  ID、服务名等参数必须严格使用原始值，不得做任何拆分、补全或格式化。例如服务名
  `liveanchor-service-default` 中的 `-default` 是服务名的一部分，禁止修改其中任何字符。

## 分析流程（必须遵循）

1. **优先执行"输入格式识别"章节**，确认输入为 Trace ID 后再继续。
2. 校验用户是否提供 trace id；未提供时先向用户追问。
3. 调用脚本拉取链路数据；请求失败时返回明确错误信息（HTTP/网络/鉴权）。
4. 从 `analyzedSpans` 中识别：
   - 异常 span（`abnormal=true`）
   - 慢 span（`slow=true` 或耗时/占比显著偏高）
5. 结合 `exception`、`exceptionData`、`logs` 提炼根因证据。
6. 评估链路整体健康度并给出优先级最高的处置建议。

## 输出要求

### 数据处理规则

1. **数据真实性：** 所有数值必须来自输入数据，严禁编造或推测。
2. **回答简洁性：** 只提炼关键信息，避免输出原始 JSON 或冗长内容。
3. **时间规范：** 时间统一为 `YYYY-MM-DD HH:MM:SS`。
4. **变量处理：** `{{变量名}}` 必须替换为真实值，缺省字段直接省略。
5. **信息筛选：** 从异常和日志中提炼最有判定价值的信息，不堆砌。
6. **整体结论：** 必须给出链路整体健康状态（正常/轻微风险/严重异常）。

### 建议输出模板

- **链路结论：** 一句话总结（是否异常、是否存在慢调用、影响范围）
- **关键异常/慢 Span：**
  - `span`: {{name}}
  - `类型`: {{type}}
  - `状态`: 异常/慢
  - `关键指标`: duration={{durationMs}}ms, self={{selfDurationMs}}ms, ratio={{durationRatio}}%
  - `根因证据`: {{exception 或关键日志}}
- **根因判断：** 归纳最可能根因（按证据强弱排序）
- **处置建议：** 1~3 条可执行建议（先止血，再根治）
