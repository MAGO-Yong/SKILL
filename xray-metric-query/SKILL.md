---
name: xray-metric-query
description:
  统一指标数据查询，支持四种查询模式：1)
  系统/中间件模板指标查询（CPU、内存、JVM、RPC、Redis、MySQL、MQ、HTTP、线程池、Sentinel 等）；2)
  PromQL(PQL) 自定义查询；3) Cat 指标查询（transaction/event/problem 的
  QPS、耗时、成功率等）；4) Cat 元数据查询（type/name 列表）。根据数据量智能返回原始数据或特征数据。当用户想要查询服务的系统指标、中间件指标、JVM
  信息、Cat 指标（transaction/event/problem）、或执行 PQL/PromQL 查询时使用此 skill。
---

# 统一指标数据查询 Metric Query

这个 skill 是统一的指标数据查询入口，支持系统指标、PQL、Cat 时序和 Cat 元数据查询，覆盖所有常见的指标查询场景。

## 工作流程

### Step 1: 判断查询模式

根据用户输入判断使用哪种查询模式，**按以下优先级**：

1. **pql 模式** — 用户提供了 PromQL / PQL 表达式 → `--mode pql`
2. **cat 模式** — 满足以下**任一**条件 → `--mode cat`
   - 用户明确提到 Cat / transaction / event / problem 关键词
   - 用户想按**接口维度**拆分查看（如「各接口的 QPS」「按接口看耗时」「哪个接口最慢」）
   - 用户指定了具体的接口名称（如「getUserInfo 的 tp99」）
   - 用户想按**机器/Pod 维度**或**机房维度**拆分看 Cat 类指标
   - 用户提到了业务自定义埋点的名称（非通用系统指标，如 `PromVmsClient`、`SendAlarm` 等）→ cat 模式，将该名称作为 `--type` 传入
3. **cat-meta 模式** — 用户想查询 Cat 可用元数据，或时序查询缺少准确的 `type` / `name` 且需要先发现候选值 → `--mode cat-meta`
   - 不传 `--type`：查询该 app/theme 下可用的 type 列表
   - 传 `--type`：查询该 type 下可用的 name 列表
   - 元数据结果可直接用于后续 `cat` 时序查询的 `--type` / `--names`
4. **system 模式**（默认） — 用户提到具体的指标名称（CPU、内存、JVM、RPC、Redis 等）且不涉及接口级拆分 →
   `--mode system`

> **歧义处理**：
>
> - 「RPC 耗时」「Redis QPS」等**整体指标**表述 → system 模式（查聚合值）
> - 「各接口的 RPC 耗时」「看看哪个接口 QPS 最高」等**涉及拆分/对比**的表述 → cat 模式 + group by
> - 简单理解：**想看整体** → system，**想拆开看** → cat + group by
>
> Don't 对模式判断过于自信：用户意图确实不明时，优先选 system 模式并说明，而不是猜一个 cat 模式参数组合去运行。NEVER 在同一次查询中同时对同一指标运行两种模式来"双保险"，这会产生混乱的输出。

---

### Step 2: 收集参数

**从用户问题中尽可能提取参数，只主动询问缺失的必需参数。**
好的同事不会为了确认每个细节而反复打扰对方——能从上下文推断的就推断，确实无法推断的才开口问。

> NEVER 自己猜测或伪造时间参数（`--start`/`--end`），时间范围直接影响数据结果。如果用户说"最近一小时"，以当前时间向前推算；如果完全没有时间信息，必须明确询问用户。

#### 公共参数

| 参数      | 必需   | 说明                                 |
| --------- | ------ | ------------------------------------ |
| `--start` | cat-meta 不需要，其他模式必需 | 开始时间，格式 `yyyy-MM-dd HH:mm:ss` |
| `--end`   | cat-meta 不需要，其他模式必需 | 结束时间，格式 `yyyy-MM-dd HH:mm:ss` |
| `--app`   | 视模式 | 服务名，system/cat 必填，pql 可选    |

