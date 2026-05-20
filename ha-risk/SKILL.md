---
name: risk
description: "风险管理相关查询：1) 查询已启用风险规则检查结果列表（调用 GET /v2/risk/list）；2) 查询巡检项列表（调用 GET /rule/list）。Use when listing risk check results, enabled rules, risk list queries, governance risk data, or inspection rules."
metadata:
  {"openclaw": {"emoji": "⚠️", "requires": {"env": ["RISK_API_BASE_URL"], "bins": ["python3"]}}}
---

# 风险管理查询

本 skill 提供两个主要功能：

## 1. 风险规则检查结果列表查询

根据用户、场景、规则、产品、时间等条件，分页查询风险检查结果（与接口 getAllEnableRule 对应，路径 `/v2/risk/list`）。

## 2. 巡检项列表查询

查询系统中的巡检项列表（与接口 getAllEnableRule 对应，路径 `/rule/list`），支持按名称、类型、状态等条件筛选。

## 使用方式

### 查询风险规则检查结果列表

在设置好 API 基址后，从 skill 目录执行：

```bash
python3 scripts/list_risk.py [可选查询参数]
```

示例：

```bash
export RISK_API_BASE_URL="https://your-api-host"
python3 scripts/list_risk.py
python3 scripts/list_risk.py --scene-id 1 --page 1 --page-size 20
python3 scripts/list_risk.py --user-email "user@example.com" --status 1
```

### 查询巡检项列表

```bash
python3 scripts/list_rules.py [可选查询参数]
```

示例：

```bash
export RISK_API_BASE_URL="https://your-api-host"
python3 scripts/list_rules.py
python3 scripts/list_rules.py --level "P0" --status 2 --page 1 --page-size 20
python3 scripts/list_rules.py --name "数据库" --owner "admin"
python3 scripts/list_rules.py --type "NETWORK" --status 2
python3 scripts/list_rules.py --type "STORAGE" --level "P1"
python3 scripts/list_rules.py --source "DB" --status 2
python3 scripts/list_rules.py --source "HA" --type "MONITOR"
```

（若在 OpenClaw 中，可用 `{baseDir}`：`python {baseDir}/scripts/list_risk.py ...` 或 `python {baseDir}/scripts/list_rules.py ...`）

### 风险规则检查结果列表查询参数（list_risk.py）

与接口 Param 一致，可通过命令行传入：

| 命令行 | 接口参数                                        | 是否必填 | 
|--------|---------------------------------------------| ---- | 
| `--user-email` | 用户邮箱                                        | 否 | 
| `--scene-id` | 场景ID                                        | 否 | 
| `--rule-id` | 规则ID                                        | 否 | 
| `--product-id` | 业务线ID                                       | 否 | 
| `--result` | 巡检结果 pass 巡检通过不是风险 fail 巡检失败 是风险            | 否 | 
| `--service-name` | 服务名                                         | 否 | 
| `--status` | 状态 1 风险 8 不是风险 3 延期 5 误报 6 治理中 7 治理完成 9 忽略  | 否 | 
| `--start-time` | 开始时间                                        | 否 | 
| `--end-time` | 结束时间                                        | 否 | 
| `--within-the-plan` | （`true` 只查询治理计划内的 / `false` 查询全量）  默认 false | 否 | 
| `--page` | page                                        | 否 | 
| `--page-size` | pageSize                                    | 否 | 

未指定 `page` / `page-size` 时，默认使用环境变量 `PAGE` / `PAGE_SIZE`，再否则为 `1` / `10`。

如果 --within-the-plan 参数传 `true` 则必须传场景ID或业务线ID（scene-id 或 product-id），否则会返回错误。 
原因是 只支持查询具体的场景或业务线的治理计划内的风险检查结果，不支持全局范围的治理计划内查询。

### 巡检项列表查询参数（list_rules.py）

与接口 Param 一致，可通过命令行传入：

| 命令行 | 接口参数 | 类型 | 是否必填 | 说明                        |
|--------|---------|------|----------|---------------------------|
| `--level` | level | String | 否 | 风险等级（P0-高风险，P1-中风险，P2-低风险） |
| `--status` | status | Integer | 否 | 状态（2-启用，3-禁用）       |
| `--name` | name | String | 否 | 规则名称                      |
| `--type` | type | String | 否 | 风险类型，支持枚举值（见下方说明）        |
| `--target-type` | targetType | String | 否 | 目标类型                      |
| `--is-ha-specification` | isHaSpecification | Integer | 否 | 是否为HA规范                   |
| `--source` | source | String | 否 | 来源，支持枚举值（见下方说明）          |
| `--owner` | owner | String | 否 | 负责人                       |
| `--page` | page | Integer | 否 | 页码                        |
| `--page-size` | pageSize | Integer | 否 | 每页大小                      |

未指定 `page` / `page-size` 时，默认使用环境变量 `PAGE` / `PAGE_SIZE`，再否则为 `1` / `20`。

#### 风险类型（type）枚举值

| 枚举值 | 说明 |
|--------|------|
| `NETWORK` | 网络层风险 |
| `COMPUTE` | 计算层风险 |
| `STORAGE` | 存储层风险 |
| `SERVICE_ARCH` | 服务架构风险 |
| `CONFIG` | 配置风险 |
| `DISASTER_RECOVERY` | 容灾&备份风险 |
| `CAPACITY` | 容量&性能风险 |
| `SECURITY` | 安全&合规风险 |
| `MONITOR` | 监控&告警风险 |
| `CHANGE` | 变更&发布风险 |
| `RED_CLOUD` | 中间件风险 |
| `CNY_STABILITY_RISK` | CNY稳定性风险 |
| `OTHER` | 其他风险 |

#### 来源（source）枚举值

| 枚举值 | 说明 |
|--------|------|
| `redCloud` | 中间件 |
| `DB` | 存储 |
| `non_relational` | 非关系型数据库 |
| `rke` | 中间件 |
| `network` | 网络系统 |
| `middle_ground` | 中台系统 |
| `PLAN` | 预案平台 |
| `HA` | 高可用平台 |

## 输出

### 风险规则检查结果列表（list_risk.py）

脚本将接口完整响应以 JSON 打印，包含 `code`、`message`、`data`（分页信息与 `list`，元素为 `QueryCheckResultResponse`，含 ruleName、sceneName、queryRuleV2Response 等字段）。

### 巡检项列表（list_rules.py）

脚本将接口完整响应以 JSON 打印，包含 `code`、`message`、`success`、`data`（分页信息与 `list`，元素为 `QueryRuleV2Response`，含 id、name、key、description、types、level、solution、historyCase、owners、status 等字段）。

## 配置

通过环境变量配置：

- `RISK_API_BASE_URL` — 服务根地址 默认 `https://haplus.devops.xiaohongshu.com`
- `RISK_API_PATH` — 风险查询路径，默认 `/v2/risk/list`
- `RULE_API_PATH` — 巡检项查询路径，默认 `/rule/list`
- `RISK_API_TOKEN` — 若网关需要鉴权，可设为 Bearer Token
- `PAGE` — 默认页码（当命令行未传 `--page` 时）
- `PAGE_SIZE` — 默认每页条数（当命令行未传 `--page-size` 时）

## 依赖
`requests>=2.28.0`。
