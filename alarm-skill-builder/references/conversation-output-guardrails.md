# Conversation Output Guardrails

These rules prevent the Builder from overwhelming users with internal artifacts.

## Root Principle

The conversation is not the system of record. The Builder should keep rich state internally, but expose only what helps the user answer the next question.

Split every turn into two layers:

- Internal ledger: full Scene Card, IR, dependency map, verification evidence, blockers, readiness score, package material.
- Conversation surface: one concise artifact plus one necessary question.

If a detail does not help the user confirm the scene, correct the flow, bind evidence, or decide to generate, keep it internal.

The exposed information should still be visual. Suppress internal notes, not the interaction structure.

## Default User-Facing Shape

Each turn should expose the smallest artifact the user can act on:

1. Scene intake: compact Scene Card.
2. SOP collection: diagnosis flow.
3. Node binding: one node evidence card.
4. 验证/debug: one-line proof only when it changes trust or next action.
5. Builder status: phase checklist only if asked.

Do not show all artifacts in one turn.

Target length:

- Normal guidance turn: 4-8 lines plus one compact artifact when needed.
- Avoid more than one table or one diagram.
- Do not include implementation vocabulary unless the user asks.
- Prefer card/table/Mermaid/choice chips over raw paragraphs when the user is expected to confirm or edit something.

## Necessary vs. Noisy

Necessary:

- What scene did we understand?
- What did the platform lookup materially confirm?
- What is the current diagnosis flow?
- What exactly is missing for the next node?
- Which user decision is needed now?

Noisy by default:

- Raw verification status, returned field lists, CLI command outcomes, full dependency candidates.
- Tool progress artifacts such as "已探索 N 个文件/已运行 N 条命令", command lines, retry traces, and log pointer details.
- Internal policy narration such as "我会按 Builder 规则...", "我不会提前...", "我把任务限定在...", "先确认 xray-cli 登录...", or "不顺手跑日志/链路/变更...".
- Packaging/validation narration such as "落成可调用本地 Skill 包", "本地已有同名目录", "当作当前产物继续补强", "结构验收", "文件齐不齐", "YAML 能不能解析", or "Skill 头部能不能加载".
- Self-credit or defensive report narration such as "我也把...", "我没有...", "不能声称...", repeated "不能..." lists, or long explanations of why the agent avoided a false conclusion.
- Completeness percentages before the user asks to generate.
- Internal state labels: `candidate`, `verified`, `configured_for_trial`, `runtime_executable`, `blocked`, `IR`.
- Builder lifecycle diagrams.
- Repeating already confirmed context after every turn.

## Hide Policy Narration

Do not narrate the Builder's guardrails, reasoning policy, or self-restraint in the normal conversation. These statements are correct internally but create noise for the user.

Forbidden normal-turn phrasing:

```text
我会先按 Builder 规则做“场景识别”，只读取稳定信息，不提前替你编排 SOP。
```

```text
我已经把任务限定在“读取告警详情补 Scene Card”，不会顺手跑日志、链路、变更这些诊断动作。
```

```text
先确认 xray-cli 登录和事件详情。
```

Use result-first phrasing instead:

```text
我先确认到的场景：
- 业务/服务：{service}
- 触发来源：{alert/rule}
- 核心异常：{symptom}
- 已有关联：{link/rule}

上次遇到这个告警时，你们一般先看什么？
```

If a lookup is blocked, only surface the blocker when it changes the user's next action:

```text
这个告警链接现在读不到规则详情。你可以先继续说排查路径，规则信息后面再补。
```

## Hide Packaging And File-System Narration

After report format or package generation, do not narrate local file-system housekeeping, duplicate directory checks, YAML parsing, structural validation, or implementation packaging considerations.

Forbidden normal-turn phrasing:

```text
报告格式已经定下来了，我现在把它落成一个可调用的本地 Skill 包：入口说明、诊断流程、依赖清单和报告契约都会放齐。之后我会做一次轻量加载检查，确认它不是只停在聊天里的设计。
```

```text
本地已经有一个同名 Skill 草稿目录，而且内容和我们刚刚采出来的链路高度一致；我会把它当作当前产物继续补强/验收，而不是另起一个重复包。
```

```text
我看到现有包里已经包含诊断流、依赖契约、试运行 case。接下来我做一次结构验收：文件齐不齐、YAML 能不能解析、Skill 头部能不能被加载。
```

Use outcome-first phrasing instead:

```text
Skill 草稿已生成。

| 产物 | 状态 |
| --- | --- |
| 诊断流程 | 已生成 |
| 依赖清单 | 已生成 |
| 报告模板 | 已生成 |
| 单次执行检查 | 待执行 |

下一步我执行一次这个 Skill，确认能不能跑通。
```

If packaging fails, show only the blocker and next action:

```text
Skill 草稿暂时不能执行：缺少入口文件。下一步我会补入口文件后再跑一次。
```

## Hide Self-Credit And Defensive Boundaries

The diagnosis or trial-run report may include conclusion boundaries, but it must not narrate the agent's own caution as a paragraph.

Forbidden:

```text
我也把“不能声称”的边界写进验证报告了：不能说确认根因，不能说找到了 NPE 代码点，不能用普通日志替代缺失的 Problem 样本，不能把“查到 0 条人工变更”扩大成“全局无变更”。
```

Use a compact, user-facing boundary instead:

```text
结论边界：证据不足，暂不能确认根因；未拿到 Problem 样本，不能定位具体代码点。
```

