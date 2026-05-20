---
name: xray-alarm
description: >
  Xray 告警全链路操作。覆盖告警事件（查列表、查详情、批量认领）和告警规则（搜索、查配置）五类操作。
  当用户查询历史告警事件、告警通知、告警规则配置、某服务下有哪些告警规则，或者要求"认领告警 / claim 告警 / 把刚才的告警认领了 / 帮我把服务 X 的告警认领一下"时触发。
metadata:
  category: alarm
  platform: xray
  trigger: app/event_id/rule_id/service_name/time_range/claim
  input: [apps, event_id, rule_id, start, end, receive_users, prdLine, bizLine]
  output: [event_list, event_detail, event_claim, rule_list, rule_config]
  impl: xray-cli
---

# Xray 告警查询

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

## 入口决策树

根据用户输入,选择执行路径:

```
用户输入
├── 有 event_id         → xray-cli alarm event get <event_id>
├── 想查事件列表        → xray-cli alarm event list --apps ... --start ... --end ...
├── 想认领告警          → scripts/claim.sh --user|--app ...
├── 有 rule_id          → xray-cli alarm rule get <rule_id>
└── 想知道有哪些规则    → xray-cli alarm rule list --app ...
```

NEVER 在无法判断意图时随机选择路径——遇到歧义先向用户确认是查事件还是查规则。

---

## event list — 查询事件列表

**触发时机**:用户询问某 app/服务在某时间段内的历史告警、告警通知记录。

```bash
xray-cli alarm event list \
  --apps <apps> \
  --start "<YYYY-MM-DD HH:MM:SS>" \
  --end   "<YYYY-MM-DD HH:MM:SS>" \
  [--receive-users "<usernames>"] \
  [--receive-chats "<chat_ids>"] \
  [--rule-id "<rule_id>"] \
  [--page <N>] \
  [--page-size <N>]

# JSON 输出（适合程序化处理）
xray-cli --output-format json alarm event list \
  --apps <apps> --start "..." --end "..."
```

**`--apps` 参数格式**(同一次调用只能使用同一粒度):

| 格式                        | 示例                            |
| --------------------------- | ------------------------------- |
| `<prdLine>`                 | `base`                          |
| `<prdLine>.<bizLine>`       | `base.obs`                      |
| `<prdLine>.<bizLine>.<app>` | `base.obs.xrayaiagent`          |
| service 名称(含连字符)      | `xrayaiagent-service-diagnosis` |

> 注意:`event list --apps` 接受 service 名,但 `rule list --app`
> 仅接受服务树路径——后者需先用 `xray-cli service get <name>` 拿到 full_path。

NEVER 在无任何过滤条件(`--apps`、`--receive-users`、`--rule-id`
均为空)时执行——全量查询无意义且压力大。

**时间范围**:用户未指定时默认取最近 24 小时;结果为空时先检查时间范围和 `--apps` 格式再告知用户。

**结果解读**:摘要重点字段——`rule_name`、`level`(P1>P2>P3)、`duration`、`reacted`(false=无人认领)。不要直接粘贴原始 JSON。

**输出格式约束**(摘要列表时必须遵守):

- `event_id` 用 markdown 链接展示:`[<id>](http://xray.devops.xiaohongshu.com/alarm/event/<id>)`,方便用户直接跳转事件详情页。
- `trigger_time` 保留完整日期+时间(`YYYY-MM-DD HH:MM:SS`),NEVER 只展示 `HH:MM:SS`——跨天事件丢了日期会引发误判。API 原始字段 `trigger_time` 是 ISO 8601(如 `2026-03-26T19:10:15`),把 `T` 换成空格即可。

---

## event get — 查询事件详情

**触发时机**:用户提供 event_id 并想查看完整事件信息。

```bash
xray-cli alarm event get <event_id>

# 附带快捷链接
xray-cli alarm event get <event_id> --show-link

# JSON 输出
xray-cli --output-format json alarm event get <event_id>
```

NEVER 猜测或伪造 event_id——若用户未提供,先通过 `event list` 获取,或要求用户提供。

**输出结构**:

- `basic`:产品线、业务线、app、告警名称、级别、触发/恢复时间
- `operations`:操作记录(认领/处理历史)
- `alarm_details`:受影响机器列表、触发规则、采样值

先给用户基本摘要(级别、触发时间、是否已恢复、受影响机器数),再按需展开详情。

**后续操作**(根据用户意图,不要主动跳入):