#### system 模式参数

| 参数             | 必需 | 说明                                                                                                 |
| ---------------- | ---- | ---------------------------------------------------------------------------------------------------- |
| `--metric-names` | 是   | 指标名称，逗号分隔。参考「指标映射表」章节                                                           |
| `--view`         | 否   | 查询视角：`cluster`（默认，表示服务、集群视角）/ `zone`（机房、可用区） / `container`（单机、单pod） |
| `--group-bys`    | 否   | 分组维度，逗号分隔                                                                                   |

#### pql 模式参数

| 参数           | 必需 | 说明                                   |
| -------------- | ---- | -------------------------------------- |
| `--pql`        | 是   | PromQL 表达式                          |
| `--app`        | 否   | 辅助数据源解析，当无 datasource 时使用 |
| `--datasource` | 否   | VMS 数据源名称，优先级最高             |

> 数据源三级降级：`datasource` > `app` > PQL 中解析 metric name

#### cat 模式参数

| 参数          | 必需 | 说明                                                                                                 |
| ------------- | ---- | ---------------------------------------------------------------------------------------------------- |
| `--theme`     | 否   | 主题：`transaction`（默认）/ `event` / `problem`                                                     |
| `--metric`    | 否   | 单个指标：`qps`（默认）/ `avg` / `tp99` / `tp95` / `tp90` / `count` / `failPercent` / `successPercent` |
| `--metrics`   | 否   | 多个指标，逗号分隔。优先级高于 `--metric`，适合一次查询 `qps,count,failPercent,tp99` 等组合 |
| `--type`      | 否   | Cat 埋点类型，单选。常见通用值：`Call`（下游调用）、`Service`（服务端）、`Http`、`URL`。**业务方可自定义任意埋点类型**（如 `PromVmsClient`、`RedisClient` 等），用户提到具体埋点名称时直接作为 `--type` 值传入，不要强行映射到通用类型。 |
| `--types`     | 否   | Cat 类型，多选（逗号分隔），与 `--type` 互斥。默认 `Service,Http`                                    |
| `--names`     | 否   | 接口名称，逗号分隔。默认 `All`                                                                       |
| `--zones`     | 否   | 机房列表，逗号分隔。默认 `All`                                                                       |
| `--ips`       | 否   | IP 列表，逗号分隔。默认 `All`                                                                        |
| `--step`      | 否   | 步长（秒），默认 60                                                                                  |
| `--group-bys` | 否   | 分组维度，逗号分隔。可选值：`ip`（按机器/Pod）、`name`（按接口名）、`zone`（按机房/可用区）          |

#### cat-meta 模式参数

| 参数      | 必需 | 说明                                                                 |
| --------- | ---- | -------------------------------------------------------------------- |
| `--app`   | 是   | 服务名                                                               |
| `--theme` | 否   | 主题：`transaction`（默认）/ `event` / `problem`                     |
| `--type`  | 否   | 不传时查询 type 列表；传入具体 type 时查询该 type 下的 name 列表     |

---

### Step 3: 调用 API

