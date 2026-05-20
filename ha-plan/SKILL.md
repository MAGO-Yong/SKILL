---
name: plan-search
description: 查询预案列表接口（getList）。调用 GET https://ha.devops.xiaohongshu.com/api/redplan/plan/v2/search 接口，支持按关键词、业务场景、业务线、有效状态、标签等条件搜索预案，返回预案列表及分页信息。当用户需要搜索/查询预案、获取预案列表、按条件筛选预案时使用。
---

# Plan Search（预案列表查询）

## 接口概览

| 字段 | 值 |
|------|-----|
| 接口名 | getList |
| 请求方式 | GET |
| 完整 URL | `https://ha.devops.xiaohongshu.com/api/redplan/plan/v2/search` |
| Content-Type | `application/x-www-form-urlencoded` |
| 鉴权方式 | SSO（通过代理自动注入，无需手动传 Token；**必须使用 `ha.devops.xiaohongshu.com` 域名，其他域名鉴权会失败**） |

## 请求参数（Query Param）

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| keyword | String | **Y** | - | 搜索关键词，不限制时传空字符串 `""`；**无匹配时 `data.plan` 返回 `null` 而非空数组** |
| scenes | String | N | - | 业务场景英文名（用户输入中文时须先通过 `HA-稳定性元数据` 转换） |
| product | String | N | - | 业务线英文名（用户输入中文时须先通过 `HA-稳定性元数据` 转换） |
| effective | Integer | N | - | 有效状态：`1` 有效预案 / `0` 无效预案；生产环境建议传 `1` |
| actuator | String | N | - | 执行器过滤（枚举见下表） |
| topK | Integer | N | 5 | 返回条数上限 |
| label | String | N | - | **精确标签过滤**（枚举：`降级` / `限流` / `切流`）；预案未打对应标签则不返回，建议优先用 `keyword` 语义搜索 |

### actuator 枚举值

| 枚举值 | 说明 |
|--------|------|
| `eds2` | RPC 切流 |
| `gslb` | GSLB 切流 |
| `rgw` | RGW 切流 |
| `apollo` | Apollo 配置变更 |
| `experiment_v2` | 实验平台变更 |
| `db_failover_v2` | DB 切主 |
| `xgw` | XGW |
| `rcm` | 变更管控 |
| `dns` | DNS |

## 调用方式

使用 `-G` + `--data-urlencode` 自动处理中文 URL 编码。

**最小调用：**

```bash
curl -s -G "https://ha.devops.xiaohongshu.com/api/redplan/plan/v2/search" \
  --data-urlencode "keyword=降级"
```

**完整调用：**

```bash
curl -s -G "https://ha.devops.xiaohongshu.com/api/redplan/plan/v2/search" \
  --data-urlencode "keyword=降级" \
  --data-urlencode "scenes=search" \
  --data-urlencode "product=community" \
  --data-urlencode "effective=1" \
  --data-urlencode "topK=20" \
  --data-urlencode "label=降级"
```

**提取核心字段（配合 `jq`，注意用 `.plan[]?` 防止 null 报错）：**

```bash
curl -s -G "https://ha.devops.xiaohongshu.com/api/redplan/plan/v2/search" \
  --data-urlencode "keyword=降级" \
  --data-urlencode "effective=1" \
  --data-urlencode "topK=10" \
  | jq '.data | {total, plans: [.plan[]? | {id, name, sceneZhName, productZhName, llmSummary, score}]}'
```

**检查调用状态：**

```bash
curl -s -G "https://ha.devops.xiaohongshu.com/api/redplan/plan/v2/search" \
  --data-urlencode "keyword=降级" \
  | jq '{code, message, total: .data.total}'
# 成功：code=200；鉴权失败：code=100000
```

## ⚠️ 已知坑点

| 问题 | 原因 | 解决方式 |
|------|------|---------|
| `code=100000` 鉴权失败 | 使用了错误域名（如 `redplan.devops.xiaohongshu.com`） | 必须用 `ha.devops.xiaohongshu.com` |
| jq 报 `Cannot iterate over null` | `data.plan` 无匹配时为 `null` 而非 `[]` | 迭代时用 `.plan[]?` 而非 `.plan[]` |
| `label` 过滤无结果 | `label` 为精确匹配，预案未打标签则过滤掉 | 去掉 `label` 参数，改用 `keyword` 语义搜索 |

