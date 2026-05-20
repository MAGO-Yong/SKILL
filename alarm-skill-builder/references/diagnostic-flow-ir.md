# Diagnostic Flow IR

Use this intermediate representation as the source of truth while incubating an alert diagnosis Skill.

The IR must start empty. Do not prefill diagnosis nodes such as alert parsing, false alarm filtering, change checks, metric breakdown, or report generation unless the user asks for them, a concrete artifact requires them, or the user accepts them as Builder suggestions.

## Empty IR

```yaml
flow_id: pending_diagnosis_skill
name: ""
scene_card:
  service_or_system: ""
  trigger_type: ""
  core_anomaly: ""
  severity: ""
  known_artifacts: []
  missing_fields: []
  status: draft
trigger:
  alert_ids: []
  alert_titles: []
  metrics: []
  business_domain: ""
runtime_contract:
  non_interactive: true
  no_fake_data: true
  execution_policy:
    mode: decision_tree|run_all_paths|stop_on_first_root_cause|enrichment_only|unknown
    ask_user_at_runtime: false
    continue_on_partial_failure: true|false|unknown
  input_contract:
    required_fields: []
    optional_fields: []
    default_time_window: ""
    time_zone: ""
  preservation_constraints:
    literal_queries: false
    case_sensitive: false
    do_not_rewrite: []
  dispatch_policy:
    type: single_path|route_table|multi_path|unknown
    fallback_path: ""
nodes: []
edges: []
open_questions:
  - "这个 Skill 的业务排障场景是什么？"
context_lookup:
  attempts: []
  blockers: []
artifact_ingestion:
  source_documents: []
  extracted_constraints: []
  extracted_gaps: []
  source_confidence: ""
batch_verification:
  strategy: representative_first|all_required_before_package|none
  groups: []
  summary:
    exact_verification_success: 0
    exact_verification_failed: 0
    not_verified: 0
    blocked: 0
dependency_bootstrap:
  minimal_required: []
  optional: []
  by_dependency: []
  summary:
    installed: 0
    missing: 0
    auth_ready: 0
    auth_blocked: 0
    verification_success: 0
    verification_blocked: 0
loadability:
  package_complete: false
  official_dependency_only: true
  flattened_entrypoint: false
  auth_contracts: []
  blockers: []
final_sop_canvas:
  status: not_shown|shown|confirmed|needs_edit
  diagram_format: mermaid
  must_include:
    - all_confirmed_nodes
    - edges_and_branches
    - data_source_per_node
    - judgment_condition_per_node
    - output_per_node
    - missing_or_blocked_items
  user_feedback: []
execution_check:
  status: not_run
  input_kind: historical|discovered|synthetic|null
  entrypoint_loaded: false
  input_parsed: false
  route_selected: ""
  report_rendered: false
  blockers: []
  next_action: ""
trial_run:
  cases: []
admission:
  skill_evaluator:
    status: placeholder
```

## Node Schema

