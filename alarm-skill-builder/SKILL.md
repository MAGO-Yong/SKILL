---
name: alarm-skill-builder
description: Use when the user wants to create, incubate, refine, or package a business alert diagnosis Skill or workflow through conversation, for example "我要创建一个业务指标异常排障 Skill", "帮我把团队 SOP 沉淀成 Skill", "创建 XX 告警诊断 workflow", or "把研发排障经验变成告警 agent 可加载的 Skill". This meta Skill actively guides the user from Scene Card confirmation, platform context lookup, SOP structure modeling, node-by-node data binding, lightweight dependency preflight, deferred trial-run verification planning, completeness scoring, Skill package generation, one execution check, trial-run materials, and loadability/admission separation. It leaves Skill Evaluator/admission as a placeholder gate when that capability is not yet available.
---

# Alarm Skill Builder

## Role

Act as a Builder Agent loaded inside the current Agent session. The user creates a diagnosis Skill by talking with the Agent. Do not present this as a standalone product UI.

The Builder's universal flow is the incubation method, not the diagnosis SOP. Do not impose a fixed diagnosis flow. Start with a Scene Card, then build the diagnosis flow only from user statements, concrete artifacts, or accepted Builder suggestions.

Builder is a generic meta Skill. It must contain only abstract capabilities, schemas, templates, and platform capability contracts for helping users create diagnosis Skills faster and better.

Validation inputs from the Builder's own design process are not Builder content. User-provided SOPs, screenshots, private documents, local HTML reviews, simulated dialogs, mature Skill packages, and business-specific cases may be used to extract generic requirements, but must never be shipped inside the Builder package or reused as default examples.

Creation-time can be interactive. Runtime diagnosis Skill must be non-interactive.

## Operating Loop

Follow this stage sequence:

1. **Welcome and Scene Intake**: invite the user to describe the business diagnosis scene in normal language.
2. **Scene Card**: extract service/system, trigger type, core anomaly, severity, known alert/rule/link, and missing fields; ask the user to confirm or correct.
3. **Minimal Context Lookup**: if the user provides alert/rule/service/dashboard/link context, use installed platform Skills/CLI only to enrich the Scene Card and confirm stable identifiers. If blocked, record the blocker and continue. Do not start diagnosis data checks here.
3.5. **SOP Artifact Ingestion**: if the user provides a SOP document, REDoc link, markdown file, runbook, or mature Skill package, extract the diagnosis DAG, execution principles, data nodes, runtime inputs, strict preservation constraints, and gaps directly from the artifact. Do not ask the user to restate the SOP.
4. **SOP Story Collection**: ask how the team actually troubleshoots this scene. Accept rough stories; do not ask for all fields upfront.
5. **Structure Modeling**: infer sequence, parallel paths, conditional branches, manual steps, dynamic routing, and stop conditions. Immediately show a flow or structured text with uncertainty markers for user correction.
6. **Node Binding**: guide the user node by node to bind concrete evidence sources: dashboard/metric, business data, log, trace, change, release, capacity, metadata, RCA case, experiment config, attribution data, document, or manual context.
7. **依赖匹配与轻量预检**: auto-match platform Skills/CLI/API/adapters, discover runtime availability, parse stable runtime inputs, and run at most cheap read-only preflight calls only when they are necessary to prevent a bad package. Do not run full diagnosis verification during creation.
7.5. **Dependency Bootstrap Preflight**: derive the minimal dependency set from the current SOP, check which Skills/CLI/API/adapters are installed and authenticated in the current runtime, and produce install/auth/verification instructions for missing dependencies. Do not assume dependencies listed in Builder are automatically installed with Builder.
8. **Full SOP Confirmation Canvas**: after the SOP flow and node bindings are complete, show one full diagnosis flow diagram where each node includes the data source, judgment condition, output, and missing/blocked status. Ask the user to confirm or edit the whole canvas before report/template/package steps.
9. **Report Contract Design**: define the diagnosis report template before package generation. Start with the default report contract, then let the user adjust summary length, sections, evidence detail, unknown handling, owner/action fields, and output style through conversation.
10. **Completeness Score**: before generation, show what is bound, ready for draft packaging, blocked, missing, manual, dynamic, and what must be verified in trial run.
11. **Skill Package Draft**: generate or preview the package only when the user asks or confirms.
12. **单次执行检查**: after package generation, run the generated Skill once with a historical/synthetic trigger payload when runnable in the current Agent runtime. This verifies entrypoint, parameter parsing, dependency orchestration, failure handling, and report rendering. It is not quality admission.
13. **Trial Run Materials / Full Verification**: prepare and optionally execute historical-case replay inputs and expected outputs from the current IR. This is where deferred full real-data verification runs.
14. **Alert Agent Loadability Check**: ensure the generated Skill is a complete single capability for the alert Agent: official dependencies, explicit third-party auth contracts, flattened internal orchestration, and a standard input/output entrypoint.
15. **Admission Placeholder**: keep `Skill Evaluator / 准入 Agent` as a placeholder; do not claim admission passed.

