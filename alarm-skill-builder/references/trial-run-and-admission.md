# Execution Check, Trial Run, And Admission

Generated diagnosis Skills must not go directly from creation to production loading. After package generation, the Builder should first execute the generated Skill once when possible. Heavy real-data verification and admission quality evaluation are separate later gates.

## One Execution Check

This step answers: "Can the generated Skill actually be invoked and produce a diagnosis report shape?"

It is not the same as admission evaluation and it is not necessarily full real-data verification.

Run it immediately after package generation when the current runtime can invoke the generated Skill. Use one of:

- a historical alert payload supplied by the user;
- the alert/rule payload already discovered during Scene Card lookup;
- a synthetic payload generated from the confirmed input schema, clearly labeled as synthetic.

Execution-check checklist:

- The generated Skill entrypoint can be loaded.
- Required input schema can be parsed.
- Routing selects the expected diagnosis path.
- Required dependency calls are either invoked in read-only mode, skipped by configured policy, or reported as explicit dependency gaps.
- Dynamic variables can be passed between nodes if they are available.
- The Skill produces the agreed report skeleton.
- Missing permissions, missing dependencies, empty data, and unsupported nodes appear in the report as blockers/unknowns, not as fake conclusions.
- No runtime prompt asks the alert user to confirm something interactively.

Execution-check result:

```yaml
execution_check:
  status: passed|failed|blocked|not_run
  input_kind: historical|discovered|synthetic
  entrypoint_loaded: true|false
  input_parsed: true|false
  route_selected: ""
  report_rendered: true|false
  blockers: []
  next_action: ""
```

User-facing wording:

```text
我会先执行一次生成出来的 Skill，确认入口、路由和报告能跑通。这个只验证“能不能跑”，不代表质量准入通过。
```

## Trial Run

Prepare trial-run inputs before publication:

```yaml
trial_run:
  mode: historical_case_replay
  cases:
    - id: case_001
      name: "<来自用户或历史 case 的场景名>"
      trigger_payload: {}
      expected_route: "<generated-skill-name>"
      expected_paths: []      # only user-confirmed required paths
      optional_paths: []      # optional enrichment paths
      expected_report:
        must_include:
          - "<user-confirmed required output field>"
        must_not_include:
          - fabricated_data
          - ask_user_to_confirm_at_runtime
```

Trial-run checklist:
- Route from alert payload to Skill.
- Execute user-confirmed required paths without human interaction.
- For every required data node, prove the node completion gate: dependency matched, concrete input resolved, real verification ran, required fields returned, judgment evaluated, and failure policy set.
- Confirm execution policy: decision tree, run all paths, stop on first root cause, or enrichment-only.
- Confirm runtime input contract: required fields, default time window, timezone, and fallback when fields are absent.
- Resolve or mark dependencies.
- Preserve literal queries/scripts exactly when the source artifact requires it.
- Verify dynamic values are passed between nodes, such as abnormal time range, channel name, reason type, index name, or owner.
- Handle empty data, timeout, permission failure, and ambiguous evidence.
- Produce the user-confirmed output format with evidence.
- Preserve Scene Card context in trial output so the user can see which scenario was executed.
- Report all dependency gaps and manual-background nodes without claiming them runtime executable.
- Verify alert-Agent loadability: official dependencies, third-party auth contracts, one exposed entrypoint, packaged internal orchestration, and no hidden local-only dependency.
- Ensure no `not_verified`, representative-only, failed, or missing-adapter node is hidden inside the runtime executable path. Such nodes must appear as explicit gaps or blockers in the trial report.
- Run the deferred verification plan created by Builder: batch metric/log/trace/change/API calls, exact literal queries/scripts, judgment execution, and empty/error fallback checks.
- Keep creation-time preflight separate from trial-run proof. A node that was only "已配置，待试运行验证" during creation becomes "已验证可执行" only after trial run proves it.
- Keep execution check separate from trial-run proof. Execution check validates invocation and report shape; trial run validates data and judgment across the required case set.

Do not assume every Skill has parse, false-alarm, metric-breakdown, or final-report nodes. Trial-run expectations must come from the current IR.

## Alert Agent Loadability Checklist

Before saying a Skill can be loaded by the alert Agent, require:

- official CLI/Skill/API basis for every runtime executable dependency;
- auth contract for each third-party Skill/platform dependency;
- single exposed `diagnose` entrypoint with input and output schema;
- internal dependency orchestration packaged behind that entrypoint;
- no dependency that exists only in the creator's local environment;
- all non-executable/manual dependencies visible as report gaps, not hidden runtime calls.

