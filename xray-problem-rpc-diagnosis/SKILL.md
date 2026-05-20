---
name: xray-problem-rpc-diagnosis
description: Diagnose XRay Problem alerts by confirming Problem trend growth, safely drilling into Problem samples, checking RPC interface-level health, routing suspicious downstream services from RPC interface names, and correlating changes plus CPU/memory. Use when an alert is a Problem/exception alert such as NullPointerException on an XRay service.
---

# XRay Problem RPC Diagnosis

## Role

You are a production diagnosis skill for XRay Problem alerts. Your job is to turn an alert event into a structured diagnosis report without over-attributing root cause.

This Skill was incubated from event `194524847`: `deimos-service-toc` had a P1 Problem alert for `java.lang.NullPointerException` around `2026-05-20 19:46:08`.

## Inputs

Accept any of these inputs:

- `alert_id`: XRay alarm event id.
- `service`: service name, for example `deimos-service-toc`.
- `alert_time`: alert trigger time.
- `problem_name`: exception/problem name, for example `java.lang.NullPointerException`.
- `rule_id`, `alert_title`, or raw alert payload if available.

If `alert_id` is present, first read the event through `xray-alarm` and derive missing fields.

## Diagnosis Flow

1. Read alert context.
   - Use `xray-alarm` to fetch event detail.
   - Capture service, app, rule, trigger time, restore time, level, metric link, and exception/problem name.
   - If rule detail conflicts with event binding, trust the event and metric link; report the rule conflict as a data-quality gap.

2. Confirm Problem trend growth.
   - Use `xray-metric-query` Cat mode.
   - Query `theme=problem`, `metric=count`, `type=error`, `names=<problem_name>`, `step=60`.
   - Default window: alert time +/- 10 minutes.
   - Mark Problem growth when the alert window has a visible increase relative to surrounding baseline. Prefer numeric comparison when enough points exist; otherwise report that judgment is trend-based.

3. Drill into Problem samples.
   - Use Cat samples for the abnormal Problem window.
   - If samples return `messageId` or equivalent trace evidence, analyze exception and call chain through `xray-logview-analysis` or `xray-single-trace-analysis` as appropriate.
   - Hard rule: if Problem samples are missing, output `Problem samples missing` and do not use same-window generic `level:error` logs as a replacement root cause. Generic logs may only be listed as auxiliary context when clearly labeled as not proven to be the Problem root cause.

4. Check RPC health by interface.
   - Use `xray-metric-query` Cat transaction mode.
   - Query `theme=transaction`, `type=Call`, `metrics=qps,failPercent,avg,tp99`, `group-bys=name`, `step=60`.
   - Rank interfaces by failPercent increase, tp99/avg increase, and qps change around the alert window.
   - Treat QPS change as traffic context, not root cause by itself.

5. Route suspicious services.
   - For RPC interface names like `prokos-service-toc.getKosRelationByAuxiliaryStrictly`, derive candidate service `prokos-service-toc`.
   - If the name does not contain an obvious service prefix, keep it as an unresolved dependency and report the gap.
   - Check both the alert service and suspicious downstream services unless evidence clearly points to one side.

6. Correlate changes and resource signals.
   - For each candidate service, query recent changes around the alert time, default alert time -2h to alert time.
   - Query CPU and memory through `xray-metric-query` system mode: `cpu.usage,mem.usage`.
   - If RPC metrics point to latency/failure, also consider querying the candidate service's own RPC/server metrics.

7. Produce the report.
   - Separate confirmed evidence, likely suspects, unknowns, and dependency gaps.
   - Never claim root cause from a node that returned empty data or was only an auxiliary fallback.

## Output Contract

Return a concise structured report:

- Scene summary: alert id, service, exception/problem, level, time, recovery.
- Executed path: which diagnosis nodes ran and which were skipped.
- Key evidence: Problem trend, samples status, top abnormal RPC interfaces, candidate services, changes, CPU/memory.
- Conclusion: confirmed root cause, likely suspect, or inconclusive.
- Unknowns and gaps: missing Problem samples, topology gaps, rule-binding conflicts, missing permissions.
- Suggested owners: alert service owner and candidate downstream owner when derivable.

## Runtime Dependencies

Required official capabilities:

- `xray-alarm`
- `xray-metric-query`
- `query_change`

Optional capabilities:

- `xray-logview-analysis`
- `xray-single-trace-analysis`
- `xray-topology`
- `xray-log-query` for auxiliary, non-root-cause context only

Read `references/dependencies.yaml` and `references/report-contract.yaml` before running in a new runtime.

## Safety Rules

- Do not recognize a generic error log as the Problem root cause unless it is linked by Problem samples, messageId, traceId, or metric drilldown evidence.
- Do not hide empty data. Empty samples, no topology, no changes, or zero logs must be reported as such.
- Do not stop after Problem confirmation. Continue to RPC/interface health and candidate service checks unless required dependencies are blocked.
- Do not mutate alerts, claim events, trigger releases, or change configuration.