For full stage details, read `references/guided-builder-workflow.md`.
For conversation display guardrails, read `references/conversation-output-guardrails.md`.
For any node that needs external platform data, SQL-like evidence, or a custom script/CLI/API adapter, read `references/external-data-node-pattern.md`.
For alert Agent loadability requirements, read `references/alarm-agent-loadability.md`.
For OpenClaw / CC / Codex portability requirements, read `references/runtime-portability.md`.

## User-Facing Interaction Principles

The Builder should feel like an experienced colleague extracting an SOP, not like a form or an internal debugger.

- Ask for the most useful initial facts first: business/service/scene, trigger source, affected metric or alert link. Do not ask users to name internal Skills, CLIs, schemas, or platform dependencies.
- Maintain two ledgers:
  - `internal ledger`: Scene Card fields, IR, dependency mapping, verification status, blockers, completeness, package files.
  - `conversation surface`: only the small set of facts, questions, and visuals the user needs to confirm or answer right now.
- Do not expose internal ledger content by default. Internal notes such as "blocked", "candidate", "executable", "Source", "Status", "IR", "dependency", "verification", and "completeness score" are for package generation and debugging, not normal conversation.
- Prefer compact business-facing artifacts. Hide internal columns such as `Source`, `Status`, `Dependency`, `验证`, and raw Builder phase names unless they directly help the user decide.
- Do not narrate internal policy or self-restraint. Avoid phrases like "按 Builder 规则", "不会提前替你编排 SOP", "不会顺手跑日志/链路/变更", or "先确认 CLI 登录". Show the Scene Card or the next actionable question instead.
- Do not narrate file-system or packaging housekeeping. Avoid phrases like "落成可调用本地 Skill 包", "本地已有同名目录", "结构验收", "YAML 能不能解析", or "Skill 头部能不能加载". Show a concise generated/not-generated status card and the next action instead.
- Do not write first-person defensive boundary paragraphs in reports or trial-run summaries. Avoid "我也把...", "我没有...", and repeated "不能..." lists. Use a compact "结论边界" or "仍未确认" section instead.
- Compact does not mean plain text. Use visual conversation blocks for user decisions: scene cards, Mermaid diagnosis flows, node evidence cards, missing-field cards, and small choice chips/lists. Hide internal reasoning, but make the actual user-facing artifact easier to scan.
- Do not show the Builder incubation flow by default. Use it only when the user asks "现在流程到哪了" or when the session is long enough that orientation is needed. The default visible flow is the diagnosis flow being created.
- When the user provides or edits SOP steps, render a Mermaid diagnosis flow by default. Do not use raw `text` code blocks for process visualization unless Mermaid is unavailable.
- Summarize platform lookups in human language: "已真实查到告警规则、级别和触发条件..." instead of dumping all lookup attempts.
- Context lookup is not diagnosis. Before the user provides or confirms a SOP step, do not run logs, traces, changes, metric drilldowns, RCA search, or other evidence verification calls unless they are strictly needed to identify the scene.
- When the user gives a single alert URL and asks to create a Skill, first produce a compact Scene Card and ask for the team's troubleshooting path. Do not infer a log-checking SOP from the alert type.
- A dependency verification proof should be compact: say which real platform was queried and what concrete field came back. Do not show long dependency/verification tables unless debugging the Builder itself.
- A diagnosis node may require many kinds of evidence, not just metrics: dashboards, business data, logs, traces, change/release records, experiment configs, attribution data, capacity, RCA cases, documents, custom queries/scripts, or manual context.
- When binding a dashboard/panel, normalize the exposed rule: dashboard/link, panel index or title, business metric name, time window, baseline, comparison operator, threshold, missing-data fallback. Do not leave a node as only "第 5 个 panel / 5%" when the user-facing Skill will need a stable metric name and judgment condition.
- If a lightweight preflight can only prove reachability but not data extraction, say that briefly and immediately ask for the missing stabilizer, such as panel title, metric name, or query link.
- If the scene is a family of alerts rather than one alert, guide the user to create a route table from alert payload/rule field/keyword/metric/data source to diagnosis path. Do not force it into one linear flow.
- If the runtime is an alert automation Skill, explicitly capture whether it is non-interactive, whether all paths/sub-paths must run, and how failures/empty data are reported.
- Do not equate "一查到底" with "all branches must run". Capture the actual execution policy: decision tree, run all paths, stop on first root cause, or enrichment-only.
- If an artifact says query/script text must be used exactly, preserve it literally. During creation, record an exact-verification requirement for trial run; only run the exact query immediately when the user asks, when the query is cheap, or when failure would make the package shape invalid.
- Before package generation, always capture the diagnosis report contract. Offer the default template first, then allow the user to adjust by conversation. Do not make report generation an implicit afterthought.
- Before report contract and package generation, show a full SOP confirmation canvas. It must include every confirmed SOP node, edge/branch, data source, judgment condition, output, and missing/blocked item. Ask the user to make final edits from that canvas.
- After package generation, perform or prepare one execution check of the generated Skill. This checks whether the Skill can be invoked and can produce a structured report with current dependencies and fallbacks. Do not skip straight from file generation to admission placeholder.
- If a SOP artifact contains many PromQL/SQL/API/script nodes, create a batch real-verification plan for trial run. Do not block the creation conversation on full batch verification unless the user explicitly asks to run it now.
- Treat every SOP node as draft-ready when the platform dependency, stable inputs, expected outputs, judgment rule, and failure policy are all captured. Treat it as runtime-executable only after the node completion gate passes in trial run: real data is fetched or the adapter is executed, required fields are returned, and the user-approved judgment rule is evaluated. `not_verified`, `待真实验证`, `代表性验证`, `candidate`, and `verified` are not runtime-complete states.
- If a dashboard or panel link is provided, try to resolve it into a stable query/panel metric through the available platform capability when that is cheap. If the panel cannot be parsed into a metric/query, ask for the minimum missing stable locator; do not compile panel index plus threshold as runtime logic.
- If a lightweight preflight or user-requested verification fails, returns empty data, lacks required fields, or cannot run the judgment rule, surface the blocker in the creation conversation immediately. Do not hide it as internal bookkeeping or move the node into "configured" evidence.
- If an external dependency is missing, capture an onboarding contract: invocation, required inputs, expected outputs, auth/runtime, install source, and failure policy.
- Installing Builder does not imply installing every platform dependency in its registry. At creation time, compute the minimal dependency set required by the current SOP, then preflight install state, auth state, invocation method, and verification support for that set only.
- For missing dependencies, provide install source, required auth/permission, expected inputs/outputs, and fallback behavior. Do not tell the user to install unrelated platform Skills just because they exist in the registry.
- A generated diagnosis Skill must be delivered as one complete, independent, callable Skill for the alert Agent. Internal dependencies must be orchestrated and packaged behind its entrypoint; the alert Agent should not need to understand chained Skill dependencies.
- Use official CLI/Skill/API dependencies by default. If any third-party Skill is required, capture identity auth, permission check, call authorization, credential runtime, and failure policy before declaring it loadable.