```bash
# system 模式 — 查询模板指标
python {SKILL_DIR}/scripts/query.py --mode system \
  --app "creator-service-default" \
  --start "2025-05-30 10:00:00" --end "2025-05-30 11:00:00" \
  --metric-names "cpu.usage,mem.usage"

# pql 模式 — 执行 PromQL
python {SKILL_DIR}/scripts/query.py --mode pql \
  --start "2025-05-30 10:00:00" --end "2025-05-30 11:00:00" \
  --pql 'sum(rate(rpc_server_requests_total{app="creator-service-default"}[5m]))'

# cat 模式 — 查询 Cat 指标
python {SKILL_DIR}/scripts/query.py --mode cat \
  --app "creator-service-default" \
  --start "2025-05-30 10:00:00" --end "2025-05-30 11:00:00" \
  --theme transaction --metric qps --type Call

# cat 模式 — 一次查询多个 Cat 指标
python {SKILL_DIR}/scripts/query.py --mode cat \
  --app "creator-service-default" \
  --start "2025-05-30 10:00:00" --end "2025-05-30 11:00:00" \
  --theme transaction --metrics "qps,count,failPercent,tp99" --type Service

# cat-meta 模式 — 查询transaction的 type 列表
python {SKILL_DIR}/scripts/query.py --mode cat-meta \
  --app "riskhulk-sync-shield" --theme transaction

# cat-meta 模式 — 查询event某个 type 下可用 name 列表
python {SKILL_DIR}/scripts/query.py --mode cat-meta \
  --app "riskhulk-sync-shield" --theme event --type "Exception"
```

---

### Step 4: 灵活呈现结果

**根据用户问题灵活调整输出**：

- **「CPU 使用率是多少？」** → 只回答平均值和当前值
- **「CPU 趋势如何？」** → 描述趋势（上升/下降/平稳）和关键数据点
- **「系统全面检查」** → 展示多个指标的摘要信息
- **「transaction QPS 多少？」** → Cat 模式结果概要

**输出要点**：

- 当前值、平均值、最大值、最小值
- 趋势描述
- 异常点识别
- 根据问题决定详细程度

**结果诚实要求**：

- 脚本退出码非 0，或 API 返回错误 → 必须如实告知用户错误原因，NEVER 用部分数据或推测数据假装成功
- 数据为空（返回空数组/无数据点）→ 明确告知用户"该时段无数据"，而不是"数据正常"或沉默跳过
- 查询成功但数据异常（如全为 0）→ 如实展示，并提示用户可能是指标未上报或服务未启动
- Don't 只因为"拿到了一些数据"就声称查询成功——返回数据不完整时也要说明

**图表渲染**（查询成功且有数据时，先调用 `show-chart` tool 渲染图表，再输出文字分析）：

| 场景 | 图表类型 | data 映射 |
| ---- | -------- | --------- |
| 单指标时序（QPS、成功率、耗时趋势） | `line` | `{ legend: 指标名, values: [{value, formattedTime}] }` |
| group by name/zone/ip 的占比分布 | `pie` | `[{ name: 分组名, value: 聚合均值或总量 }]` |
| 多指标对比（P50/P99/P999 等） | `bar` | `[{ name: 指标名, data: [{label: 时间或分组, value}] }]` |

不画图的情况：数据为空、查询失败、用户只问单个数字（如"CPU 现在多少"）。

---

### Step 5: 异常检测与 samples 下钻（仅 cat 模式）

cat 模式查询并呈现结果后，分析时序数据判断是否存在异常。
不依赖固定阈值，基于数据的统计分布和上下文综合判断，典型异常形态：

- **突降/突升**：某时间窗口内数值相对前后明显偏离
- **持续劣化**：整体趋势单向恶化
- **毛刺**：单点值显著偏离整体均值

**若检测到异常**，执行以下步骤：

1. 定位异常最严重的时间窗口，精确到分钟级（通常 1~5 分钟）
2. 调用 samples 接口：
   - 时间范围：使用异常时间窗口，而非原始查询范围（避免返回大量无关数据）
   - 时间格式：`yyyy-MM-dd HH:mm:ss`，不要传时间戳
   - `--type`：与 cat 查询保持一致（若原查询是 `--types` 多选，取异常最严重的那个 type）
   - `--success false`：优先查失败样本；若是耗时异常（avg/tp99 等指标）则不传 `--success`

```bash
python {SKILL_DIR}/scripts/query.py --mode samples \
  --app "your-service" \
  --start "2025-05-30 10:03:00" --end "2025-05-30 10:05:00" \
  --type "Service" --success false
```