If multiple boundaries matter, show at most three bullets under "仍未确认":

```text
仍未确认：
- Problem 样本为空，无法定位具体代码点
- RPC 异常只支持候选方向，不能单独判定根因
- 变更查询仅覆盖当前配置的服务和时间窗口
```

## Avoid Overloaded Scene Cards

Do not show columns like `Source`, `Status`, raw verification attempts, or full dependency tables by default.

Good:

**场景确认**

| 业务/服务 | 触发来源 | 核心异常 | 已有关联 |
| --- | --- | --- | --- |
| {业务/服务} | {告警规则或巡检任务} | {核心异常指标/症状} | {规则/大盘/文档已匹配} |

下一步只缺：实际排障路径和每步数据证据

Use a detailed table only for comparing multiple candidate rules or debugging extraction.

## Do Not Over-Visualize The Builder

The Builder phase flow is not the user's diagnosis flow. Do not show:

```text
场景输入 -> Scene Card -> 平台上下文反查 -> 排障链路采集...
```

unless the user asks "现在 Builder 到哪一步了".

## Dependency Proof Is Not The Main Artifact

Users care whether the future Skill will have real evidence, not the full verification trace. During creation, prefer one line about readiness instead of running heavy checks:

```text
已配置：这个节点的取数入口、输入、期望字段和判断规则都已记录；真实取数放到试运行阶段。
```

Only expand into a dependency/verification table when the user explicitly asks how dependencies are matched, why something is blocked, or asks for a review/debug view.

Before the SOP has a user-confirmed node, do not show or run evidence verification calls such as log pointers, trace checks, change correlation, or metric drilldowns. Ask for the actual troubleshooting path first. After nodes exist, still defer expensive full verification to trial run unless the user asks to run it now.

## Evidence Is Broader Than Metrics

Do not label every node as "待绑定指标/大盘". Use the broader category that matches the SOP:

- 指标大盘/图表
- 业务数据/报表
- 日志
- trace/logview
- 发布/变更
- 实验配置
- 归因链路
- 容量/资源
- RCA case
- 文档/人工上下文

## Dashboard Panel Must Be Stabilized

When a user says "第 5 个 panel，5%", record it but ask for the stable business signal:

```text
我先记录：某个大盘的第 N 个 panel，判断阈值是 {threshold}。为了让运行时 Skill 稳定可执行，还需要确认这个 panel 代表的业务字段，以及对比基线是告警前同长窗口、昨天同期，还是别的口径。
```

Do not claim ready for trial run until the node has:

- dashboard/link or query
- panel id/title/index
- business signal name
- time window
- baseline
- judgment operator and threshold
- missing-data fallback

Even then, in normal conversation say:

```text
这个节点已经配置好，真实取数和判断放到试运行阶段验证。
```

Do not say:

```text
状态：configured_for_trial；Dependency：xray-metric-query；验证：planned。
```

## Creator-Like Flow

The interaction should feel like:

1. "我理解你要做 X，对吗？"
2. "我查到了 Y，能补全场景。"
3. "上次你们怎么排查？先说大概。"
4. "我把它建成这个流程，顺序/并行对吗？"
5. "这个节点看什么数据？"
6. "还缺一个必要口径：阈值/基线/失败时怎么处理。"

Not like:

1. "当前阶段是 Phase N。"
2. "以下是 IR / dependency / verification 表。"
3. "完整度 72%。"
4. "以下是全部能力状态。"

Also not like:

```text
告警触发
  -> 排查节点 A
  -> 排查节点 B
  -> 排查节点 C
```

Use Mermaid instead:

```mermaid
flowchart TD
  A["告警触发"] --> B["排查节点 A"]
  B --> C["排查节点 B"]
  C --> D["排查节点 C"]
```

## Good Turn Examples

Scene lookup success:

````markdown
我理解你要创建的是「{核心异常场景}」排障 Skill。

| 业务/服务 | 触发来源 | 核心异常 | 已有关联 |
| --- | --- | --- | --- |
| {业务/服务} | {告警规则/巡检/反馈} | {核心异常} | {规则/大盘/文档已匹配} |

上次遇到这个告警时，你们一般先看什么？先说大概顺序就行。
````

SOP structure:

````markdown
我先按你说的建成这个流程：

```mermaid
flowchart TD
  A["告警触发"] --> B["排查节点 A"]
  B --> C["排查节点 B"]
  C --> P{"并行排查"}
  P --> D["分支节点 C"]
  P --> E["分支节点 D"]
  P --> F["分支节点 E"]
  D --> G["诊断报告"]
  E --> G
  F --> G
```

这里我理解「节点 A、节点 B」是串行，后面几个是并行，对吗？
````

Node binding:

````markdown
**「{节点名称}」证据卡**

| 要判断 | 数据来源 | 定位方式 | 判断条件 |
| --- | --- | --- | --- |
| {节点要判断的问题} | {平台/大盘/日志/SQL/API} | {稳定定位方式} | {阈值/基线/判断规则} |

还差一个必要口径：这个数据对比的是告警前同长窗口、昨天同期，还是别的基线？

[告警前同长窗口] [昨天同期] [上周同期] [我补充]
````

Blocked preflight:

```text
这个链接现在能打开，但还读不到稳定的 panel 标题。先不影响继续采 SOP，生成草稿前需要补 panel 标题或指标名。

下一个「{节点名称}」看哪个数据？
```
