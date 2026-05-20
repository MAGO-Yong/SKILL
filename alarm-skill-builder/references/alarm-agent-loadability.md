# Alarm Agent Loadability

Use this checklist before claiming a generated diagnosis Skill can be loaded by the alert Agent.

Ignore publication logistics here unless the user explicitly asks for release or publishing.

## Loadability Principles

1. **Official dependency basis**: the diagnosis Skill should rely on official CLI, official Skill, or official API capabilities for metrics, logs, traces, events, changes, topology, capacity, experiments, and other platform data.
2. **Third-party auth is explicit**: if the Skill depends on another Skill/platform, capture identity authentication, permission check, call authorization, credential runtime, renewal, and failure policy.
3. **Single exposed capability**: the alert Agent should call one generated diagnosis Skill entrypoint. Internal calls to metrics/logs/traces/events/changes should be orchestrated and packaged behind that entrypoint.
4. **Complete packaging**: package prompts, references, routing, scripts/wrappers, dependency contracts, auth contracts, trial cases, and report schema together.
5. **No hidden local dependencies**: dependencies that only exist on the creator's local machine are not loadable unless packaged as wrappers around official interfaces.
6. **Dependency bootstrap is explicit**: installing the Builder Skill does not automatically install all platform Skills/CLI it knows about. The generated diagnosis Skill must declare the minimal dependency set it actually needs, plus install/auth/preflight requirements.
7. **Target runtime portability**: loadability must be evaluated for the target Agent runtime, such as OpenClaw, CC, Codex, or another Agent host. A dependency that works only in the creator's local Codex session is not enough.

## Required Package Artifacts

```text
<diagnosis-skill>/
├── SKILL.md
├── manifest.yaml
├── references/
│   ├── sop.md
│   ├── diagnostic-flow.yaml
│   ├── dependencies.yaml
│   ├── dependency-bootstrap.yaml
│   ├── auth-contracts.yaml
│   ├── report-contract.yaml
│   └── trial-cases.yaml
├── scripts/
│   └── atomic/                 # optional wrappers around official CLI/API only
└── tests/
    └── trial-run-cases.yaml
```

## Dependency Policy

Allowed:

- official CLI with stable non-interactive invocation;
- official Skill available to the Agent runtime;
- official API with documented auth and response schema;
- packaged script wrapper around official CLI/API;
- manual placeholder only when clearly reported as non-executable gap.

Not loadable:

- dependency installed only on the creator's local machine;
- hidden transitive Skill dependency not declared in the package;
- third-party Skill without auth/permission/call contract;
- script that requires interactive login during alert runtime;
- data node marked runtime executable without trial-run verification evidence.
- required dependency that is listed only in Builder's registry but not installed, authorized, or declared in the generated Skill package.
- dependency that has no invocation path in the target Agent runtime, even if it works in another Agent host.
- generated wrapper that relies on absolute local paths or creator-machine-only files.

## Dependency Bootstrap Contract

Generated diagnosis Skills should include the minimal runtime dependency set, not the full Builder registry:

```yaml
dependency_bootstrap:
  required:
    - dependency_id: xray-metric-query
      required_by_nodes: [step_1_metric_check]
      install_source: "SkillHub or built-in platform Skill"
      invocation_method: skill
      auth:
        identity_source: "agent identity or XRay read token"
        permission_check: "can read metric datasource"
      preflight:
        command_or_verification: "read-only sample query"
        expected_fields: [time_series]
      fallback: "block node and report dependency gap"
  optional:
    - dependency_id: rca-case-query
      fallback: "skip optional historical case enrichment"
```

For users who install only Builder, this file is the bridge from "Builder knows the dependency exists" to "this generated Skill can actually run in their environment".

Use `references/dependency-bootstrap-template.yaml` as the template for this artifact.

## Third-Party Skill Auth Contract

For every third-party Skill/platform dependency:

```yaml
auth_contract:
  dependency_id: ""
  platform: ""
  identity_source: ""      # service account / user token / agent identity / platform token
  authentication: ""       # how token/session is acquired
  permission_check: ""     # how permission is verified before call
  call_authorization: ""   # allowed scopes/actions/apis
  secret_runtime: ""       # env var / vault / platform credential
  renewal_policy: ""
  failure_policy: ""       # block node / mark unknown / stop diagnosis / continue
```

If this is unknown, keep the dependency as `loadability_blocked` even if a local verification worked.

## Single Entrypoint Contract

The packaged diagnosis Skill must expose:

```yaml
entrypoint:
  name: diagnose
  input_schema:
    alert_id: optional
    alert_time: required
    alert_title: optional
    service: optional
    rule_id: optional
    payload: optional
  output_schema:
    scene_summary: required
    executed_path: required
    key_evidence: required
    conclusion: required
    unknowns: required
    dependency_gaps: required
    suggested_owners: optional
```

The alert Agent should not need to know whether the generated Skill internally uses metrics, logs, traces, change queries, or other Skills.

## User-Facing Language

When blocked:

```text
这个 Skill 目前可以生成草稿，但还不能声明“告警 Agent 可加载”。阻塞项是：第三方依赖 X 的鉴权契约缺失，或 Y 仍是本地脚本没有官方接口。
```

When ready:

```text
这个 Skill 已满足加载准备：官方依赖已封装，三方鉴权契约齐全，对外只暴露一个 diagnose 入口，依赖对告警 Agent 是透明的。
```