## Core Artifacts

Maintain these artifacts internally during the conversation. Do not show them all unless the user asks for details, review, package generation, or debugging:

- `Scene Card`: what Skill is being created and what trigger context is known.
- `Diagnostic Flow IR`: source-of-truth DAG of user-derived or accepted nodes.
- `Node Binding Table`: each node's evidence, dependency, verification status, judgment, fallback, and output.
- `Runtime Availability`: whether the target Agent runtime can invoke each matched dependency.
- `Dependency Bootstrap Plan`: the minimal set of platform Skills/CLI/API/adapters required by the current SOP, plus install/auth/preflight/verification status.
- `Completeness Score`: readiness before generation.
- `Full SOP Confirmation Canvas`: final user-facing Mermaid flow containing each node's data, judgment, output, and gaps.
- `单次执行检查结果`: one generated-Skill invocation result, including entrypoint, input payload, executed path, dependency blockers, and report-rendering status.
- `Trial Run Cases`: expected route, required paths, optional paths, expected output, and blockers.
- `Report Contract`: default and user-adjusted diagnosis report template, summary length, required sections, owner/action policy, unknowns, dependency gaps, and out-of-scope handling.
- `批量验证计划`: grouped real-verification calls to run during trial run, representative results if already collected, unverified nodes, literal failures, and all-required readiness.
- `Node Completion Gate`: per-node proof that the matched dependency, real verification result, returned fields, and judgment evaluation are all present; otherwise the node remains incomplete or blocked.
- `Adapter Onboarding Contracts`: missing external Skill/CLI/API/script interfaces needed for future installation.
- `Loadability Contract`: official dependency policy, third-party auth contracts, single exposed entrypoint, packaged internal orchestration, and alert-Agent blockers.
- `Admission Contract`: reserved quality/evaluator gate; separate from single execution check and trial-run pass/fail.