```yaml
id: step_001
source: user_supplied|artifact_derived|builder_suggested|accepted_suggestion
type: data_check|decision|transform|lookup|report|gate|manual_context|unknown
status: draft|needs_confirm|confirmed|verified|configured_for_trial|runtime_executable|blocked|missing|placeholder
purpose: ""
evidence_needed:
  - kind: metric|dashboard|business_data|log|sql|external_api|script|trace|change|release|capacity|metadata|case|experiment|attribution|alert|document|manual_context
    value: ""
    business_signal: ""      # user-facing signal being judged by this node
    source_locator:
      url: ""
      dashboard_id: ""
      panel_id: ""
      panel_index: null
      panel_title: ""
      query: ""
      filters: {}
    time_window: ""
    baseline: ""             # previous window / same time yesterday / WoW / fixed threshold / user-defined
    extraction_method: ""    # Skill / CLI / API / SQL / generated script / query link / browser panel read / manual
    preservation:
      literal: false          # true when query/script/text must be used exactly as supplied
      original_text: ""
      approved_runtime_text: ""
      rewrite_allowed: true|false|unknown
    required_returned_fields: []
    dynamic_outputs: []       # values passed to later nodes, e.g. abnormal_period, channel_name, index_name
inputs: []
route_binding:
  match_fields: []           # monitor/title/measurement_name/path keyword/etc.
  match_values: []
  path: ""
  fallback: false
sub_paths:
  - id: ""
    name: ""
    required: true
    run_policy: always|on_condition|optional
    top_n: null
dependency_candidates:
  - id: <capability id from platform-capability-registry.yaml>
    status: candidate|verified|configured_for_trial|runtime_executable|blocked|missing|forbidden
    matched_need: ""
    safety: read_only|mixed|action
    expected_inputs: []
    expected_outputs: []
    runtime_availability:
      available_in_current_agent: true|false|unknown
      invocation_method: skill|cli|plugin|api|generated_script|manual|not_available
      auth_state: ready|missing|unknown|failed
      install_state: installed|missing|unknown
      verification_allowed: true|false
      blocker: ""
    verification:
      verification_status: planned|success|blocked|failed|exact_verification_success|exact_verification_failed|not_verified
      returned_fields: []
      missing_fields: []
      judgment_test:
        rule: ""
        result: true|false|null
      literal_failure:
        error: ""
        user_decision: keep_original_blocked|approve_fix|manual_gap|pending
        candidate_fix: ""
    onboarding_contract:
      adapter_name: ""
      invocation: ""
      required_inputs: []
      expected_outputs: []
      auth_runtime: ""
      install_source: ""
      failure_policy: ""
    bootstrap:
      required_or_optional: required|optional
      required_by_nodes: []
      install_state: installed|missing|unknown
      install_source: ""
      install_action: ""
      invocation_method: skill|cli|api|adapter|manual|unknown
      command_or_entrypoint: ""
      non_interactive: true|false|unknown
      auth_state: ready|missing|unknown|failed
      identity_source: ""
      permission_check: ""
      call_authorization: ""
      preflight_status: not_run|success|blocked|failed
      fallback_behavior: block_node|mark_unknown|manual_gap|skip_optional
judgment:
  type: threshold|existence|overlap|diff|concentration|owner_match|checklist|manual|unknown
  rule: ""
  operator: ""               # >, >=, <, <=, contains, exists, overlaps, etc.
  threshold: ""
  missing_data_policy: ""    # continue / skip / manual_confirm / stop / unknown
on_success: ""
on_failure: ""
on_unknown: ""
fallback: ""
completion_gate:
  capability_matched: false
  input_resolved: false
  real_verification_ran: false
  required_fields_returned: false
  judgment_evaluated: false
  failure_policy_set: false
  configured_complete: false
  blocker: ""
```

## Edge Schema

```yaml
from: step_001
to: step_002
condition: success|failure|unknown|always|<user-defined>
source: user_supplied|artifact_derived|builder_suggested|accepted_suggestion
```

## Source Discipline

- `user_supplied`: directly stated by the user.
- `artifact_derived`: extracted from a real alert, dashboard, SOP doc, trace, RCA case, or link.
- `builder_suggested`: suggested by Builder but not accepted. Do not compile as mandatory runtime logic.
- `accepted_suggestion`: explicitly accepted by the user. May be compiled into the Skill.

## Runtime Contract Notes

Set runtime properties only when known:

```yaml
runtime_contract:
  non_interactive: true
  no_fake_data: true
  execution_policy:
    mode: ""                # decision_tree / run_all_paths / stop_on_first_root_cause / enrichment_only / unknown
    ask_user_at_runtime: false
    continue_on_partial_failure: null
  input_contract:
    required_fields: []      # e.g. alert_time, alert_id, service
    optional_fields: []
    default_time_window: ""
    time_zone: ""
  preservation_constraints:
    literal_queries: false
    case_sensitive: false
    do_not_rewrite: []
  required_paths: []       # only user-confirmed required paths
  optional_paths: []       # optional enrichment paths
  parallel_paths: []       # paths that may run concurrently
  stop_conditions: []      # user-confirmed stop rules
  route_table: []          # alert payload or measurement -> path, for multi-scenario Skills
  fallback_path: ""        # default path for unmatched/ambiguous payload
  sub_path_policy: ""      # run_all / stop_on_first_hit / conditional / unknown
  error_policy:
    auth_failed: ""
    query_failed: ""
    empty_data: ""
    timeout: ""
```

Do not assume all Skills must run all paths. Some diagnosis Skills stop on first confirmed root cause; some require all paths; some only enrich a report. Ask or infer from user-confirmed SOP.

When a document says "一查到底" or "不用人工确认", store it as non-interactive runtime behavior first. Only set `mode: run_all_paths` when the document or user explicitly says all branches/sub-paths must execute.

## Evidence Binding Notes

Do not compile brittle evidence bindings into runtime logic when a stable business signal is missing.

Examples:

- Acceptable draft: "某大盘第 N 个 panel，阈值 X%。"
- Not yet executable: same as above without `business_signal`, `baseline`, and `missing_data_policy`.
- Executable-ready: "大盘链接，panel id/title 已确认，business_signal 已确认，baseline=告警前同长窗口，judgment=drop_rate > X%，missing_data_policy=continue_unknown。"

Evidence kind should reflect the data class, not only the tool. A troubleshooting node may be backed by dashboard metrics, business reports, logs, traces, deployment/change records, experiment configs, attribution data, RCA cases, documents, custom scripts/APIs, or manual context.

For SQL-like/API/scripted paths, store the source locator, query or endpoint template, required inputs, filters, aggregation dimensions, returned fields, post-processing, judgment rule, and failure policy. Do not reduce them to a vague phrase such as "查日志" or "查平台数据".

For dashboard/panel paths, do not stop at a visual locator. Store the parsed dashboard/panel locator, the resolved metric/query, the baseline, and the judgment rule. A panel index plus threshold is a draft locator, not executable runtime logic.

For literal-query artifacts, store the original query exactly and set `rewrite_allowed: false`. If the literal query fails during verification, report the original query failure as a blocker; do not silently repair it.

For dynamic nodes, store emitted values and consumers. Examples:

- `step_1` emits `abnormal_period`, consumed by `step_2_to_6`.
- `recall_channel_check` emits `channel_name`, consumed by root-cause queries.
- `index_pool_check` emits `index_name`, consumed by an index-switch script.

## Batch 验证 Notes

When a document contains many queries, avoid a binary "all executable" claim.

```yaml
batch_verification:
  strategy: representative_first
  groups:
    - adapter: xray-metric-query
      datasource: vms-recommend
      representative_nodes: [step_1_1h_ratio]
      required_nodes: [step_1_1h_ratio, step_1_24h_ratio, step_2_phase, step_3_recall_channel]
      status: partial
  summary:
    exact_verification_success: 1
    exact_verification_failed: 0
    not_verified: 3
    blocked: 0
```

## Dependency Bootstrap Notes

Installing the Builder Skill does not install all platform dependencies listed in the registry. The IR must track the minimal dependency set needed by the current SOP and whether each dependency is actually available in the current runtime.

Use `dependency_bootstrap.minimal_required` for dependencies required by confirmed runtime nodes. Use `dependency_bootstrap.optional` for enrichment-only checks that can be skipped or reported as unknown.

Do not mark a generated Skill loadable when a required dependency has:

- missing install source;
- unknown or failed auth;
- interactive-only invocation;
- no declared input/output contract;
- no failure policy.

## Completion Gate Notes

