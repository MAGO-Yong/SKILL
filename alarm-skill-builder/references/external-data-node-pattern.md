# External Data Node Pattern

Use this pattern whenever a diagnosis node needs data that is outside the user's plain SOP text: another platform, a dashboard panel, a SQL-like query, an internal API, an existing Skill/CLI, or a custom script.

The Builder must stay generic. Do not promote a single business case, table, CLI, or platform into the universal flow. Treat concrete platforms as adapters behind the same node-binding contract.

## What The Builder Must Discover

For every external-data node, guide the user to confirm these fields:

| Area | Ask For | Why It Matters |
| --- | --- | --- |
| Business question | What this step decides | Keeps the node business-facing |
| Data source | Dashboard, platform, API, SQL, Skill, CLI, file, manual source | Determines adapter type |
| Locator | URL, panel, metric, table, query, API endpoint, script path, service, trace id | Makes the node reproducible |
| Time scope | Alert window, yesterday, WoW, fixed window, event time offset | Aligns diagnosis with alert |
| Filters/dimensions | Service, app, version, experiment, region, user, owner, upstream/downstream | Enables drilldown |
| Judgment rule | Threshold, existence, diff, overlap, concentration, checklist | Converts data into conclusion |
| Returned fields | Fields needed to apply the rule | Defines verification success |
| Failure policy | Empty data, auth failure, timeout, missing field | Required for unattended runtime |
| Runtime adapter | Existing Skill, CLI, generated script, API wrapper, manual placeholder | Defines generated Skill implementation |

Ask for the minimum missing field needed to make the node stable. Do not ask the user to design the whole adapter at once.

## Adapter Types

Use this neutral taxonomy instead of business-specific labels:

| Adapter | Use When | Generated Artifact |
| --- | --- | --- |
| `existing_skill` | An installed Skill can fetch the needed fields | Skill invocation contract |
| `official_cli` | A CLI exists, is installed, and supports non-interactive output | CLI command template |
| `generated_script` | Query templates, joins, normalization, retries, or post-processing are needed | `scripts/atomic/<node>.py` |
| `official_api` | Platform has a stable documented API but no Skill wrapper | API wrapper with auth contract |
| `dashboard_read` | Only a dashboard/panel URL exists | Panel locator plus extraction limitation |
| `manual_placeholder` | No runtime-capable dependency exists yet | Interface stub and report gap, never a hidden substitute for execution |

## Conversation Shape

Good flow:

1. Capture the node in business language.
2. Ask what data proves or disproves that node.
3. Parse any provided URL/table/query/API/script into a locator.
4. Match the most likely adapter silently.
5. Run only lightweight preflight if it is cheap and necessary; otherwise defer real-data verification to trial run.
6. Show a compact evidence card with the business signal, locator, rule, and one missing field.
7. Store adapter details and trial-run verification tasks internally for package generation.

Do not show raw dependency tables unless the user asks to debug the Builder.

## Evidence Card

Use this card for any external-data node:

| 要判断 | 数据来源 | 定位方式 | 判断条件 | 运行方式 |
| --- | --- | --- | --- | --- |
| `<business question>` | `<platform/dashboard/API/SQL/script>` | `<url/panel/query/endpoint/path>` | `<baseline/operator/threshold>` | `<Skill/CLI/script/API/manual>` |

Then ask:

```text
还缺一个信息：<the single field needed for runtime stability or trial-run verification>。
```

## Real-Data Verification Contract

During creation, a node can be `configured_for_trial` after the Builder captures the adapter, locator, expected fields, judgment rule, and failure policy.

A node is `runtime_executable` only after trial run performs a real read-only verification proving that:

- the adapter can be invoked in the current runtime;
- auth and permissions are sufficient;
- output is parseable;
- returned fields include the fields required by the judgment rule;
- the judgment can be evaluated or at least read-only verified against returned data.

If a lightweight preflight only proves reachability, mark it `verified` or `configured_for_trial`, not `runtime_executable`.

For many similar external-data nodes, create a deferred 批量真实验证 plan:

- creation-time preflight may prove adapter reachability;
- trial-run all-required verification proves runtime readiness;
- untested nodes remain `not_verified`;
- exact-text failures remain blocked until the user approves a fix or marks the node manual.

## Custom Script Contract

When the user needs custom logic or repeated queries, generate a local wrapper script instead of embedding ad hoc commands in prose.

Every generated script should expose:

```text
inputs: alert_time/window + node-specific filters
outputs: rows/features + judgment_result + evidence_summary + raw_locator
errors: auth_failed/query_failed/empty_data/missing_fields/timeout
```

Prefer JSON output so the alert Agent can load the Skill without human interpretation.

## Missing Adapter Onboarding

If the adapter is absent, keep the node useful by defining the missing adapter contract:

```text
adapter: <name>
invocation: <skill/cli/api/script>
inputs: <values from alert or upstream nodes>
outputs: <fields needed by judgment>
auth/runtime: <permission or install requirement>
failure: <continue/stop/unknown>
```

Do not claim this node is runtime executable until the adapter is installed and verified in the target Agent runtime. A manual placeholder is a visible capability gap, not a lower-quality execution path.

## Runtime Questions

Ask these only when they affect generated behavior:

```text
这个节点在告警触发时必须自动跑吗，还是只作为人工参考？
```

```text
查不到数据时，是继续生成未知结论，还是终止整个诊断？
```

```text
这个数据源是否需要把查询封装成脚本，还是直接调用已有 Skill/CLI 就够？
```