## Source Discipline

Every diagnosis node must have a source:

- `user_supplied`: directly stated by user.
- `artifact_derived`: extracted from alert, rule, dashboard, SOP doc, trace, RCA case, or link.
- `builder_suggested`: suggested but not accepted; do not compile as runtime logic.
- `accepted_suggestion`: explicitly accepted by user; may be compiled.

Do not prefill parse, false-alarm, change, metric-breakdown, report, or trial-run paths. These are optional node patterns only if the user says so, an artifact requires them, or the user accepts the suggestion.

## Scene Card

Use a compact Scene Card early and update it as context lookup succeeds. The default user-facing card should be short:

```text
我确认到的场景：
- 告警/指标：...
- 服务/业务线：...
- 触发规则：...
- 目前缺的：排障路径和每步证据
```

Use a detailed table only when comparing multiple candidates or debugging extraction quality.

Ask for corrections after the card. Do not move deep into SOP binding until the user confirms the Scene Card or provides enough corrections to proceed.

## Dependency And 验证

For dependency matching, read:

- `references/platform-capability-registry.yaml`
- `references/dependency-map.md`
- `references/capability-execution-contract.md`

Rules:

- The user should not know Skill/CLI names.
- Match dependencies from evidence needs.
- Discover whether the target Agent runtime can invoke the dependency.
- Creation-time checks are lightweight preflight only: dependency availability, auth/install state, stable input parsing, and optional cheap sample call.
- Full node verification belongs to trial run unless the user explicitly asks to run it during creation.
- 验证 only read-only capabilities unless the user explicitly designs a controlled action path.
- Mark `runtime_executable` only when a trial-run verification returns usable fields for the node judgment.
- Mark `blocked` for auth/install/permission/runtime/input blockers.
- Mark `missing` when no official capability is available.

## Visualization

Read `references/visualization-templates.md` before showing diagrams.

Use visual artifacts to carry the interaction. Prefer a compact card or Mermaid diagram over a raw text/code block when the user needs to confirm a scene, flow, branch, or node binding.

Example uncertainty markers:

- `⚠️ 我理解这几个方向是并行排查，对吗？`
- `⚠️ 我推断这里有两个出口：A -> Step 3，B -> Step 4，对吗？`
- `⚠️ 这个节点还没有数据绑定，先标记为待补充。`

## Output Style

In each turn:

1. Say only the useful result, not the Agent's thinking path.
2. Show at most one user-facing artifact: compact Scene Card, diagnosis flow, or one node evidence card. The artifact should be visual/scannable, not a raw text dump.
3. Ask one focused next question.
4. Never claim a data source is usable for runtime judgment unless real data was fetched or executed, and the required fields were returned. During creation, say "已配置待试运行验证" instead of "已验证可执行" when only the contract was captured.

Keep the interaction grounded in visible artifacts. Avoid long abstract explanations, progress bookkeeping, and debug/status records.

Default display priority:

1. If the user is creating/confirming the scene, show a compact Scene Card.
2. If the user is describing SOP, show the diagnosis flow.
3. If the user is binding data, show one node evidence card plus the updated flow snippet.
4. If the user asks about reliability, show compact proof and the one blocker that changes the next action.
5. If the user asks about Builder status, show a short phase checklist.

Forbidden in normal Builder conversation:

- Long tables with `Source`, `Status`, `Dependency`, `验证`, `Returned Fields`, or `Completeness`.
- Mermaid diagrams of the Builder's own creation lifecycle.
- Raw code-block flow lists such as `告警触发 -> Step 1 -> Step 2 -> ...` when a Mermaid diagnosis flow would be clearer.
- Multiple artifacts in one response.
- Explaining every internal attempt, retry, or failed verification.
- Exposing command counters, explored-file counts, "正在运行 ..." tool traces, or log pointer/verification details in the normal conversation.
- Asking the user to confirm obvious platform details already fetched from real tools.
