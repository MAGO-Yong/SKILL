---
name: xray-log-query
description:
  '查询小红书内部 Xray 日志平台的多类日志，支持通用业务日志（application）、百川 Flink
  作业日志（flink）、Larc
  训练任务日志（larc）、云原生事件日志（event）、云原生审计日志（audit）、接入层网关日志（rgw）、业务网关日志（edith）、客户端点位日志（pv）、客户端流量日志（measurement）。支持按服务名、TraceId、关键词等条件查询日志详情（/logs）和日志数量分布（/charts）。适用于以下场景：上下文中包含
  traceId、异常相关的信息，排查线上服务异常、根据 xrayTraceId
  追踪请求链路、统计某时间段内的日志数量趋势、查询某用户或某 Pod 的相关日志、查询 Flink
  作业或训练任务日志、查询 k8s
  事件或审计记录、查询网关接入层流量日志、查询客户端埋点/点位数据、查询客户端流量指标数据。当用户说"帮我查日志"、"查一下
  xxx 服务的错误"、"这个 traceId 的日志是什么"、"查一下 flink
  作业日志"、"查云原生事件"、"查审计日志"、"查业务网关日志"、"查 karen-gateway
  日志"、"最近一小时有多少 error"、"查一下某个埋点/点位数据"、"查一下某个 measurement 的数据"、"查
  APM 数据"、"查前端监控数据"时触发本 skill。'
version: 2.0.0
metadata:
  category: log
  subcategory: application-log
  platform: xray
  trigger: service_name/traceId/keyword/time_range
  input: [query, st, et, page, pageSize]
  output: [log_list, log_count, log_clusters]
  impl: xray-cli
---

# Xray 日志查询

> 本 skill 通过 **xray-cli** 命令行工具查询日志（不再直接调 HTTP API）。
>
> - **依赖**：`xray-cli >= 0.0.22`（提供多表 / `log cluster` / `--search-trace-app` / 前置校验）
> - **`{SKILL_DIR}`**：本 skill 所在目录的绝对路径；调用 Python 助手脚本时必须用绝对路径

## 前置检查：xray-cli 是否可用

执行任何命令前先确认 `xray-cli` 已安装并登录。若 `xray-cli --version` 报
`command not found`，按以下三步引导用户：

1. **安装**

   ```bash
   npm install -g --registry http://npm.devops.xiaohongshu.com:7001/ @xray/xray-cli && xray-cli --version
   ```

2. **后台登录**（引导用户在浏览器完成登录；OAuth 浏览器跳转通常需要 10s 以上）

   ```bash
   nohup xray-cli auth login > /tmp/xray-login.log 2>&1 &
   echo "PID: $!"
   # 轮询等待登录完成（最长约 60s），用户需在浏览器中确认
   for i in {1..30}; do
     sleep 2
     grep -qE "登录成功|success|Logged in" /tmp/xray-login.log && break
   done
   cat /tmp/xray-login.log
   ```

3. **查看用法**

   ```bash
   xray-cli --help
   ```

NEVER 在未确认 xray-cli 可用的情况下直接执行后续命令——失败时回到上面三步重新检查安装与登录状态。

---

## 概述

调用 `xray-cli log {query|chart|cluster}` 查询小红书多类日志。CLI 已经内置：

- 9 张日志表的目标表识别和必填字段校验
- 时间跨度 / pageSize / xrayTraceId 格式 / `| SELECT` 注入等前置参数校验
- beta 环境表合法性（仅 application）
- `--search-trace-app` 跨服务追踪关联

skill 在 CLI 之上保留两个能力：

| 助手脚本 | 用途 |
| -------- | ---- |
| `scripts/nl_to_xql.py` | 自然语言 → XQL 查询参数（query / st / et / search_trace_app）；规则模式 + 可选 LLM 模式 |
| `scripts/to_timestamp.py` | 相对时间 / 字符串时间 → Unix 秒，用于喂 CLI 的 `--st` / `--et` |

