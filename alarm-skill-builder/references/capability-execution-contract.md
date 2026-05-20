# Capability Execution Contract

The Builder must distinguish creation-time readiness from trial-run execution for every external-data SOP node:

1. `matched`: It knows which Skill/CLI should handle the node.
2. `verified`: It parsed concrete user input and confirmed the dependency interface can support the node.
3. `configured_for_trial`: It has stable inputs, expected outputs, judgment rule, and failure policy, but has not necessarily fetched real data yet.
4. `runtime_executable`: It actually fetched data or successfully ran a read-only verification in the target runtime and returned fields usable for judgment.
5. `blocked`: The dependency exists but auth, permission, missing input, missing install, network, or runtime errors prevent execution.

Do not describe a dependency as runtime executable unless level 4 happened. During creation, prefer "已配置，待试运行验证".

## Verification Timing Policy

Builder creation should optimize for fast, correct Skill incubation, not full diagnosis execution.

Creation-time default:
- match the platform capability;
- parse stable inputs and locators;
- capture expected returned fields, judgment rule, and failure policy;
- check install/auth/runtime availability when cheap;
- run at most one cheap read-only preflight per dependency or datasource when it prevents an invalid package.

Defer to trial run:
- full batch metric/log/trace/change/API queries;
- exact verification for many literal PromQL/SQL/script nodes;
- expensive time-window scans;
- judgment execution across every required branch;
- alert-Agent loadability proof.

Run heavier verification during creation only when the user explicitly asks, when the node is a single cheap lookup, or when a missing/invalid result would change the generated package structure.

## Node Completion Gate

For an SOP node to be "configured for trial run", all of these must be true:

1. `capability_matched`: the Builder selected a real official platform Skill/CLI/API, or a user-approved adapter contract for a custom platform/script.
2. `input_resolved`: the node has concrete runtime inputs, such as metric query, dashboard panel id/title, service, trace id, SQL/API parameters, time window, baseline, and filters.
3. `expected_fields_declared`: the node declares the fields required by the judgment.
4. `judgment_rule_captured`: the user-approved rule is captured, including baseline and threshold logic where applicable.
5. `failure_policy_set`: empty data, timeout, auth failure, and missing-field behavior are explicit.
6. `trial_verification_planned`: the generated Skill package records how trial run will fetch real data and evaluate the rule.

Only nodes that pass these six checks may be presented as "已配置，待试运行验证".

For an SOP node to be "runtime executable", all configured-for-trial checks must pass, and:

1. `real_verification_ran`: trial run actually invoked the matched capability or adapter in read-only mode against the provided input in the target Agent runtime.
2. `required_fields_returned`: the result contains the fields required by the node judgment, not merely a success status.
3. `judgment_evaluated`: the user-approved rule was run against the returned data.

Only nodes that pass runtime execution checks may be presented as "已验证可执行".

These are incomplete states and must stay visible as incomplete when they affect generation:

| State | Meaning | User-facing wording |
| --- | --- | --- |
| `matched` | likely dependency found | "已匹配候选平台能力，尚未取数" |
| `verified` | interface/input shape checked | "调用方式可行，待试运行取数" |
| `configured_for_trial` | inputs, fields, judgment, and failure policy captured | "已配置，待试运行验证" |
| `representative verification only` | one query proves the datasource entrance | "入口可用，不代表该节点完成" |
| `not_verified` | required runtime query/script was not executed | "未完成配置：待真实验证" |
| `verification_success_no_judgment` | data returned but no rule evaluation | "已取数，判断规则还没跑通" |
| `blocked` | auth/install/input/runtime failure | "配置阻塞：需要补权限/依赖/输入" |

The Builder must keep incomplete states explicit in the conversation and in the generated Skill package. Do not imply that an incomplete node is ready for unattended runtime execution.

This contract applies to metrics, logs, traces, alert details, release records, change events, capacity, HA metadata, RCA cases, experiment configs, custom SQL/API/script adapters, and any future platform data used by a diagnosis SOP.

## Universal Real-Data Verification Record

Represent each concrete test like this:

```yaml
verification_check:
  node_id: <node_id>
  node_data_need: <metric|log|trace|change|release|capacity|metadata|case|experiment|alert|external_api|script|sql>
  user_input:
    raw: ""
    parsed:
      service: ""
      metric_name: ""
      dashboard_url: ""
      trace_id: ""
      log_keyword: ""
      alert_id: ""
      release_url: ""
      experiment_id: ""
      time_window: ""
      judgment_rule: ""
  dependency_id: <capability id>
  verification_intent: ""
  required_fields: []
  optional_dimensions: []
  status: planned|success|blocked|failed|exact_verification_success|exact_verification_failed|not_verified
```

## Verification Types

| Data Need | Typical Dependency | Concrete Inputs | Required Returned Fields | Judgment Examples |
| --- | --- | --- | --- | --- |
| alert detail/rule | xray-alarm | alert_id, event_id, rule_id, title | alert_title, trigger_condition, service, time | title matches metric, rule recently changed |
| metric trend/breakdown | xray-metric-query, xray-cli | metric_name, dashboard_url, PromQL, tags | current_value, baseline_value or time_series | drop_ratio > 5%, one dimension differs > 3% |
| log evidence | xray-log-query, xray-cli log query | service, keyword, trace_id, user_id, time_range | log_rows, count, timestamp, message | error_count doubles, specific error appears |
| trace search | xray-trace-search | service, endpoint, ERROR/SLOW mode | trace_list, span groups, latency | slow traces concentrate on one downstream |
| single trace | xray-single-trace-analysis, xray-logview-analysis | trace_id, message_id | abnormal_spans, slow_spans, dependency_health | root span error exists, downstream timeout |
| AI trace | xray-ai-trace-analysis | Langfuse trace_id/session_id | ai_call_graph, token_cost, model_latency | one model call latency spikes |
| topology | xray-topology | service, endpoint, mode | upstream_services, downstream_services, qps, latency | downstream success rate drops |
| release/deploy/pod | ones-assistant | service, app, deploy_group, env, time_range | release_history, image_version, pod_status | release overlaps alert window, pod restart spikes |
| change event | query_change | service, app, owner, change window | change_events, change_type, change_owner | config/strategy change overlaps alert window |
| capacity | honghu-capacity-query | service, region, time_range | capacity_waterline, limit_qps, buffer_remaining | buffer below threshold, QPS near limit |
| HA metadata | stability-metadata | business line, scene, service | owners, core_services, emergency_contacts | owner exists, scene maps to core service |
| plan/prevention | ha-plan | root_cause, scene, service | matched_plans, degrade_actions | plan matches diagnosed root cause |
| RCA case | rca-case-query | keyword, business_line, fault_type | rca_cases, known_causes, prior_actions | similar case exists with same symptom |
| experiment config | experiment-platform-query | experiment_id, bucket_id, app, scene | bucket_ratio, owner, effective_time | abnormal group maps to active experiment |
| external platform/API | official Skill/API or generated adapter | URL, endpoint, query, auth context, time range | required fields declared by node judgment | returned fields satisfy rule |
| custom script/SQL | official CLI/API plus generated script | script inputs, query template, filters, time range | JSON rows/features, error code, judgment fields | threshold/diff/concentration/checklist passes |

## General Execution Rules

- Prefer read-only verifications.
- Do not run evidence verifications before the corresponding SOP node exists. Alert/rule lookup may identify the scene; logs, traces, changes, topology, capacity, RCA, and metric drilldowns require a user-supplied, artifact-derived, or accepted-suggestion node.
- Use the official Skill when available in the target Agent runtime.
- Use the official CLI only when it is installed, non-interactive, and can return parseable output.
- Before running a real-data verification, record runtime availability: target Agent Skill/tool availability, CLI install state, auth state, invocation method, and blockers.
- If the Skill/CLI cannot be invoked, record `blocked`; do not silently downgrade to a guessed API.
- If the user gives only a vague data need, keep dependency as `candidate` and ask for the minimum concrete input required for a verification.
- If returned data lacks fields needed for the judgment, set `verified` or `blocked` with `missing_fields`; do not mark runtime executable.
- If a node has a judgment rule, run it against sample data whenever possible.
- If a node has no numeric threshold, use the appropriate judgment type: existence, overlap, diff, concentration, owner match, checklist, or route confidence.
- For business-domain metrics such as revenue, order, success-rate, conversion, or efficiency metrics, do not assume XRay can provide the metric. If XRay cannot, use a confirmed business data platform capability, an official API/CLI, or a generated adapter around a user-confirmed query; otherwise mark `business-data-query` as missing.
- If an artifact requires literal PromQL/SQL/script text, do not normalize, optimize, reformat, or repair it without explicit user approval. Use the exact text for verification. If exact text fails, mark the node blocked by literal-query failure.
- If a judgment references a variable that should come from an earlier node, such as abnormal time window, channel name, reason type, index name, or owner, verify that the upstream node emits that field before marking the downstream node runtime executable.
- If a document states a conclusion but provides no evidence source, keep the conclusion as a report suggestion or manual gap. Do not compile it into automated judgment.

