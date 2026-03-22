# Output Modes

Switch output shape based on the user's stage, not just the topic.

## Round 1 Default

Use a research memo plus decision recommendation style.

Characteristics:
- conclusion-forward
- structured
- research-oriented
- preserves key observations and unresolved questions
- helps the user decide whether to go deeper

If the user's goal is first-time understanding, round 1 should instead read like a learning-oriented research note.

Characteristics:
- explanation-forward
- fewer compressed bullets
- more full-sentence teaching
- introduces concepts step by step
- uses examples to reduce confusion
- still ends with a judgment, but only after the concept is understandable

## Round 2 Exploratory

If the user still wants deeper understanding rather than proposal support, keep a deeper memo-style analysis.

Characteristics:
- stronger judgments than round 1
- more focused than round 1
- still preserves research logic and unresolved areas

## Round 2 Initiative / Proposal / Solution

If the user is moving toward initiative evaluation, proposal work, or solution direction, switch to a presentation-friendly report style.

Characteristics:
- conclusion-forward
- more formal structure
- emphasizes background, problem, practices, internal mapping, recommendation, and next actions
- suitable for internal presentation or evaluation
- should make the evidence basis visible when strong claims are made

When using this mode, clarify the audience if it matters:
- manager or leadership
- review committee
- cross-functional team
- technical design audience

For internal technical product or solution topics, also prefer making source grounding visible in concise form, for example:
- official documentation
- internal system context
- practice reports
- case studies
- observed production patterns

When the topic is an internal platform plan, evaluation platform, governance platform, or technical solution proposal, also prefer making these explicit when available:
- which user groups or business lines are driving the demand
- which modules are P0/P1/P2 or otherwise most urgent
- which adjacent platforms already exist and what should be reused
- what milestone or staged landing target the recommendation implies

For platform, model, or architecture topics, also prefer:
- making the document teach through examples instead of staying purely abstract
- including a few concrete schema/object/workflow examples when they materially improve understanding
- explicitly stating major design tradeoffs and why the recommended split is chosen

For learning-oriented outputs, also prefer:
- using simple comparisons such as "A answers X, B answers Y"
- explicitly saying "this means" or "in practice"
- writing for a reader who may be seeing the topic for the first time

## Always Keep

Regardless of mode, keep:
- key conclusions
- risks and boundaries
- unresolved questions
- next-step actions
