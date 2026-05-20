# Dependency Map

Use this map as the short human-readable view. For actual matching, first read `platform-capability-registry.yaml`; it contains trigger intents, inputs, outputs, safety boundaries, and node mappings.

| Need | Candidate | Notes |
| --- | --- | --- |
| 告警事件/规则/title/product line | xray-alarm | Query event detail, rule config, historical alert events. |
| 指标趋势/PromQL/同比环比 | xray-metric-query, xray-cli | Prefer non-interactive JSON output for generated diagnosis Skill. |
| 日志/关键词 | xray-log-query, xray-cli log query | Use when SOP needs log rows, counts, or extracted fields. |
| 外部平台数据/SQL-like 查询/自定义脚本 | existing Skill, official CLI, official API, generated script, manual placeholder | Use the generic external-data node contract. Concrete platforms are adapters, not Builder primitives. |
| Trace/慢链路/异常 span | xray-trace-search, xray-single-trace-analysis, xray-logview-analysis | Use trace id, service, endpoint, slow/error mode. |
| AI agent/Langfuse trace | xray-ai-trace-analysis | Use for AI application or agent workflow diagnosis. |
| 服务上下游/拓扑 | xray-topology | Use when path depends on upstream/downstream health. |
| 发布/镜像/部署组/Pod | ones-assistant | Official ONES skill; production actions need strict safety boundary. |
| Darwin/Autobots 索引、构建、队列、迁移、服务数据 | darwin-autobots-cli, darwin-index-query, k8s-diagnosis, index-switch-check, autobots-queue-report, index-migration-check, autobots-queue-mapper, autobots-build-troubleshooting, darwin-service-query, deploy-group-diagnosis, autobots-database, darwin-agent-call | Use for Darwin index/build/service troubleshooting. Treat mutations such as pod restart as forbidden unless explicitly gated. Database-backed checks require auth contract. |
| 变更/封网/合规 | RCM official Skill | Use for release, config, strategy, freeze window, compliance checks. |
| 容量水位/压测 | Honghu capacity Skill | Use for capacity-driven incidents. |
| 预案/HA 元数据/RCA case | HA/RCA official Skills | Use for emergency plan matching and historical case search. |
| 实验配置/灰度桶 | Experiment platform Skill or API | Mark missing if no official skill/API exists. |
| 未知平台数据源 | generated adapter interface or manual placeholder | Ask for locator, returned fields, judgment rule, and failure policy before claiming configured for trial run. |

Dependency status values:

```yaml
dependency_candidates:
  - name: xray-metric-query
    status: candidate
    reason: "需要按实验组查询业务指标"
    runtime_mode: read_only
  - name: experiment-platform-skill
    status: missing
    reason: "需要查询实验配置和 owner，但当前未确认官方 Skill"
    fallback: "报告中标记需要人工补充实验元数据"
```

Safety rules:
- Prefer read-only dependencies for generated diagnosis Skills.
- Do not add production mutation actions unless explicitly required and separately controlled.
- Mark unofficial or unavailable dependencies as gaps instead of silently replacing them with guessed APIs.

Builder behavior:
- Do not ask the user to know Skill names.
- Infer candidate dependencies from the registry.
- Show the reason for the match in the node table or IR.
- Ask the user to confirm business semantics, available dimensions, and permission boundary.
- Keep missing dependencies as explicit interfaces with fallback behavior.
