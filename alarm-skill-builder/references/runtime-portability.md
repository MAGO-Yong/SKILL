# Runtime Portability

`alarm-skill-builder` is intended to be installed and used by other people in OpenClaw, CC, Codex, or other Agent hosts. Do not assume the creator's local environment, installed Skills, CLI paths, browser state, or filesystem layout.

## Portability Principles

- The Builder is a meta Skill. It carries guidance, registries, templates, and contracts; it does not automatically carry every platform Skill/CLI in the registry.
- Target runtime must be explicit: `openclaw`, `cc`, `codex`, or `other`.
- Capability matching must go through a runtime capability resolver when available. If the runtime cannot list Skills/CLI/API capabilities, record `unknown` and require preflight before claiming execution.
- Do not degrade a node to text-only guidance when the SOP requires data execution. Mark it blocked or a visible dependency gap.
- Do not use creator-machine absolute paths, local browser state, local cache files, or Codex-only tools in generated diagnosis Skills.
- Generated scripts are allowed only when packaged with the generated Skill and when their dependencies, interpreter, auth, inputs, outputs, and target runtime support are declared.

## Runtime Capability Matrix

For each required dependency, record target support:

```yaml
runtime_support:
  dependency_id: ""
  target_agent: openclaw|cc|codex|other
  invocation_method: skill|cli|api|adapter|script_wrapper|not_available
  supported: true|false|unknown
  install_state: installed|missing|unknown
  auth_state: ready|missing|unknown|failed
  non_interactive: true|false|unknown
  verification_status: not_run|success|blocked|failed
  blocker: ""
```

## No Capability Downgrade

If a node requires platform data, the Builder must not silently convert it to:

- a documentation-only instruction;
- a user-memory note;
- a manual checklist hidden inside a runtime executable path;
- a guessed query without official dependency support;
- a verification performed in Codex but packaged as if it works in OpenClaw or CC.

Allowed alternatives:

- `blocked`: required dependency cannot run in target runtime.
- `dependency_gap`: dependency contract is packaged, but node is not runtime executable.
- `manual_background`: user explicitly says this step is human context, not automated evidence.
- `optional_skipped`: optional enrichment can be skipped and reported as not-run.

## Generated Skill Package Requirements

The generated diagnosis Skill should include:

- `dependency-bootstrap.yaml` with target runtime and minimal dependency set;
- `auth-contracts.yaml` for third-party or platform dependencies;
- `diagnostic-flow.yaml` with configured-for-trial, runtime-executable, blocked, optional, and manual nodes separated;
- packaged scripts only with relative paths and declared interpreters;
- no references to `/Users/...`, `.codex`, `.agents`, local cache paths, local HTML review artifacts, or creator-only files.

## Builder Conversation Rule

When a dependency is not available in the target runtime, say:

```text
这个节点需要 {platform capability}，但目标运行环境 {target_agent} 当前没有可调用入口。这个节点不能降级成可执行，只能作为依赖缺口进入 Skill 包；补齐安装/鉴权/预检后才能启用。
```
