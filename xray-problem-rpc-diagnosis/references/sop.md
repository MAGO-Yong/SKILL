# SOP

## Scene

XRay Problem/exception alert for a service. The initial case is `deimos-service-toc` with `java.lang.NullPointerException`, P1, triggered at `2026-05-20 19:46:08` and restored at `2026-05-20 19:47:08`.

## Human Troubleshooting Story

1. First query the service's Problem trend.
2. Check whether exceptions clearly increased and identify the abnormal time point.
3. Analyze related exceptions to find the concrete error point.
4. Check RPC calls by interface: QPS, success/failure, avg latency, and tp99.
5. Inspect upstream/downstream dependency services to decide whether the issue is local or dependency-caused.
6. For suspicious services, query changes, CPU, and memory to narrow root cause.

## Critical Preservation Rule

If Problem samples are missing, do not use same-window generic error logs as the root cause replacement. Report `Problem samples missing` and continue with RPC/resource/change correlation as separate evidence.

## Default Windows

- Problem trend: alert time +/- 10 minutes.
- Problem samples: the abnormal minute or a 2 minute window around it.
- RPC metrics: alert time +/- 10 minutes.
- Changes: alert time -2 hours to alert time.
- CPU/memory: alert time +/- 10 minutes.