`status: configured_for_trial` and `completion_gate.configured_for_trial: true` require stable inputs, expected outputs, judgment rule, failure policy, and a deferred trial-run verification task. `status: runtime_executable` requires real verification plus judgment in trial run. The Builder may generate a draft Skill before runtime verification, but unverified nodes must be listed as `trial_run_required`, `dependency_gaps`, `manual_gaps`, or `blocked_runtime_nodes`, not hidden as production-ready executable steps.

Examples:

- `representative verification success` + sibling queries not run -> datasource entrance verified, sibling nodes remain configured for trial rather than runtime executable.
- `query returns rows` + threshold not evaluated -> verification succeeded, node remains incomplete.
- `dashboard link parsed` + panel query unavailable -> input not resolved, node remains blocked or needs user input.
- `custom script named` + no install/auth/runtime contract -> missing adapter, not loadable.

Generation readiness should distinguish:

- "can draft package"
- "single execution check passed"
- "configured for trial run"
- "trial run passed all required queries"
- "admission-ready"

## Missing Adapter Onboarding Notes

For missing dependencies, store an onboarding contract so future capability installation can connect cleanly:

```yaml
onboarding_contract:
  adapter_name: index-switch-check
  invocation: "python3 skills/index-switch-check/scripts/check_switch.py <name>"
  required_inputs:
    - name
  expected_outputs:
    - switch_status
    - reason
  auth_runtime: "unknown"
  failure_policy: "mark dependency gap and continue report"
```

## Report Contract

Generated diagnosis Skills should declare a report contract before packaging:

```yaml
report_contract:
  template_version: default_v1|custom
  root_cause_summary:
    max_chars: 100
    style: concise
    certainty_policy: confirmed|likely|unknown_allowed
  sop_step_conclusions:
    format: list|table|json
    required_fields:
      - step_name
      - conclusion
      - key_evidence
      - status
  terminology:
    explain_abbreviations: true
    avoid_unexplained_jargon: true
    glossary_max_items: 5
  unknowns:
    include: true
  dependency_gaps:
    include: true
  suggested_next_actions:
    include: true
    include_owner: optional
  must_include:
    - scene_summary
    - trigger_time_or_window
    - root_cause_summary
    - sop_step_conclusions
    - terminology_if_needed
    - executed_path
    - key_evidence
    - conclusion
    - confidence_or_unknowns
    - dependency_gaps
    - recommended_owner_or_next_action
  must_not_include:
    - fabricated_data
    - hidden_manual_confirmation
    - unverified_dependency_claimed_executable
```

## Alert Agent Loadability

Generated diagnosis Skills must be delivered as one complete and independently callable capability for the alert Agent.

```yaml
loadability:
  package_complete: true|false
  official_dependency_only: true|false
  flattened_entrypoint: true|false
  exposed_entrypoint:
    name: diagnose
    input_schema: {}
    output_schema: {}
  internal_orchestration:
    hidden_from_caller: true
    packaged_dependencies: []
  auth_contracts:
    - dependency_id: ""
      platform: ""
      identity_source: ""      # agent identity / service account / platform token / user token
      authentication: ""
      permission_check: ""
      call_authorization: ""
      secret_runtime: ""
      failure_policy: ""
  blockers: []
```

Loadability is different from local verification success. A Skill may run in the creator's Codex environment but still be blocked for alert Agent loading if dependencies are local-only, hidden, unauthenticated, or not packaged behind the generated Skill entrypoint.

## Completeness Fields

```yaml
completeness:
  scene_card:
    status: draft|confirmed
    score: 0
  sop_structure:
    confirmed_nodes: 0
    total_nodes: 0
    score: 0
  data_binding:
    bound_nodes: 0
    total_nodes: 0
    score: 0
  final_sop_canvas:
    status: not_shown|shown|confirmed|needs_edit
    score: 0
  trial_verification:
    configured_for_trial: 0
    runtime_executable: 0
    blocked: 0
    missing: 0
    score: 0
  trial_run_material:
    status: missing|partial|ready
    score: 0
  total_score: 0
  next_best_action: ""
```