## Batch Verification Rules

For SOP artifacts with many queries:

- Group verifications by adapter and datasource.
- First run a representative read-only verification per group to validate basic access.
- Before claiming package runtime readiness, run every required query/script/API call that will execute unattended.
- Keep `not_verified` distinct from `blocked` and `failed`.
- If literal query mode is required, every verification must use exact artifact text.
- A representative verification may only set `datasource_access_verified=true`; it must not upgrade sibling nodes to `runtime_executable`.
- A node with `not_verified`, `exact_verification_failed`, missing adapter, or missing judgment result cannot be compiled as unattended runtime logic. It can only be included as a draft/manual gap/blocker.

Readiness wording:

| State | Meaning | Allowed claim |
| --- | --- | --- |
| representative verification only | at least one query per adapter/datasource works | "入口已验证" |
| all required verification success | every required runtime query succeeds | "数据节点已通过试运行验证" |
| some queries not verified | query exists but not tested | "可生成草稿，需补真实验证" |
| exact verification failed | literal query failed | "原样查询阻塞" |

## Dashboard And Panel Binding

When the user gives a dashboard or panel link, the Builder must try to convert it into stable trial-run evidence:

```yaml
dashboard_binding:
  raw_url: ""
  parsed:
    dashboard_id: ""
    panel_id: ""
    panel_index: null
    panel_title: ""
    time_range: ""
  matched_capability: xray-metric-query|dashboard_api|browser_panel_read|missing
  extraction_verification:
    status: success|blocked|failed|not_verified
    query_or_metric: ""
    returned_fields: []
  judgment_verification:
    rule: ""
    baseline: ""
    result: true|false|null
  completion: complete|incomplete|blocked
```

Rules:

- Do not treat "第 N 个图表 + 5%" as complete. It is a locator draft until the Builder resolves the panel into a stable metric/query and evaluates the drop rule.
- If the dashboard API cannot expose panel query data, ask for the panel title, copied query, metric name, or query link.
- If the metric data can be fetched but the baseline is missing, ask for baseline before marking the node complete.
- If the judgment rule cannot be computed because returned fields are missing, mark the node `verification_success_no_judgment`.

## Literal Failure Handling

When exact query/script fails:

```yaml
literal_failure:
  original_text: "<artifact exact text>"
  error: "<verification error>"
  allowed_actions:
    - keep_original_blocked
    - propose_candidate_fix
    - convert_to_manual_gap
  user_decision: pending
```

If proposing a fix, label it as a candidate and wait for approval. Do not overwrite original artifact text.

## Missing Adapter Contract

For a missing Skill/CLI/API/script, collect:

```yaml
missing_adapter:
  adapter_name: ""
  invocation: ""
  required_inputs: []
  expected_outputs: []
  auth_runtime: ""
  install_source: ""
  failure_policy: ""
```

This lets the generated Skill expose a stable interface even before the adapter is installed.

## Runtime Availability Record

```yaml
runtime_availability:
  dependency_id: <capability id>
  available_in_current_agent: true|false|unknown
  invocation_method: skill|cli|plugin|api|generated_script|manual|not_available
  auth_state: ready|missing|unknown|failed
  install_state: installed|missing|unknown
  verification_allowed: true|false
  blocker: ""
```

Creation-time status mapping:

- Dependency known + inputs/outputs/judgment/failure policy captured -> `configured_for_trial`.
- Dependency known but input shape incomplete -> `verified` or `candidate`, depending on specificity.
- Available + auth/install/input blocked -> `blocked`.
- Capability exists in registry but not current runtime -> `blocked`.
- No official capability exists -> `missing`.

Trial-run status mapping:

- Available + auth ready + verification returns usable fields + judgment runs -> `runtime_executable`.
- Verification returns data but fields/judgment are incomplete -> `verified` with missing field details.

