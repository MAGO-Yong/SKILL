# Agent Native Skill Design Principles

Use this reference when the survey analysis leads to defining product capabilities as Skills (e.g., AI Skills, platform APIs, agent tools).

## The Core Problem: Feature-Mapped vs. Intent-Mapped

**Feature-mapped Skills** (wrong):
- Mirror product UI pages 1:1
- Input = platform internal parameters (e.g., logview ID, transaction type)
- Output = raw data list
- Agent must chain multiple Skills to complete one task

**Intent-mapped Skills** (correct):
- Mirror user task intent
- Input = what users naturally say (service name, time range, error keyword)
- Output = actionable conclusion
- Skill internally orchestrates all data fetching and reasoning

## Three-Layer Architecture

```
Scenario Skills  ──  Domain-specific wrapping; role language; embedded expertise
      ↑ calls
Composite Skills ──  Orchestrate atomics; solve complete task intent; output conclusions
      ↑ calls
Atomic Skills    ──  Single data dimension; zero inference; structured data output
```

**Visibility rule**: Users and external Agents see only Composite + Scenario Skills. Atomic Skills are internal building blocks — do not expose them directly unless as platform API primitives.

## Atomic Skill Design

### What makes a good Atomic Skill

Atomic Skills fetch one type of data along one natural dimension. The split criterion is:

```
Signal type (log / trace / metric / alert / change) × Granularity (single / list / aggregate)
```

**Validation checklist**:
- [ ] No platform-internal concepts in input parameters (no internal IDs, internal type names)
- [ ] No inference or judgment in output ("is this an error?" → NO; "here is the error count" → YES)
- [ ] Can be reused by at least 3 different Composite Skills

### Atomic Skill template

```
ID: [system-readable-id]
Resolves: [What data does this return, in one sentence]
Input: [param1 (required)] · [param2 (optional)] · ...
Output: [data structure description — field names and types]
Does NOT do: [explicit boundary — what inference or action is out of scope]
User demand source: [quote from survey respondent]
Status: [✅ exists / 🔵 partial / 🔴 not built]
```

### Common Atomic Skill domains for observability platforms

| Domain | Natural Dimensions |
|--------|--------------------|
| Log | by-condition list, pattern cluster, field aggregate |
| Trace | search list, single detail, exception distribution |
| Metric | time series curve, resource snapshot |
| Alert | event list, rule config |
| Change (external) | change record list (deploy/config/flag) |

**External system atomics** (e.g., change records from deploy/config systems) are often the most critical and most neglected. If root cause analysis requires cross-system correlation, the external atomic is not optional — it's a prerequisite.

## Composite Skill Design

### What makes a good Composite Skill

A Composite Skill solves one complete task intent. It:
- Has a clear trigger phrase ("my service is alerting, what's wrong?")
- Internally calls multiple atomics without exposing the chain to the caller
- Outputs a decision-ready conclusion, not a data dump
- Includes an LLM reasoning layer that synthesizes evidence into a finding

### Composite Skill template

```
Name: [Human-readable name]
Task intent: [The exact question a user would ask to trigger this]
Trigger: [Event-driven / User-initiated / Agent-invoked]

Internal orchestration:
  1. [Atomic call + purpose]
  2. [Atomic call + purpose]
  ...
  N. LLM reasoning: [What it synthesizes]

Output:
  - [Conclusion item 1]
  - [Conclusion item 2]
  - [Recommended action]

Demand source: [N users, representative quotes]
Critical dependency: [Any atomic that MUST exist for this to have value]
```

### Composite Skill types (by user trigger)

| Type | Trigger Pattern | Core Design Requirement |
|------|----------------|------------------------|
| Reactive | Alert / error event | Near-zero input; fast; automated |
| Investigative | User has a hypothesis | Narrowing interaction; guide to answer |
| Constructive | User wants to create something | Write access required; preview before commit |
| Observational | Periodic / deploy event | Baseline comparison; batch output |

## Scenario Skill Design

Scenario Skills wrap Composite Skills in domain language for a specific role. They differ from Composite Skills in:

- Input uses role-native vocabulary (e.g., `jobName` not `serviceName` for data engineers)
- Output includes role-specific judgment (e.g., "PS vs. Worker" for ML engineers)
- Embedded domain expertise in reasoning layer (e.g., Flink backpressure patterns)

### When to create a Scenario Skill vs. a Composite Skill

Create a Scenario Skill when:
- A specific role uses a distinctly different vocabulary for the same underlying data
- The reasoning layer requires embedded domain knowledge not generally applicable
- The output format is tailored to a role-specific workflow

Do NOT create a Scenario Skill just because there's a different user persona. If the underlying journey and data are the same, use a Composite Skill with flexible parameters.

## Common Anti-Patterns

| Anti-pattern | Example | Fix |
|---|---|---|
| UI page mapping | "Log page Skill" | Map to intent: "Error pattern detection" |
| Platform vocab leakage | Input: `logviewId`, `transactionType` | Input: `traceId`, `serviceName` |
| Inference in atomic output | "Is this anomalous: yes" | Remove judgment; return count only |
| Composite doing one thing | Composite calls 1 atomic | Merge into atomic or elevate to composite |
| Missing external atomic | Root cause Skill without change data | Change record atomic is prerequisite |
| Periodic task as Skill | "Daily log export Skill" | This is a scheduled workflow, not a Skill |
| High selection ≠ build it | "Agent status analysis" (0 descriptions) | Validate with interviews before building |
