# Product Analysis Framework

## Report Structure (Required Sections)

### Section 1: Data Quality Summary

Present counts and a rationale table:

```
Total raw records: N
Invalid (filtered): X  
Valid records: N-X

Invalid breakdown:
| Name | Fill Time | Reason |
|------|-----------|--------|
| ... | 14s | All answers = "1", duplicate submission |

Quality tier distribution:
| Tier | Count | Characteristics |
|------|-------|-----------------|
| HIGH | ~25%  | Complete scenarios, clear journey |
| MID  | ~50%  | Specific needs, limited detail |
| LOW  | ~25%  | Checkbox-only, 1-2 word answers |
```

Always present the invalid list before filtering and confirm with user.

### Section 2: User Segmentation by Usage Pattern

**Do not segment by job title alone.** Segment by how users actually interact with the product. Four archetypal patterns (adapt to domain):

| Type | Trigger | Core Need | Frequency Pattern |
|------|---------|-----------|------------------|
| Reactive | Alert/complaint/error | Fast root cause | Irregular, urgent |
| Investigative | Active suspicion | Hypothesis narrowing | Regular, deliberate |
| Maintenance | Scheduled/routine | Coverage & validity | Predictable, repetitive |
| Data-driven | Metrics/trends | Export & synthesis | Periodic, batch |

For each segment:
- Representative count and % of valid responses
- Typical usage journey (3-5 steps)
- What the same "feature" means to this segment (critical: same feature, different need)
- Key users to interview from HIGH tier

### Section 3: Trigger Source Analysis

Map where users start — this defines the Skill's interaction entry point.

| Trigger Source | Count | Key Design Implication |
|----------------|-------|------------------------|
| Alert/notification | N | Near-zero input; auto-respond to alert ID |
| Active investigation | N | Has a hypothesis; guide narrowing |
| CI/CD / deploy event | N | Needs baseline comparison |
| Scheduled / periodic | N | Not a Skill — this is a workflow/scheduler |
| External system event | N | API-first; structured output for machines |
| Customer complaint | N | UID-anchored; trace user journey |

⚠️ Periodic triggers (daily/weekly jobs) are **not Skill candidates** — they require workflow scheduling infrastructure, not on-demand invocation.

### Section 4: Core Journey Maps

Extract 3–6 journeys from HIGH-tier open-ended responses. For each journey:

```
Journey Name: [Action-oriented title, e.g., "Alert-Driven Root Cause"]
Trigger: [What causes the user to open the product]
Goal: [What they need to achieve]

Steps:
1. [Action] → [Tool/system used] → [Pain point if any]
2. ...
N. [Resolution or handoff]

Key pain points:
- [Exact user quote] — [Username]
- ...

Automation opportunity:
[Which steps could be eliminated or automated by a Skill]
```

Pain point categories (use these labels):
- **Batch gap**: Must repeat N times manually (N clusters/services/pods)
- **Cross-system switch**: Must leave product to check another system
- **Last-mile break**: Got the data but must manually move it somewhere
- **Cognitive load**: Must do complex reasoning under time/stress pressure
- **Expertise barrier**: Task requires specialized knowledge (e.g., PQL syntax, tuning parameters)

### Section 5: Feature Frequency with Cross-Validation

Present selection rate alongside open-ended description rate:

| Feature | Selected | % | Described in open-ended | Verdict |
|---------|----------|---|------------------------|---------|
| Log query | 41 | 84% | 35+ | ✅ Real demand |
| Alert config | 17 | 35% | 12 | ✅ Real demand |
| Agent status | 11 | 22% | 0 | ⚠️ Likely casual selection — validate |
| Event query | 13 | 27% | ~0 | ⚠️ Likely casual selection — validate |

**Rule**: Features with selection rate > 20% but 0 open-ended descriptions → flag and defer until user interviews confirm real scenarios.

### Section 6: Prioritized Capability List

```
P0 (Build now):
- [Capability] — [# users, key pain point, evidence quote]
- ...

P1 (Build soon):
- [Capability] — [Rationale]

P2 (Roadmap):
- [Capability] — [Condition for elevation to P1]

Hold (Do not build yet):
- [Capability] — [Why: no scenario evidence / pre-requisite missing / needs validation]
```

Prioritization signals (in order of weight):
1. Trigger frequency (how often does this happen)
2. Pain severity (how bad is it — stress level, time lost, error risk)
3. Evidence quality (vivid open-ended > checkbox-only)
4. Pre-requisite availability (can we build it now)
5. Strategic leverage (does it unblock other capabilities)

### Section 7: Follow-up Interview Recommendations

List HIGH-tier users with specific interview topics:

| User | Evidence Quality | Topics to Probe |
|------|-----------------|-----------------|
| [Name] | Precise journey map | [Specific unresolved question] |
| ... | | |

Interview guide structure (per user):
1. Walk me through the last time you [journey trigger]
2. What did you open first? What did you do next?
3. Where did you get stuck or have to switch tools?
4. How long did each step take?
5. What would "perfect" look like?

## Input → Output Signal Matrix

Use this when designing Skill inputs and outputs from survey data.

### Input signals (what users are willing to provide)

Collect from open-ended responses. Categorize:

| Input Type | Naturalness | Notes |
|-----------|-------------|-------|
| Service name | High | Users mention this constantly |
| Time range | High | "just now", "around 3pm", "last 30 min" |
| Error keyword | High | Copy-pasted from terminal or alert |
| TraceID | Medium | Only power users know to look for it |
| UID | Low | Customer-facing teams only |
| SQL/query syntax | Very Low | Expertise barrier — Skill should generate this |

### Output signals (what users expect to receive)

| Output Type | Demand | Notes |
|------------|--------|-------|
| Root cause conclusion | High | "Why did it fail?" not "here's the data" |
| Visual dashboard/chart | High | Users want assets, not raw numbers |
| Alert rule | High | Expect creation, not just config advice |
| Structured log summary | Medium | Noise-filtered, not full list |
| Topology map | Medium | Upstream/downstream service graph |
| Exported report | Low-Medium | Periodic batch users specifically |
| Code fix suggestion | Low | Specialized users only |

⚠️ High demand for "create asset" outputs (dashboard, alert rule) means the product must support write operations, not just read/query.