3. 从返回结果中提取 `messageId`（非空），取前 3 个
4. 依次调用 `xray-logview-analysis` skill，传入每个 `messageId` 进行链路分析
5. 汇总链路结论，与指标异常关联，给出综合根因判断

**若未检测到异常**：不触发下钻，正常结束。

---

## 指标映射表（system 模式）

使用 system 模式时，需要将用户的自然语言描述映射为 `--metric-names` 的值。

### 分组模板

当用户说「查看 XXX 类指标」时，自动展开为对应的指标列表：

**SYSTEM**（系统基础）:
`cpu.usage, mem.usage, mem.used, network.in.io, network.out.io, disk.write.io, disk.read.io`

**JVM**:
`jvm.young.gc.count, jvm.young.gc.duration, jvm.old.gc.count, jvm.old.gc.duration, jvm.eden.space.used, jvm.survivor.space.used, jvm.old.space.used, jvm.metaspace.used, jvm.live.threads`

**THREAD**（线程池）:
`executor.threads.usage, executor.threads.count.max, executor.queued.task.count, executor.execution.duration`

**RPC**:
`rpc.client.request.qps, rpc.client.request.success, rpc.client.request.duration.avg, rpc.server.request.qps, rpc.server.request.success, rpc.server.request.duration.avg`

**HTTP**:
`http.client.request.qps, http.client.request.success, http.client.request.duration.avg, http.server.request.qps, http.server.request.success, http.server.request.duration.avg`

**MYSQL**: `mysql.request.qps, mysql.request.success, mysql.request.duration.avg`

**REDIS**:
`redis.jedis.request.qps, redis.jedis.request.success, redis.jedis.request.duration.avg, redis.jedis.connection.wait`

**MQ**（RocketMQ）:
`rocketmq.producer.qps, rocketmq.producer.success, rocketmq.producer.duration.avg, rocketmq.consumer.qps, rocketmq.consumer.success, rocketmq.consumer.duration.avg`

**SENTINEL**: `sentinel.request.qps, sentinel.block.qps, sentinel.fail.qps`

**SCHEDULE**:
`xschedule.trigger.qps, xschedule.trigger.duration, xschedule.trigger.error, redschedule.task.processing.total`

---

### 完整指标列表

#### 1. 系统监控 (SYSTEM)

**CPU**:

- `cpu.usage` — CPU 使用率
- `cpu.cfs.periods.total` — 每秒执行的 CPU 时间周期数
- `cpu.cfs.throttled.periods.total` — 每分钟容器被限制的 CPU 时间周期数

**内存**:

- `mem.usage` — 内存使用率
- `mem.used` — 已使用内存
- `mem.total` — 总内存
- `mem.cache` — 内存中的 cache 用量
- `mem.swap` — 交换分区用量
- `mem.working.set` — 当前内存工作集使用量
- `mem.max.usage.bytes` — 最大内存使用量的记录
- `mem.failcnt` — 每分钟申请内存失败次数
- `mem.failures.total` — 每分钟累计内存申请错误次数
- `mem.mapped.file` — 内存映射文件使用内存量

**网络**:

- `network.in.io` — 网络入流量
- `network.out.io` — 网络出流量

**磁盘/IO**:

- `disk.write.io` — 磁盘写 I/O
- `disk.read.io` — 磁盘读 I/O
- `fs.write.seconds.total` — 每分钟 I/O 写操作花费的时间

**日志**:

- `logback.error.count` — 错误日志数量

#### 2. JVM

**GC**:

- `jvm.young.gc.count` — JVM Young GC 次数
- `jvm.young.gc.duration` — JVM Young GC 耗时
- `jvm.old.gc.count` — JVM Old GC 次数
- `jvm.old.gc.duration` — JVM Old GC 耗时

**内存区域**:

- `jvm.eden.space.used` — JVM Eden 区使用内存
- `jvm.survivor.space.used` — JVM Survivor 区使用内存
- `jvm.old.space.used` — JVM Old 区使用内存
- `jvm.metaspace.used` — JVM Metaspace 使用内存

**线程**:

- `jvm.live.threads` — JVM Live 线程总数

#### 3. 线程池 (THREAD)

- `executor.threads.usage` — 线程池利用率
- `executor.threads.count.max` — 线程池最大线程数
- `executor.queued.task.count` — 线程池排队数
- `executor.execution.duration` — 线程池任务处理耗时

#### 4. RPC

**客户端**:

- `rpc.client.request.success` — RPC 客户端请求成功率
- `rpc.client.request.qps` — RPC 客户端请求 QPS
- `rpc.client.request.duration.avg` — RPC 客户端请求平均耗时
- `rpc.client.request.duration.tp95` — RPC 客户端请求耗时 TP95
- `rpc.client.request.duration.tp99` — RPC 客户端请求耗时 TP99
- `rpc.client.request.duration.tp999` — RPC 客户端请求耗时 TP999

**服务端**:

- `rpc.server.request.success` — RPC 服务端请求成功率
- `rpc.server.request.qps` — RPC 服务端请求 QPS
- `rpc.server.request.duration.avg` — RPC 服务端请求平均耗时
- `rpc.server.request.duration.tp95` — RPC 服务端请求耗时 TP95
- `rpc.server.request.duration.tp99` — RPC 服务端请求耗时 TP99
- `rpc.server.request.duration.tp999` — RPC 服务端请求耗时 TP999

**C++ RPC**:

- `cpp.rpc.client.request.time.TP<999` — RPC 客户端耗时 TP<999
- `cpp.rpc.client.request.time.TP9999` — RPC 客户端耗时 TP9999
- `cpp.rpc.server.request.time.TP<999` — RPC 服务端耗时 TP<999
- `cpp.rpc.server.request.time.TP9999` — RPC 服务端耗时 TP9999

#### 5. HTTP

**客户端**:

- `http.client.request.qps` — HTTP 客户端请求 QPS
- `http.client.request.success` — HTTP 客户端请求成功率
- `http.client.request.duration.avg` — HTTP 客户端请求平均耗时
- `http.client.request.duration.tp95` — HTTP 客户端请求耗时 TP95
- `http.client.request.duration.tp99` — HTTP 客户端请求耗时 TP99

**服务端**:

- `http.server.request.success` — HTTP 服务端请求成功率
- `http.server.request.qps` — HTTP 服务端请求 QPS
- `http.server.request.duration.avg` — HTTP 服务端请求平均耗时
- `http.server.request.duration.tp95` — HTTP 服务端请求耗时 TP95
- `http.server.request.duration.tp99` — HTTP 服务端请求耗时 TP99

#### 6. MySQL

- `mysql.request.success` — MySQL 请求成功率
- `mysql.request.qps` — MySQL 请求 QPS
- `mysql.request.duration.avg` — MySQL 请求平均耗时
- `mysql.request.duration.tp95` — MySQL 请求耗时 TP95
- `mysql.request.duration.tp99` — MySQL 请求耗时 TP99

#### 7. Redis

**Jedis**:

- `redis.jedis.request.success` — Redis(Jedis) 请求成功率
- `redis.jedis.request.qps` — Redis(Jedis) 请求 QPS
- `redis.jedis.request.duration.avg` — Redis(Jedis) 请求平均耗时
- `redis.jedis.request.duration.tp95` — Redis(Jedis) 请求耗时 TP95
- `redis.jedis.request.duration.tp99` — Redis(Jedis) 请求耗时 TP99
- `redis.jedis.connection.wait` — Redis(Jedis) 连接池排队数
- `redis.jedis.connection.duration.avg` — Redis(Jedis) 获取连接耗时

**Lettuce**:

- `lettuce.ops.count` — Redis 请求 QPS (Lettuce)
- `lettuce.conn.count` — Redis 建联 (Lettuce)
- `lettuce.failover.down` — Redis 实例摘除 (Lettuce)
- `lettuce.failover.recovered` — Redis 实例恢复 (Lettuce)
- `lettuce.ops` — Redis 请求耗时 (Lettuce)
- `lettuce.timeout` — Redis 生效的 soTimeout 配置 (Lettuce)
- `redis.lettuce.request.success` — Redis 请求成功率 (Lettuce)

**通用**:

- `infra_redis_hit_total` — Redis 命中率

#### 8. MQ (RocketMQ)

**生产者**:

- `rocketmq.producer.qps` — RocketMQ 生产者 QPS
- `rocketmq.producer.success` — RocketMQ 生产成功率
- `rocketmq.producer.duration.avg` — RocketMQ 生产平均耗时
- `rocketmq.producer.duration.tp95` — RocketMQ 生产耗时 TP95
- `rocketmq.producer.duration.tp99` — RocketMQ 生产耗时 TP99

**消费者**:

- `rocketmq.consumer.qps` — RocketMQ 消费者 QPS
- `rocketmq.consumer.success` — RocketMQ 消费成功率
- `rocketmq.consumer.duration.avg` — RocketMQ 消费平均耗时
- `rocketmq.consumer.duration.tp95` — RocketMQ 消费耗时 TP95
- `rocketmq.consumer.duration.tp99` — RocketMQ 消费耗时 TP99

#### 9. Sentinel

**基础限流**:

- `sentinel.request.qps` — Sentinel 请求 QPS
- `sentinel.block.qps` — Sentinel Block QPS
- `sentinel.fail.qps` — Sentinel Fail QPS

**动态限流 (dynamicLimiter)**:

- `sentinel.dynamicLimiter.request.qps` — 总请求 QPS
- `sentinel.dynamicLimiter.block.qps` — 触发 Block QPS
- `sentinel.dynamicLimiter.fail.qps` — Fail QPS
- `sentinel.dynamicLimiter.success.qps` — Success QPS
- `sentinel.dynamic.qps` — 阈值 QPS
- `sentinel.rate.dynamicLimiter.block.qps` — Block 高流量 QPS

**熔断 (circuitBreaker)**:

- `sentinel.circuitBreaker.request.qps` — 总请求 QPS
- `sentinel.circuitBreaker.block.qps` — 触发 Block QPS
- `sentinel.circuitBreaker.fail.qps` — Fail QPS
- `sentinel.circuitBreaker.success.qps` — Success QPS
- `sentinel.rate.circuitBreaker.block.qps` — 触发熔断 QPS

**超时/其他**:

- `red.rpc.cds.timeout` — 服务治理动态超时配置
- `triggered.timeout.qps` — 触发超时 QPS
- `distributed_rate_limiter_waterLevel` — 集群限流水位

#### 10. Schedule (RedSchedule)

- `xschedule.trigger.qps` — 单 Job 执行 QPS
- `xschedule.trigger.duration` — 单任务执行耗时(ms)
- `xschedule.trigger.error` — 单任务执行失败
- `redschedule.task.processing.total` — 运行中的 Job

---

## Cat 指标说明（cat 模式）

Cat 指标用于查询应用的 Transaction / Event / Problem 维度的时序数据。

### theme（主题）

| 值            | 说明                                               |
| ------------- | -------------------------------------------------- |
| `transaction` | 调用链指标（默认），如接口调用的 QPS、耗时、成功率 |
| `event`       | 事件指标                                           |
| `problem`     | 异常/问题指标                                      |

### metric / metrics（指标类型）

优先级规则：

- 传了 `--metrics`：一次查询多个指标
- 没传 `--metrics`，但传了 `--metric`：查询单个指标
- 两者都不传：后端默认 `qps`