## 支持环境

| 环境           | 切换方式      | 支持表              |
| -------------- | ------------- | ------------------- |
| `prod`（默认） | 不传 `--env`  | 所有日志表          |
| `beta`         | `--env beta`  | 仅 `application` 表 |

beta 环境查询非 application 表时，CLI 会立即报错并提示切到 prod。

## 支持日志表（`xray-cli log query --table <name>`）

| 表名                   | 说明                                        | 必填字段（query 中至少含其一） |
| ---------------------- | ------------------------------------------- | ---------------------------- |
| `application`          | 通用业务日志（默认）                        | `subApplication` / `xrayTraceId` / `_pod_name_` / `traceId` / `ID` / `catMsgId` / `catRootId` / `userId` / `ext.uid` |
| `rgw`                  | 接入层网关日志（nginx）                     | （无） |
| `flink`                | 百川 Flink 作业日志                         | `release` |
| `larc`                 | Larc 训练任务日志                           | `subApplication` |
| `event`                | 云原生事件日志（k8s events）                | `cluster` |
| `audit`                | 云原生审计日志（k8s audit）                 | `cluster` |
| `edith`                | 业务网关日志（karen-gateway 系列）          | `subApplication` |
| `pv`                   | 客户端点位日志（埋点 / APM 点位）           | `context_artifactName` |
| `measurement`          | 客户端流量日志（APM 流量指标）              | `context_artifactName` |
| `apm_client_new`       | APM 客户端日志（生产）                      | `context_artifactName` |
| `apm_client_new_test`  | APM 客户端日志（测试）                      | `context_artifactName` |

每张表的常用字段、取值示例（地域代码、Lucene 写法、`request_time` 单位等）请用 `xray-cli docs log` 一键拉取，**不要在 skill 里再维护一份**——单一信息源在 CLI。

## 与 xray-single-trace-analysis 的职责区分

**本 skill** 和 **xray-single-trace-analysis** 都支持以 Trace ID 为输入，但职责不同：

| 对比维度 | xray-log-query（本 skill）                        | xray-single-trace-analysis                     |
| -------- | ------------------------------------------------- | ---------------------------------------------- |
| 数据类型 | **日志数据**：应用输出的文本日志（application 表）| **链路数据**：Span 调用链、耗时分布、异常 Span |
| 核心能力 | 搜索/过滤日志内容、日志聚类、趋势统计             | 分析 Span 拓扑、定位慢/异常节点、根因分析      |
| 典型问题 | "这个 traceId 对应的日志是什么？"                 | "这条链路为什么慢？"                           |

**意图判断规则**（用户提供 Trace ID 时）：

- 用户想查看**该 trace 对应的应用日志内容、日志文本** → 本 skill 处理
- 用户想了解**调用链路结构、Span 耗时、哪个节点异常** → 转交 `xray-single-trace-analysis`

## 工作流程

### Step 1：判断查询环境与目标表

| 用户描述特征                                 | 处理                                     |
| -------------------------------------------- | ---------------------------------------- |
| 明确提到"beta 环境"、"测试环境"、"beta 日志" | 命令加 `--env beta`                      |
| 明确提到"生产环境"、"线上"、"prod"           | 命令加 `--env prod`（或省略）            |
| 未提及环境                                   | 默认 `prod`                              |

**目标表判断**（用户描述特征 → `--table`）：