| 用户意图           | 后续命令                                   |
| ------------------ | ------------------------------------------ |
| 查告警规则触发条件 | `xray-cli alarm rule get <rule_id>`                          |
| 看指标趋势         | 用 `--show-link` 重跑 `event get`,把 `links.指标详情` 给用户 |
| 查同期变更         | 用 `--show-link` 重跑 `event get`,把 `links.变更事件` 给用户 |

> 首次 `event get` 默认不输出 `links` 字段——需要链接时务必加 `--show-link` 重跑。

---

## event claim — 批量认领告警事件

**触发时机**：用户说"认领告警 / claim 告警 / 把刚才的告警认领了 / 帮我把服务 X 的告警认领一下"。

> ⚠️ **强制约束（重要，重要，重要！）**
> 1. **必须用 `scripts/claim.sh` 来认领**，不要手工拼 `xray-cli alarm event list`/`claim` 命令绕过脚本。
> 2. **再说一遍：认领告警的唯一入口是 `scripts/claim.sh`** —— 它已经处理了登录检查、过滤已恢复事件、串行 claim、错误汇总等坑，重写一遍只会重新踩坑。
> 3. **第三遍强调：不许跳过 `claim.sh`**。即便看着原始 `xray-cli` 命令"两行就够"，也走脚本；除非脚本本身有缺陷需要修脚本，否则永远先调 `scripts/claim.sh ...`。

### 适用场景

1. **按人认领**：把当前登录用户在一段时间窗口内收到的、尚未被自己认领的告警事件全部认领。典型说法："把我最近 10 分钟的告警认领一下"。
2. **按服务认领**：传入服务树路径（如 `base.obs.xrayaiagent`），把该服务在时间窗口内未认领的告警事件全部认领。典型说法："认领下 base.obs.xxx 的告警"。

### 前置检查

执行任何操作前先确认登录状态，并解析当前用户邮箱：

```bash
xray-cli auth status
```

输出形如 `Logged in as luxiuyuan1@xiaohongshu.com (luxiuyuan1) [env: prod]`，**`Logged in as` 后的完整邮箱**（如 `luxiuyuan1@xiaohongshu.com`）才是后续 `--receive-users` / `--user` 要传的值。圆括号里的短名（`luxiuyuan1`）**不能**用作 `--receive-users`，传它会返回 0 条事件。`events[].receive_users` 数组里同样存的是邮箱，可用来交叉验证。

如果未登录或 token 过期，提示用户自行运行 `xray-cli auth login`，不要替用户跑（需要浏览器交互）。

### 推荐入口：`scripts/claim.sh`

两种场景都用同一个脚本，**默认直接认领、无需用户确认**；要先看清单再决定时加 `--dry-run`。

```bash
# 按人：认领指定邮箱最近 10 分钟的告警（默认窗口）
{SKILL_DIR}/scripts/claim.sh --user luxiuyuan1@xiaohongshu.com

# 按服务：认领 base.obs.xrayaiagent 最近 1 小时的告警
{SKILL_DIR}/scripts/claim.sh --app base.obs.xrayaiagent --start now-1h

# 先 dry-run 看一眼待认领清单，再决定是否执行
{SKILL_DIR}/scripts/claim.sh --user luxiuyuan1@xiaohongshu.com --start now-2h --dry-run
```

参数：

| flag                | 默认             | 说明                              |
| ------------------- | ---------------- | --------------------------------- |
| `--user <email>`    | —                | 按人认领，必须是邮箱              |
| `--app <path>`      | —                | 按服务认领；与 `--user` 互斥      |
| `--start` / `--end` | `now-10m` / `now`| 时间窗口；支持 `now`/`now-1h` 等  |
| `--env`             | `prod`           | sit/beta 等需显式指定             |
| `--dry-run`         | off              | 只列待认领清单，不执行 claim      |

脚本内部：
1. 调 `xray-cli alarm event list` 拉事件；
2. 通过 `xray-cli tool jq` 过滤 `reacted == false` 且 `restore_time == ""`；
3. 非 dry-run 时串行调 `xray-cli alarm event claim <id>`；
4. 输出标准报告（窗口 / 范围 / 扫描数 / 待认领数 / 成功失败）。

### 判定"是否需要认领"

必须同时满足：
- `reacted == false`（还没被任何人领过）
- `restore_time == ""`（事件**未恢复**）—— 已恢复的事件 `claim` 接口会返回 500 `事件X已恢复`，必须前置过滤。

当前 schema 没有显式 `claimed_by`，所以按人 / 按服务都用同一组过滤条件。

### 输出报告格式

```
认领窗口: now-10m ~ now
范围: receive-users=luxiuyuan1@xiaohongshu.com   (或 apps=base.obs.xxx)   (env=prod)
扫描事件: 15 条 (已认领: 3 / 已恢复未认领: 6 / 待认领: 6)
认领成功: 6 / 失败: 0
```