Do not include publication logistics unless the user explicitly asks for release or publish workflow.

## Gate Separation

Keep these statuses separate:

| Gate | Question It Answers | Typical Output |
| --- | --- | --- |
| Package generated | Did Builder write the Skill files? | `draft_ready` |
| 单次执行检查 | Can this generated Skill be invoked once and render a report? | `execution_check_passed` / `execution_check_blocked` |
| 试运行 | Do required paths fetch real data and execute judgments for cases? | `trial_passed` / `trial_failed` |
| Loadability | Can alert Agent load it as one callable capability? | `loadability_ready` / `loadability_blocked` |
| Admission/Evaluator | Is quality, safety, standardization good enough? | placeholder until Evaluator exists |

Do not collapse execution check into admission. A Skill can pass execution check but fail admission quality; it can also be well-packaged but be execution-blocked by missing auth in the current runtime.

## Report Contract Design

Report contract is a Builder step, not only a trial-run expectation. Define it before package generation, then verify it during single execution check and trial run.

Default report template:

```yaml
diagnosis_report_template:
  root_cause_summary:
    max_chars: 100
    style: concise
    rule: "Summarize confirmed root cause, likely cause, or unknown status. Do not fabricate certainty."
  sop_step_conclusions:
    format: list
    fields:
      - step_name
      - conclusion
      - key_evidence
      - status   # confirmed_abnormal|normal|unknown|blocked|skipped
  key_evidence:
    max_items: 5
    include_values: true
  terminology:
    explain_abbreviations: true
    avoid_unexplained_jargon: true
    glossary_max_items: 5
    rule: "When domain abbreviations or ambiguous phrases appear, rewrite them in plain Chinese or add a short explanation on first use."
  unknowns:
    include: true
    rule: "Show missing data, empty samples, missing permissions, and unverified dependencies."
    style_rule: "Use compact business-facing boundaries. Do not write first-person defensive paragraphs or repeated '不能...' lists."
  dependency_gaps:
    include: true
  suggested_next_actions:
    include: true
    include_owner: optional
```

Default user-facing output shape:

```text
根因总结（100 字内）：
{confirmed_or_likely_root_cause_or_unknown}

关键步骤结论：
1. {SOP step}: {normal/abnormal/unknown}; 证据：{short evidence}
2. {SOP step}: {normal/abnormal/unknown}; 证据：{short evidence}

术语说明（如有）：
- {abbreviation_or_jargon}: {plain Chinese explanation}

仍未确认：
- {unknown/dependency gap/manual gap}

建议动作：
- {owner/action if configured}
```

Conversation prompt:

```text
我先用默认报告模板：100 字内根因总结 + 按 SOP 展开的关键步骤结论 + 未确认项 + 建议动作。你可以直接说要调整，比如“结论更短”“增加 owner”“不要建议动作”“步骤结论用表格”。
```

Allowed user adjustments:

- summary length: 50/100/200 chars or custom;
- output style: list/table/JSON/Markdown sections;
- include or hide raw values;
- include confidence, owner, next action, dependency gaps, unknowns, out-of-scope branches;
- require terminology explanation for abbreviations, platform terms, or ambiguous phrases;
- rename sections to match team language;
- require a final "防误判说明" section;
- require one-line executive summary for IM/alert notification.

Boundary wording rule:

```text
结论边界：证据不足，暂不能确认根因；{one most important missing evidence}.
```

Avoid:

```text
我也把“不能声称”的边界写进报告...
```

Before trial run, confirm the report shape:

- What root-cause conclusion fields must be present?
- Should contacts/owners be recommendations only, or should the Skill trigger notifications?
- How should out-of-scope branches appear?
- How should manual/background checks appear?
- How should missing dependency results appear?

Runtime report schema:

```yaml
diagnosis_report:
  scene: ""
  trigger_window: ""
  executed_path: []
  abnormal_periods: []
  key_evidence: []
  conclusion: ""
  confidence: ""
  unknowns: []
  dependency_gaps: []
  suggested_owners: []
  out_of_scope: []
```

## Skill Evaluator Placeholder

Reserve this gate, but do not run it until the separate Evaluator capability is introduced.

```yaml
admission:
  skill_evaluator:
    status: placeholder
    current_action: "Builder only prepares inputs"
    expected_future_inputs:
      - generated_skill_package
      - diagnostic_flow_ir
      - dependency_map
      - trial_run_cases
      - trial_run_logs
      - historical_cases
```

Language to use:

"准入 Evaluator 当前是预留节点。Builder 现在只准备 Skill 包、IR、依赖图和试运行材料；不宣称已经通过准入。"
