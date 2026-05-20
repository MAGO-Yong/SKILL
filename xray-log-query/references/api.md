# Xray 日志查询接口参考

本 skill 已切换到 **xray-cli** 作为唯一调用入口（v2.0.0+）。本页保留底层 HTTP API 的简要说明，仅供需要绕过 CLI 直连后端的高级场景使用；日常请直接用 `xray-cli`。

## CLI 参考

最权威的 CLI 文档由 CLI 自身提供：

```bash
# 整体说明 + 各表必填字段 + 各表常用字段速查 + 典型用法
xray-cli docs log

# 子命令的精确 flag 与默认值
xray-cli log query --help
xray-cli log chart --help
xray-cli log cluster --help

# JSON Schema（输入 / 输出）
xray-cli schema log.query
xray-cli schema log.chart
xray-cli schema log.cluster
```

## 底层 HTTP API（绕过 CLI 时参考）

> 仅在需要直接打 HTTP 时使用。一般情况下都该走 `xray-cli`，CLI 已封装鉴权、ticket 生成、参数校验、错误码映射。

### Base URL

```
prod: https://xray-ai.devops.xiaohongshu.com/open/skill/log/api/v1/tables
beta: https://xray-ai.devops.beta.xiaohongshu.com/open/skill/log/api/v1/tables   （仅 application 表）
```

### 认证

请求需在 Header 中携带 `xray_ticket`：

```
xray_ticket = Base64( app + "&" + token + "&" + currentTimeMillis )
```

`currentTimeMillis` 必须现场生成，后端做时效性验证。

```python
import base64, time
ticket = base64.b64encode(f"{app}&{token}&{int(time.time()*1000)}".encode()).decode()
# Header: xray_ticket: {ticket}
```

### 三个端点

| 端点                         | 用途                                           | CLI 等价                |
| ---------------------------- | ---------------------------------------------- | ----------------------- |
| `GET /tables/{tid}/charts`   | 时间分布直方图（同时为 `/logs` 预热缓存）      | `xray-cli log chart`    |
| `GET /tables/{tid}/logs`     | 分页日志详情                                   | `xray-cli log query`    |
| `GET /tables/{tid}/cluster-logs` | Drain 模板聚类（仅 application 表）        | `xray-cli log cluster`  |

`tid` 因表而异（application = 33；其他表不再硬编码进 skill，统一用 CLI 抹平）。

### 通用 Query 参数

| 参数             | 类型    | 说明                                                          |
| ---------------- | ------- | ------------------------------------------------------------- |
| `table`          | string  | 表名（CLI 的 `--table`）                                      |
| `query`          | string  | Lucene 过滤条件                                               |
| `st` / `et`      | int64   | Unix 秒                                                       |
| `page` / `pageSize` | int  | 仅 logs；pageSize 默认 20，最大 10000                         |
| `orderKeywords`  | string  | 仅 logs；`asc` 或 `desc`，默认 `desc`                         |
| `searchTraceApp` | bool    | 仅 logs；按 traceId 自动关联涉及的服务（CLI 的 `--search-trace-app`） |
| `compareST` / `compareET` | int64 | 仅 cluster-logs；对比窗口                                |

### 响应包络

所有端点返回统一包络 `{code, msg, data}`，`code != 0` 时 `msg` 含错误描述。CLI 已映射这层，调用方不必关心。

### 校验规则（CLI 已内置）

直连 HTTP 时仍需自行校验：

- query 必须含目标表的必填字段（详见 `xray-cli docs log` 的"各表字段速查"）
- 时间跨度 ≤ 5 天（Apollo `max_query_time_range_day`）
- pageSize ≤ 10000
- xrayTraceId 必须 32 位十六进制
- query 不允许 `| SELECT` 注入

### 常见错误码与含义

| 错误信息                          | 处理                                            |
| --------------------------------- | ----------------------------------------------- |
| `查询超出限制`                    | 缩小时间范围或加更多过滤条件                    |
| `必须含有 subApplication...`     | 按表的必填字段补条件                            |
| `没有对应的访问权限`              | 响应中含申请链接，提示用户申请                  |
| `此服务查询被禁止`                | 服务在黑名单中                                  |
| `查询时间区间过长`                | 超过最大查询天数                                |
| `日志表已下线`                    | 该表已停用                                      |

## 历史

skill v1.x 使用 Python 直接调 HTTP API（`scripts/query_*.py` + `validate_query.py`），v2.0.0 起统一通过 `xray-cli` 调用，去除了重复的校验和表配置维护。