| 用户描述                                                                              | `--table`     |
| ------------------------------------------------------------------------------------- | ------------- |
| `karen-gateway` / 业务网关 / edith                                                    | `edith`       |
| `rgw` / `nginx` / `http_host` / `request_uri` / `response_status` / 域名 / 接入层     | `rgw`         |
| `flink` / `release` / `jobmanager` / `taskmanager` / 百川任务 / Flink 作业            | `flink`       |
| `larc` / 训练任务 / 算法训练                                                          | `larc`        |
| `event` / Kubernetes 事件 / k8s event / Pod 事件 / `reason` / `kind`                  | `event`       |
| `audit` / 审计日志 / k8s 审计 / `verb` / `user.username` / `requestURI`               | `audit`       |
| `level` / `msg` / `subApplication` / 异常堆栈 / traceId（非网关场景）                 | `application` |
| `pv` / 点位 / 埋点 / 客户端点位 / APM 点位 / 前端点位                                 | `pv`                  |
| `measurement` / `measurement_data` / 客户端流量 / APM 流量 / 前端流量指标             | `measurement`         |
| `apm client` / APM 客户端日志 / `apm_client_new`                                      | `apm_client_new`      |
| `apm client 测试表` / APM 客户端测试日志 / `apm_client_new_test`                      | `apm_client_new_test` |
| 提到 APM / 客户端监控 / 前端监控但**无法明确对应上述四张表之一**                      | **必须询问用户**，列出四张表供选择（见下方提示模板） |
| 无法明确判断时                                                                        | **必须询问用户**，NEVER 默认 `application` |

**四张客户端表的选择提示模板**（当用户意图模糊时，原文输出以下内容）：

> 请问您要查哪张客户端日志表？
>
> - `pv` — 客户端点位日志（埋点 / APM 点位，含 `measurement_name` 等点位字段）
> - `measurement` — 客户端流量日志（APM 流量指标，含 `measurement_data` 等聚合字段）
> - `apm_client_new` — APM 客户端日志（生产，含 `context_artifactName` 等客户端上下文字段）
> - `apm_client_new_test` — APM 客户端日志（测试环境验证用）

不传 `--table` 时 CLI 默认查 `application`；传错的表名 CLI 会立即报错并列出所有支持的表。

### Step 2：构造 query 与时间范围

#### 2A：自然语言 → XQL（推荐入口）

```bash
python3 {SKILL_DIR}/scripts/nl_to_xql.py \
  --text "查一下 my-service 最近 1 小时的 error 日志" \
  --table application
```

输出 JSON：

```json
{
  "query": "subApplication:my-service AND level:error",
  "st": 1778208591,
  "et": 1778212191,
  "search_trace_app": false,
  "mode": "rule",
  "confidence": "high",
  "explanation": "..."
}
```

字段含义：

- `query` → 直接传给 `xray-cli ... --query`
- `st` / `et` → 直接传给 `xray-cli ... --st` / `--et`（Unix 秒）
- `search_trace_app=true` → 命令加 `--search-trace-app`
- `confidence=low` → stderr 有警告，建议人工确认或加 `--llm-api-key` 启用 LLM

启用 LLM 模式（更准确，可选）：

```bash
python3 {SKILL_DIR}/scripts/nl_to_xql.py \
  --text "..." --table application \
  --llm-api-key $LLM_API_KEY
```

#### 2B：直接构造（已有具体 query）