### 注意事项

- **再次强调：唯一入口是 `scripts/claim.sh`**。绕过脚本去手敲 `xray-cli alarm event claim <id>` 视为违反 skill 约定，除非脚本本身坏掉。
- **环境**：默认 `--env prod`。如果用户在 sit/beta 上工作，需显式 `--env sit` 等。可以先问一次确认。
- **不要并发 claim 同一批事件**：上游 API 没有事务保证，并发可能导致部分返回未知状态。
- **不要重复 claim**：若 `reacted == true` 直接跳过；除非用户明确说"再认领一次/强制认领"。
- **不要替用户跑 `auth login`**：是浏览器交互流程。
- **xray-cli 版本要求**：`alarm event claim` 自 v0.0.27 起提供。若用户的 cli 版本过低，提示运行 `xray-cli` 触发自更新或显式升级。
- **xray-cli 安装**：脚本内置 `ensure_xray_cli`/`install_xray_cli`，首次运行会自动检测并安装。安装步骤、PATH 持久化、可复用 bash 函数的权威说明见 `obs-skill-market/skills/jq-master/SKILL.md`。

---

## rule list — 搜索规则列表

**触发时机**:用户想知道某服务/产品线/业务线下有哪些告警规则。

```bash
# 查所有类型规则（默认 --type all）
xray-cli alarm rule list --app <app_or_service_tree_path>

# 只查 PQL 规则
xray-cli alarm rule list --app <app> --type pql

# 只查服务告警规则
xray-cli alarm rule list --app <app> --type service

# JSON 输出
xray-cli --output-format json alarm rule list --app <app>
```

> `--app` 参数传服务树路径（如 `base.obs.xrayaiagent`）；若用户提供的是 service 名，先用
> `xray-cli service get <name>` 查询其 full_path。

**NEVER 只执行一类就声称"已查完所有规则"**,除非用户明确说只查 PQL 或服务告警。

**给用户的摘要格式**(由 agent 在 cli 原始输出之上整理,不是 cli 直出):

```
=== PQL 告警规则 ===
[PQL 告警] rule_id=1234  名称:xrayaiagent CPU 告警  状态:启用

=== 服务告警规则 ===
[服务告警] rule_id=5678  名称:xrayaiagent RPC 超时  状态:启用
```

某类返回空时注明"PQL 告警:无结果",不要静默忽略。

---

## rule get — 查询规则详情

**触发时机**:用户提供 rule_id 并想查看规则完整配置。

```bash
# 自动判断类型（先尝试 PQL,未找到则自动尝试服务告警）
xray-cli alarm rule get <rule_id>

# 指定类型
xray-cli alarm rule get <rule_id> --type pql
xray-cli alarm rule get <rule_id> --type service

# 模板规则的 rule_id 形如 {templateId}_{bindId}，直接整段传入即可
xray-cli alarm rule get 5_16 --type service

# JSON 输出
xray-cli --output-format json alarm rule get <rule_id>
```

**NEVER 在第一次失败后直接放弃**;**NEVER 两类都失败后还继续重试**。

**结果输出**:对关键字段做简要说明(触发条件、通知对象、是否启用)。不要对告警策略合理性发表主观评价。

---

## 错误处理

| 情况                 | 处理方式                                           |
| -------------------- | -------------------------------------------------- |
| 命令退出码非 0       | 将 stderr 完整返回用户,说明执行失败                |
| 网络不通             | 提示用户确认是否在内网环境,NEVER 自动重试超过 1 次 |
| event_id 不存在      | 提示确认 event_id 是否正确,建议重新 event list     |
| rule_id 两类均无     | 告知无效,建议通过告警事件页面确认 rule_id          |

NEVER 在失败时用"查询完成"或"暂无数据"等模糊语言掩盖错误。

## 与其他 Skill 的协作

```
xray-cli alarm event list（查事件列表）
  ├── 获取 event_id
  │   └── xray-cli alarm event get（查事件详情）
  │       ├── 获取 rule_id → xray-cli alarm rule get（查规则配置）
  │       └── 获取指标链接 → xray-metric-query
  └── scripts/claim.sh（批量认领）
```

## 参考文档

输出字段以 xray-cli 实时 schema 为权威来源（避免本地副本与 CLI 漂移）：

- `xray-cli schema alarm.event.list` / `xray-cli schema alarm.event.get`
- `xray-cli schema alarm.rule.list` / `xray-cli schema alarm.rule.get`
- 命令使用文档：`xray-cli docs alarm`