| 值                | 说明               |
| ----------------- | ------------------ |
| `qps`             | QPS（每秒请求数）   |
| `avg`             | 平均耗时(ms)       |
| `count`           | 请求次数            |
| `tp50`            | 耗时 TP50          |
| `tp90`            | 耗时 TP90          |
| `tp95`            | 耗时 TP95          |
| `tp99`            | 耗时 TP99          |
| `tp999`           | 耗时 TP999         |
| `failPercent`    | 失败率(%)          |
| `successPercent` | 成功率(%)          |

### type / types（Cat 类型）

`--type`（单选）和 `--types`（多选）互斥，常用值：

| 值        | 说明                   |
| --------- | ---------------------- |
| `Call`    | 下游调用（RPC 客户端） |
| `Service` | 服务端处理             |
| `Http`    | HTTP 请求              |

如果用户未指定，默认使用 `--types "Service,Http"`。

### group by（分组维度）

`--group-bys` 支持三种维度，可组合使用：

| 维度   | 含义                            | 典型场景                    |
| ------ | ------------------------------- | --------------------------- |
| `ip`   | 按机器/Pod 分组                 | 想看各实例的负载分布        |
| `name` | 按接口名分组（含义取决于 type） | 想看各接口各自的 QPS / 耗时 |
| `zone` | 按机房/可用区分组               | 想看跨机房的流量分布        |

> **重要**：`name` 维度的含义取决于 `type`：
>
> - `type=Service` → `name` 是服务端接口名
> - `type=Call` → `name` 是下游调用接口名
> - `type=Http` → `name` 是 HTTP 请求路径

#### 意图→参数推断指南

当用户描述中出现以下意图时，自动推断 `--group-bys` 和 `--type`：

| 用户意图                                  | 推断参数                                     |
| ----------------------------------------- | -------------------------------------------- |
| 「看各接口的 QPS」「按接口维度看」        | `--type Service --group-bys name`            |
| 「看各 RPC 接口的耗时」「下游调用拆分看」 | `--type Call --group-bys name`               |
| 「按机器维度看」「看各 Pod 的情况」       | `--group-bys ip`（不影响 type/types 默认值） |
| 「按机房看流量」「看各可用区的 QPS」      | `--group-bys zone`                           |
| 「各接口在各机器上的分布」                | `--type Service --group-bys name,ip`         |
| 「某个接口在各机器上的表现」              | `--type Service --names xxx --group-bys ip`  |

> 注意：使用 `--group-bys name` 时，通常需要搭配
> `--type`（单选），因为 name 的含义由 type 决定。如果用户未指定 type 且使用了
> `--group-bys name`，默认使用 `--type Service`。

### 常见用法示例

```bash
# 查看 transaction 的 QPS（默认 Service+Http 类型）
--mode cat --app xxx --theme transaction --metric qps

# 一次查看多个 transaction 指标
--mode cat --app xxx --theme transaction --metrics "qps,count,failPercent,tp99"

# 查看 Call 类型的平均耗时
--mode cat --app xxx --metric avg --type Call

# 查看特定接口的 TP99
--mode cat --app xxx --metric tp99 --type Service --names "UserService.getUser"

# 查看 event 的数量
--mode cat --app xxx --theme event --metric count

# 看各 Service 接口各自的 QPS
--mode cat --app xxx --metric qps --type Service --group-bys name

# 看各机器的 tp99
--mode cat --app xxx --metric tp99 --group-bys ip

# 看某个接口在各机房的 QPS
--mode cat --app xxx --metric qps --type Service --names "getUserInfo" --group-bys zone
```

---

## PQL 查询说明（pql 模式）

直接执行 PromQL 表达式查询 VMS 数据。

### 数据源解析优先级

1. `--datasource` — 直接指定 VMS 数据源名称
2. `--app` — 通过服务名反查数据源
3. 自动从 PQL 表达式中解析 metric name 来查找数据源

### 常见用法示例