## 返回结构

```
data
├── plan[]?                     预案列表（无匹配时为 null，迭代用 .plan[]?）
│   ├── id                      预案 ID
│   ├── name                    预案名称
│   ├── description             预案描述
│   ├── llmSummary              LLM 生成摘要（推荐直接展示给用户）
│   ├── score                   语义相关性得分（推荐按此字段降序排列）
│   ├── status                  状态
│   ├── kind                    类型
│   ├── actuator                执行器（枚举：eds2/gslb/rgw/apollo/experiment_v2/db_failover_v2/xgw/rcm/dns）
│   ├── effective               是否有效（1 有效 / 0 无效）
│   ├── isDegenerate            是否降级预案
│   ├── label                   标签
│   ├── tagIds[]                标签 ID 列表
│   ├── tagNames[]              标签名列表
│   ├── scene                   业务场景标识
│   ├── sceneName               业务场景英文名
│   ├── sceneZhName             业务场景中文名
│   ├── productName             业务线英文名
│   ├── productZhName           业务线中文名
│   ├── allows[]                允许执行人 UID 列表
│   ├── allowUsers[]            允许执行人详情（BhkUserInfo[]）
│   ├── lastExecTime            最后执行时间
│   ├── lastExecStatus          最后执行状态
│   ├── lastExecUser            最后执行人 UID
│   ├── lastExecUserInfo        最后执行人详情（BhkUserInfo）
│   ├── checkBy                 审核人邮箱
│   ├── checkUserInfo           审核人详情（BhkUserInfo）
│   ├── check_time              审核时间
│   ├── releaseName             发布名称
│   ├── releaseDesc             发布描述
│   ├── validatePeriod          校验周期
│   ├── delayDays               延迟天数
│   ├── peakId                  峰值 ID
│   ├── polling                 轮询标识
│   ├── robotIds[]              机器人 ID 列表
│   ├── chatIds[]               群聊 ID 列表
│   ├── directoryFileId         目录文件 ID
│   ├── alarmNotifierList[]     告警通知人列表
│   ├── associatedServiceList[] 关联服务列表
│   ├── changeSystems[]         变更系统列表
│   ├── action_status           执行状态 { action_uid }
│   ├── created_time            创建时间
│   └── updated_time            更新时间
├── total                       总条数
├── page                        当前页码（默认 1）
└── pageSize                    每页条数（默认 20）
```

### BhkUserInfo 结构

| 字段 | 类型 | 说明 |
|------|------|------|
| uid | String | 用户 UID |
| username | String | 用户名 |
| alias | String | 别名/花名 |
| um | String | UM 号 |
| email | String | 邮箱 |
| email_alias | String | 邮箱别名 |
| mobile | String | 手机号 |
| avatar | String | 头像 URL |
| accountNo | String | 账号编号 |
| type | Integer | 用户类型 |
| property | String | 属性 |
| super_admin | Boolean | 是否超管 |
| id | Integer | 用户 ID |
| created_time | String | 创建时间 |
| updated_time | String | 更新时间 |

## 返回码

| code | 含义 |
|------|------|
| 200 | 成功 |
| 100000 | 鉴权不通过（检查域名是否为 `ha.devops.xiaohongshu.com`） |
| 其他 | 失败，错误原因见 `message` 字段 |

## 使用指引

1. **域名固定用 `ha.devops.xiaohongshu.com`**：其他域名（如 `redplan.devops`）鉴权会失败
2. **`plan` 无匹配时为 `null`**：jq 迭代必须用 `.plan[]?`，否则报错
3. **`label` 是精确过滤非模糊搜索**：优先用 `keyword` 语义搜索；`label` 仅在明确知道预案已打标签时使用
4. **中文场景/业务线需转换**：`scenes` 和 `product` 为英文名，中文须先调用 `HA-稳定性元数据` 转换
5. **`effective=1` 过滤有效预案**：生产场景建议始终传入，避免返回已下线数据
6. **`topK` 默认仅 5 条**：需要更多结果时显式指定
7. **`llmSummary` 推荐直接展示**：语义友好，适合呈现给用户
8. **`score` 推荐降序排列**：值越高与 keyword 语义越相关
