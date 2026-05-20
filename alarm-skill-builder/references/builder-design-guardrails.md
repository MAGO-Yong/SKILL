# Builder Design Guardrails

## Root Cause Of Previous Bias

The Builder accidentally reused a diagnosis flow from earlier examples:

- parse alert / business domain / metric / time window
- false alarm filtering
- change / experiment / release check
- metric breakdown
- structured report

Those are valid nodes for some diagnosis Skills, but they are not the universal Builder flow.

## Correct Abstraction

The universal Builder flow is:

1. User asks to create a diagnosis Skill.
2. Builder creates and confirms a Scene Card.
3. Builder proactively enriches context from alert/rule/service/dashboard artifacts.
4. Builder asks for the troubleshooting story.
5. Builder models structure: sequence, parallel paths, branches, manual/dynamic steps.
6. Builder visualizes only user-derived, artifact-derived, or accepted nodes.
7. Builder binds data and verifies dependencies node by node.
8. Builder scores completeness.
9. Builder compiles a Skill package and trial-run materials.

## Hard Rules

- Start diagnosis IR with `nodes: []`.
- Do not prefill parse, false-alarm, change, metric-breakdown, report, or trial-run paths.
- Do not skip Scene Card confirmation unless the user explicitly gives a complete existing IR.
- Label generic ideas as `builder_suggested`; compile them only after user acceptance.
- Keep examples neutral and synthetic. Do not ship user-provided cases as examples.
- When a user points out overfitting, search all Skill files for the leaked fixed nodes and remove them.

## Distribution Boundary

User-provided validation materials, screenshots, private SOP examples, local HTML review artifacts, reverse simulations, and one-off case studies must not be included in the distributed Builder package.

Allowed:

- Extract generic Builder requirements from a case.
- Convert repeated findings into neutral rules, schemas, templates, or capability contracts.
- Keep private validation artifacts outside the Builder package.

Forbidden:

- Shipping files named after a user-provided case.
- Shipping reverse-simulation notes.
- Shipping local paths, screenshots, copied SOP content, or specific alert/service examples.
- Using a previous user's business flow as a default example in Builder prompts.