```bash
# 提供 app 辅助数据源解析
--mode pql --app "creator-service-default" \
  --pql 'sum(rate(rpc_server_requests_total[5m]))'

# 直接指定数据源
--mode pql --datasource "vms-prod" \
  --pql 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))'

# 不提供 app 和 datasource，自动从 PQL 解析
--mode pql --pql 'node_cpu_seconds_total{mode="idle"}'
```

---

## 使用场景示例

### 场景 1：查看服务 CPU 和内存

用户：「看一下 creator-service-default 最近一小时的 CPU 和内存」

```bash
python {SKILL_DIR}/scripts/query.py --mode system \
  --app "creator-service-default" \
  --start "2025-05-30 10:00:00" --end "2025-05-30 11:00:00" \
  --metric-names "cpu.usage,mem.usage"
```

### 场景 2：JVM 全面检查

用户：「检查一下 xxx 服务的 JVM 状况」

```bash
python {SKILL_DIR}/scripts/query.py --mode system \
  --app "xxx-service" \
  --start "2025-05-30 10:00:00" --end "2025-05-30 11:00:00" \
  --metric-names "jvm.young.gc.count,jvm.young.gc.duration,jvm.old.gc.count,jvm.old.gc.duration,jvm.eden.space.used,jvm.old.space.used,jvm.metaspace.used,jvm.live.threads"
```

### 场景 3：查看 Cat Transaction QPS

用户：「看一下 creator-service-default 的 transaction QPS」

```bash
python {SKILL_DIR}/scripts/query.py --mode cat \
  --app "creator-service-default" \
  --start "2025-05-30 10:00:00" --end "2025-05-30 11:00:00" \
  --theme transaction --metric qps
```

### 场景 3.1：一次查看多个 Cat 指标

用户：「看一下 creator-service-default 的 transaction QPS、请求数和失败率」

```bash
python {SKILL_DIR}/scripts/query.py --mode cat \
  --app "creator-service-default" \
  --start "2025-05-30 10:00:00" --end "2025-05-30 11:00:00" \
  --theme transaction --metrics "qps,count,failPercent"
```

### 场景 4：查看特定接口的 TP99

用户：「creator-service-default 的 Call 类型接口 TP99 是多少」

```bash
python {SKILL_DIR}/scripts/query.py --mode cat \
  --app "creator-service-default" \
  --start "2025-05-30 10:00:00" --end "2025-05-30 11:00:00" \
  --metric tp99 --type Call
```

### 场景 5：执行自定义 PQL

用户：「帮我查一下这个 PQL：sum(rate(rpc_server_requests_total{app="xxx"}[5m]))」

```bash
python {SKILL_DIR}/scripts/query.py --mode pql \
  --start "2025-05-30 10:00:00" --end "2025-05-30 11:00:00" \
  --pql 'sum(rate(rpc_server_requests_total{app="xxx"}[5m]))'
```

### 场景 6：查看各 RPC 接口的 QPS（Cat group by）

用户：「看一下 creator-service-default 各个 Service 接口的 QPS」

```bash
python {SKILL_DIR}/scripts/query.py --mode cat \
  --app "creator-service-default" \
  --start "2025-05-30 10:00:00" --end "2025-05-30 11:00:00" \
  --metric qps --type Service --group-bys name
```

### 场景 7：RPC + MySQL + Redis 综合排查

用户：「全面看一下 xxx 服务的中间件指标」

```bash
python {SKILL_DIR}/scripts/query.py --mode system \
  --app "xxx-service" \
  --start "2025-05-30 10:00:00" --end "2025-05-30 11:00:00" \
  --metric-names "rpc.server.request.qps,rpc.server.request.success,rpc.server.request.duration.avg,mysql.request.qps,mysql.request.success,mysql.request.duration.avg,redis.jedis.request.qps,redis.jedis.request.success,redis.jedis.request.duration.avg"
```