构造规则参考 [Step 1 表格](#step-1判断查询环境与目标表) + `xray-cli docs log` 中"各表字段速查"。

#### 2C：时间字符串 → Unix 秒（如需）

```bash
# 区间字符串
python3 {SKILL_DIR}/scripts/to_timestamp.py --range "2024-03-25 14:00:00 - 2024-03-25 15:10:10"

# 相对时间
python3 {SKILL_DIR}/scripts/to_timestamp.py --range "now-1h - now"

# 起止分别指定
python3 {SKILL_DIR}/scripts/to_timestamp.py --start "2024-03-25 14:00" --end "2024-03-25 15:00"
```

输出为秒级时间戳，直接作为 `--st` / `--et`。

### Step 3：调用 xray-cli

| 目的                       | 命令                                               |
| -------------------------- | -------------------------------------------------- |
| 数量分布 / 直方图（预热）  | `xray-cli log chart --query "..." --st X --et Y --table T --output-format json` |
| 日志详情                   | `xray-cli log query --query "..." --st X --et Y --table T --output-format json` |
| 内容模板聚类（仅 application） | `xray-cli log cluster --query "..." --st X --et Y --output-format json` |

#### 通用 flag 速查

| Flag                  | 说明                                                       |
| --------------------- | ---------------------------------------------------------- |
| `--env prod\|beta`    | 环境（默认 prod）                                          |
| `--table <name>`      | 9 张表之一（默认 application）                             |
| `--service <svc>`     | 等价于 `--query "subApplication:<svc>"`，自动 AND 合并 `--query`；服务树校验生效（拼错名时 CLI 给出建议） |
| `--query "<XQL>"`     | Lucene/XQL 过滤条件                                        |
| `--st <unix-sec>`     | 起始时间（默认 15 分钟前）                                 |
| `--et <unix-sec>`     | 结束时间（默认现在）                                       |
| `--page <n>`          | 页码（仅 query，默认 1）                                   |
| `--page-size <n>`     | 每页条数（仅 query，默认 100，最大 10000）                 |
| `--order asc\|desc`   | 排序（仅 query，默认 desc）                                |
| `--search-trace-app`  | 仅 query；按 traceId 查时让服务端自动关联涉及的服务        |
| `--compare-st <unix>` / `--compare-et <unix>` | 仅 cluster；启用对比窗口（diffType: 0=新增 / 1=增加 / 2=不变 / 3=减少） |
| `--output-format json`| **解析输出时必加**；省略默认 text                          |

#### 推荐顺序

1. **先 chart**（预热缓存让 query 更快）
2. **再 query**（拿到具体日志）
3. **可选 cluster**（仅在用户明确要求"聚类 / 模式分析 / cluster / pattern"，或"对比两个时段日志模式"时调用；rgw / flink / larc / event / audit / edith / pv / measurement 不支持聚类，CLI 会拒绝）

### Step 4：解读结果

CLI `--output-format json` 输出与 HTTP API 完全一致，逐字段处理即可：

#### chart 结果

- `data.count` 总日志数
- `data.histograms[].{from,to,count,details}`（`details` 按 level 分色）

#### query 结果

- `data.logs[]` 关注：`_time_second_` / `level` / `msg` / `subApplication` / `xrayTraceId` / `_pod_name_`
- `data.cost`（毫秒）/ `data.where`（实际 WHERE 条件）
- `data.count == 0`：告知用户未找到日志，建议放宽时间范围或调整 query

特殊表的字段重点：

- **rgw**：`http_host` / `request_uri` / `request_method` / `response_status` / `request_time`（**秒**，浮点数）/ `clientIP` / `x-xray-traceid`；`upstream_status` / `upstream_response_time` 是数组
- **pv**：`context_artifactName` / `measurement_name`（核心区分字段）/ `page_instance` / `context_platform` / `context_userId`（24 位十六进制） / `context_appVersion` / `dtm`
- **measurement**：同 pv，但有 `measurement_data`（**JSON 对象**，包含 `step` / `result` / `strategy_name` 等具体字段，需结合 `measurement_name` 解读）

#### cluster 结果

- 有数据（`data.templates` 非空）：按 `count` 降序，重点标 top 3~5；模板中 `[*]` 是变量占位符
- 无数据：告知用户聚类未训练或时间范围内日志极少
- 对比模式（传了 `--compare-st/--compare-et`）：解读 `diffType`（0=新增 / 1=增加 / 2=不变 / 3=减少）和 `diffNum` / `diffRate`

#### 错误处理

CLI 在请求前已经做了多数校验，常见 API 错误：

- `没有对应的访问权限`：提示用户申请权限，响应里通常含申请链接
- `查询超出限制`：建议缩小时间范围或加更多过滤
- `必须含有 subApplication`：CLI 已会本地拦截，若仍触发说明 query 字段名不在 CLI 必填字段表中——检查是否表选错

### Step 5：分页（如需）

递增 `--page` 直到 `data.count < pageSize` 表示到末页。

## 快速示例

### 查询某服务最近 1 小时的错误日志（自然语言入口）

```bash
# 1) 自然语言 → XQL
PARSE=$(python3 {SKILL_DIR}/scripts/nl_to_xql.py \
  --text "查一下 my-service 最近 1 小时的 error 日志" \
  --table application)
QUERY=$(echo "$PARSE" | jq -r .query)
ST=$(echo "$PARSE" | jq .st)
ET=$(echo "$PARSE" | jq .et)

# 2) 先 chart 预热缓存
xray-cli log chart \
  --query "$QUERY" --st $ST --et $ET \
  --table application --output-format json

# 3) 再拿日志详情
xray-cli log query \
  --query "$QUERY" --st $ST --et $ET \
  --table application --order desc --page-size 20 \
  --output-format json
```

### 查询某服务最近 1 小时的错误日志（直接构造）

```bash
xray-cli log chart --service my-svc --query "level:error" \
  --st 1700000000 --et 1700003600 --output-format json

xray-cli log query --service my-svc --query "level:error" \
  --st 1700000000 --et 1700003600 \
  --order desc --page-size 20 --output-format json
```

### 按 TraceId 查询链路日志（自动关联服务）

```bash
xray-cli log query \
  --query "xrayTraceId:cec509f5a460691f6435f8f3bb692f8b" \
  --search-trace-app --order asc --page-size 200 \
  --output-format json
```

> traceId 查询时间范围可宽松（如前后各 5 分钟），CLI/服务端会自动按 traceId 解码精确时间压缩。

### 聚类对比分析（仅当用户明确要求聚类）

```bash
xray-cli log cluster --service my-svc \
  --st 1700003600 --et 1700007200 \
  --compare-st 1699917200 --compare-et 1699920800 \
  --output-format json
```

### 查询 rgw 网关 5xx 错误

```bash
xray-cli log query --table rgw \
  --query 'http_host:edith.xiaohongshu.com AND response_status:500' \
  --output-format json
```

### 查询 rgw 慢请求（>1s）

```bash
xray-cli log query --table rgw \
  --query 'http_host:edith.xiaohongshu.com AND request_time:>1' \
  --order desc --page-size 50 --output-format json
```

### 查询 k8s 事件（event 表）

```bash
xray-cli log query --table event \
  --query 'cluster:qcsh5-xray AND level:Warning AND kind:Pod' \
  --output-format json
```

### 查询 Flink 作业日志

```bash
xray-cli log query --table flink \
  --query 'release:baichuan-509-55614 AND component:jobmanager' \
  --output-format json
```

### 查询客户端点位（pv 表）

```bash
xray-cli log query --table pv \
  --query 'context_artifactName:xhs_apm AND measurement_name:page_view' \
  --output-format json
```

## 故障排查

| 现象                                              | 处理                                                                            |
| ------------------------------------------------- | ------------------------------------------------------------------------------- |
| `command not found: xray-cli`                     | 回到「前置检查」一节按三步走安装并登录                                          |
| `unknown command "cluster"` 或缺 `--search-trace-app` | xray-cli 版本过低；让用户重跑安装命令（同前置检查）升级到 v0.0.22+              |
| 鉴权错误（401 / `auth login required`）          | 走「前置检查」第 2 步的后台登录脚本，等待用户在浏览器完成确认                  |
| `beta env only supports the application table`  | 用户在 beta 环境查非 application 表；询问是否切到 prod                           |
| `query must contain at least one of: ...`        | query 缺必填字段；按表字段速查补 `subApplication` / `release` / `cluster` 等     |
| `time range ... exceeds the 5-day limit`        | 缩小 `--st/--et` 跨度                                                            |
| `xrayTraceId ... is not a 32-char hex string`   | 用户给的 traceId 格式有误，回去确认                                              |