## Example: Metric Query

User says: "第二步需要查询某个业务指标，并且判断跌幅大于 X% 就是异常。"

```yaml
id: business_metric_check
type: data_check
purpose: 查询业务指标并计算相对跌幅
inputs:
  - metric_name: <business_metric_name>
  - time_window
  - baseline_window
dependency_candidates:
  - id: xray-metric-query
    status: configured_for_trial
    verification:
      input_type: metric_name|dashboard_url|promql
      parsed_metric: <business_metric_name>
      verification_status: planned
      expected_returned_fields: [current_value, baseline_value]
      judgment_rule: "(baseline_value - current_value) / baseline_value > 0.05"
```

## Example: Release And Change

User says: "查告警前 30 分钟有没有相关服务发布或配置变更。"

```yaml
id: release_change_check
type: data_check
purpose: 查询告警前 30 分钟发布和配置变更
dependency_candidates:
  - id: ones-assistant
    status: configured_for_trial
    verification:
      input_type: service_and_time_window
      verification_status: planned
      expected_returned_fields: [release_id, service, image_version, start_time, status]
      judgment_rule: "release.start_time within alert_time - 30m"
  - id: query_change
    status: blocked
    verification:
      verification_status: blocked
      reason: "RCM dependency unavailable in current runtime"
```

## Example: Logs

User says: "查某类业务事件日志，error 数超过平时两倍算异常。"

```yaml
id: tracking_log_check
type: data_check
dependency_candidates:
  - id: xray-log-query
    status: configured_for_trial
    verification:
      input_type: service_keyword_time_range
      verification_status: planned
      expected_returned_fields: [timestamp, level, message, count]
      judgment_rule: "error_count_current > error_count_baseline * 2"
```

## Example: Trace

User says: "如果 trace 里某个关键下游超时，就认为是下游链路问题。"

```yaml
id: recall_trace_check
type: data_check
dependency_candidates:
  - id: xray-single-trace-analysis
    status: configured_for_trial
    verification:
      input_type: trace_id
      verification_status: planned
      expected_returned_fields: [slow_spans, abnormal_spans, downstream_health]
      judgment_rule: "downstream service contains recall and latency > threshold"
```

## 验证 Result Summary

When the user asks for technical details, summarize verification results compactly:

| Node | Dependency | 试运行验证 | Expected Fields | Judgment Rule | Status |
| --- | --- | --- | --- | --- | --- |
| ctr_metric_check | xray-metric-query | planned | current_value, baseline_value | drop_ratio > 5% | configured_for_trial |
| release_change_check | ones-assistant | planned | release_history | overlap alert window | configured_for_trial |

For blocked nodes:

| Node | Dependency | 验证 | Blocker | Next Needed | Status |
| --- | --- | --- | --- | --- | --- |
| change_check | query_change | service + time window | dependency unavailable | install/connect official RCM skill | blocked |

## Generated Skill Runtime Contract

For every configured data node, the generated diagnosis Skill should contain:

```yaml
runtime_query:
  dependency_id: <capability id>
  inputs: {}
  expected_outputs: []
  judgment:
    type: threshold|existence|overlap|diff|concentration|owner_match|checklist
    rule: ""
  error_handling:
    empty_data: "mark data gap and continue required paths"
    auth_failed: "stop calls to this dependency and report auth blocker"
    timeout: "record timeout and continue independent paths"
    missing_fields: "mark node blocked or verified but not runtime_executable"
```

## Literal Query Example

Artifact says: "全程严格使用文档原样 promql，不改动任何大小写。"

```yaml
runtime_query:
  dependency_id: xray-metric-query
  inputs:
    pql_original: "<exact artifact text>"
    datasource: vms-recommend
  preservation:
    literal: true
    rewrite_allowed: false
  error_handling:
    invalid_query: "report original query failed; do not auto-repair"
```

## Dynamic Output Example

```yaml
node_outputs:
  step_1:
    emits:
      - abnormal_period_start
      - abnormal_period_end
      - strongest_drop_period
  step_5_0:
    emits:
      - index_or_channel_name
downstream_inputs:
  step_2_to_6:
    time_window: from step_1.abnormal_period
  index_switch_check:
    name: from step_5_0.index_or_channel_name
```
