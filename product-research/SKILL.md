---
name: product-research
description: Conduct deep product research for new concepts, market directions, product opportunities, competitor analysis, initiative evaluation, and decision support. Use when Codex needs to clarify a research topic, collect and analyze materials, deepen through iterative research, compare industry practices, synthesize findings, and produce a structured product research report with recommendations.
---

# Product Research

Conduct deep product research for unfamiliar topics, new directions, product opportunities, competitor analysis, initiative evaluation, and decision support.

Default to a product manager perspective. Focus on users, scenarios, value, alternatives, paths, risks, and next actions. When the topic is technical, platform, infrastructure, or engineering-efficiency related, strengthen analysis of capability boundaries, dependencies, implementation conditions, and rollout constraints.

Do not treat this skill as a one-shot summary tool. Default to deep research mode unless the user explicitly asks for a lightweight pass.

## Workflow

Follow this sequence unless the user explicitly asks for a different shape of output:

1. Topic alignment gate
2. Round 1 light intake
3. Round 1 foundational research
4. Round 1 memo-style report
5. Round 2 narrowing conversation
6. Round 2 deep research
7. Round 2 decision-oriented report

Use the round 1 memo style by default. If round 2 becomes initiative-, proposal-, or solution-oriented, switch to a presentation-friendly report style.

## Topic Alignment Gate

Before starting formal research, align on what the user actually wants to study.

Do not start searching, analyzing, or drafting conclusions until the topic is aligned.

### Goal

Confirm:
- what the user wants to study
- what key terms mean in this context
- what the current research boundary is
- what direction to use for the first round of research

### Core rules

- Align the research object before researching the content.
- Do not default to the most common public meaning of a term if multiple reasonable interpretations exist.
- Interpret the full phrase and task intent, not just isolated keywords.
- If the topic includes a concept plus an action or goal, prioritize the full task meaning.
- If there are two or more reasonable interpretations that would lead to different research paths, stop and align first.
- If the user gives examples, treat them as examples rather than hard scope boundaries unless the user explicitly says "only", "mainly", or otherwise constrains the scope.
- If the topic is a composite phrase such as "A + B", explicitly determine:
  - the research object
  - the research lens or discipline
  - the user's likely goal
  - the main output object
- For composite phrases, test at least 2-3 structural interpretations before locking direction. Common patterns include:
  - A for B
  - B for A
  - A/B as a category or market term
- Once the user clarifies the topic, rewrite the working definition, research boundary, and round focus before continuing. Do not continue on the pre-clarification path.

### High-risk topic detection

Treat the topic as high-risk and trigger alignment when any of these is true:
- a term may have multiple meanings
- the phrase includes abbreviations, jargon, internal terms, or mixed Chinese/English wording
- the topic is very short
- the topic is a compound phrase with unclear center of gravity
- the user describes what they want to achieve, but not clearly what object to research
- the same description could lead to very different research paths

Examples but not limited to:
- capability
- platform
- governance
- quality
- observability
- automation
- agent
- copilot
- availability
- security
- operations

### Output format

Use this structure:

I want to align on the topic first so the research does not drift.

My current understanding of your topic is:
- [one-sentence working definition]

I break this topic into these key parts:
- [...]
- [...]
- [...]

Possible ambiguity or branching points I notice:
- [...]
- [...]

If I continue with my current interpretation, I will focus on:
- [...]

Please confirm whether this understanding is correct. If not, tell me which meaning, object, or question you actually want to focus on.

If the user adds clarification, respond with an updated lock-in before starting research:

Updated working definition:
- [...]

This round will focus on:
- [...]

This round will not focus on:
- [...]

## Round 1 Light Intake

After topic alignment, ask only the minimum needed to start.

Confirm:
- why the user wants to research this now
- how familiar they already are with the topic
- what they most want to understand first

Do not ask for full internal context, target users, output form, and initiative constraints in the first round unless the user is already clearly in a proposal/initiative stage.

## Round 1 Foundational Research

Round 1 is for building reliable understanding, not for jumping directly into initiative design.

### Goal

Help the user move from vague awareness to structured understanding:
- what this is
- what problem it addresses
- where it applies
- what value it creates
- how the industry is approaching it
- whether it is worth deeper follow-up

### Default framework

Choose the default lens based on topic type:

For concept, system, platform, or capability topics, use:
1. definition and boundary
2. problem and drivers
3. scenarios
4. value logic
5. industry practices and representative approaches
6. implementation outline
7. initial judgment and next-step recommendation

For product opportunity, consumer, or market-facing topics, use:
1. target users and jobs to be done
2. problem and unmet need
3. alternatives and competition
4. value proposition
5. market or adoption signals
6. product shape and monetization hints
7. retention or repeat-usage logic when relevant
8. initial judgment and next-step recommendation

### Minimum coverage

Round 1 should usually cover:
- what it is
- what it is not
- adjacent concepts and distinctions
- typical scenarios
- value and expected benefits
- key implementation outline
- industry maturity and representative players
- initial judgment
- unresolved questions

For product opportunity or consumer topics, also cover:
- target users
- alternatives or competitive substitutes
- market/adoption signals when available
- basic business model or monetization clues when relevant
- retention, repeat usage, or behavior loop when relevant
- likely market entry point or wedge when relevant

For broad category or market-label topics, include at least:
- a judgment on whether the category is truly emerging, mostly marketing language, or just a feature layer
- at least 3 representative products, vendors, or substitutes when available

For product research topics, round 1 must also include a representative landscape sweep rather than only concept explanation.

At minimum, scan:
- representative international products or platforms
- representative China-market products or platforms when relevant
- major cloud vendors when relevant
- startup or tooling players when relevant
- open-source or ecosystem signals when relevant

If the topic is strongly relevant to the China market, Chinese product ecosystems, or Chinese vendor practice, do not rely only on English-language and overseas sources.

If the topic is about a capability system, platform capability, operating framework, or construction direction, do not stop at concept summary. Produce a capability map in round 1.

The capability map should usually show:
- research object
- capability layers
- core modules
- representative product mapping
- likely evolution path
- which modules are foundation versus upper-layer functions

Read [source-system.md](references/source-system.md), [analysis-frameworks.md](references/analysis-frameworks.md), and [output-modes.md](references/output-modes.md) when preparing round 1.

## Source System

Do not organize sources only as official versus unofficial. Organize them by research role.

### 1. Discovery sources

Use to discover concepts, players, themes, cases, and leads.

Examples:
- PR/news releases
- launch writeups
- conference news
- high-quality WeChat public account articles
- deep media articles
- newsletters
- personal blogs
- community discussions
- China vendor blogs and product announcements when relevant

### 2. Verification sources

Use to confirm facts, capability boundaries, implementation details, and constraints.

Examples:
- official product pages
- official docs
- whitepapers
- API docs
- best-practice guides
- release notes
- case studies
- open-source docs

### 3. Judgment sources

Use to support comparisons, maturity assessment, and recommendations.

Examples:
- practice retrospectives
- customer cases
- ecosystem and commercialization signals
- pricing pages
- partner pages
- analyst writeups
- internal materials

### Rules for WeChat articles

High-quality WeChat articles are valid inputs, especially for Chinese product and technology contexts.

Use them to:
- discover industry language and patterns
- find case studies and references
- identify leads worth tracing

Do not rely on them alone for major conclusions when stronger sources are available. If a WeChat article contains an important claim, trace to original docs, talks, whitepapers, or other corroborating sources when possible.

### Landscape scan requirement

For product research topics, do at least one explicit landscape sweep before finalizing round 1.

The sweep should identify relevant representatives across the most useful buckets, such as:
- international vendors
- China vendors
- cloud vendors
- platform/tooling companies
- open-source ecosystems

Do not assume overseas sources are sufficient when the topic has strong China-market relevance or the user is likely to need domestic product references.

## Lead Deepening And Relational Analysis

Do not read sources in isolation.

When you find an important lead, keep tracing it.

### What counts as a lead

- a new concept
- a product capability name
- an architecture module
- a scenario
- a customer case
- a metric or value claim
- a new player or project
- a route difference
- a keyword mentioned but not explained

### When to deepen automatically

Deepen when a source:
- introduces an important concept without detail
- mentions a product capability without explaining how it works
- mentions a customer case without implementation detail
- uses abstract words like "intelligent", "automated", or "agent-based"
- references docs, whitepapers, talks, repositories, or other primary materials
- conflicts with another source on something important

### Common deepening paths

- from PR to official docs
- from article to whitepaper
- from conference summary to slides/video/session details
- from concept to capability structure
- from capability to scenario
- from scenario to value
- from value to dependencies and constraints

### Relational analysis requirements

Map sources against each other instead of summarizing them one by one.

Look for:
- whether definitions align across sources
- whether a marketed capability is actually described in docs
- whether scenarios are validated by real cases
- whether value claims have evidence or only rhetoric
- whether different players are solving the same problem or just using similar words
- whether a capability depends on underlying data, workflow, governance, tooling, or human review
- whether the research should be framed as a market/category, a capability system, or an internal construction direction

## Round 1 Output Style

Default style:
- memo-style
- research-oriented
- decision-supporting
- conclusion-forward
- structured and restrained

Round 1 should feel like a strong internal research memo, not a polished executive deck.

If the topic is capability-system-oriented, make the capability map one of the primary outputs instead of burying it in narrative sections.

Use the round 1 template in [report-template.md](assets/report-template.md).

## Round 2 Narrowing Conversation

After round 1, stop and narrow before continuing.

Do not automatically continue into deeper research without checking direction.

### Goal

Turn "this is worth further study" into "this is the exact question the next round should answer."

### Confirm in round 2

- whether the user wants to continue
- whether the next round is still exploratory or now initiative-oriented
- which direction to deepen
- who the target user or object is
- what internal context or constraints matter
- what final output form is desired
- who the output is for when the work is initiative-, proposal-, or review-oriented
- what decision the user wants help making

### Suggested prompt structure

Based on round 1, the most promising directions to deepen are:
- [...]
- [...]
- [...]

To make round 2 focused, I want to confirm:
- do you want to keep understanding the space, or move into initiative / proposal / solution analysis?
- which area do you most want me to deepen?
- who is the main user or target object?
- do you already have relevant internal context, systems, pain points, or constraints?
- what kind of output do you want in the end?
- what decision do you want this research to support?

## Round 2 Deep Research

Round 2 is for stronger judgment, not wider collection.

### Common paths

#### A. Continued understanding

Use when the user still wants deeper market, route, or concept understanding.

#### B. Initiative evaluation

Use when the user wants to judge whether something should be proposed, prioritized, or started.

#### C. Solution direction

Use when the user already leans toward action and wants a path, design direction, or phased approach.

### Default framework for initiative / proposal work

Use:
1. background
2. problem
3. external practices
4. internal state and gap
5. direction or solution path
6. risks and prerequisites
7. recommendation and next actions

Also incorporate:
- current state
- gap
- opportunity
- path

### Round 2 focus

Usually cover:
- refined research question
- external industry practices and route differences
- target user and scenario mapping
- internal state mapping
- capability or solution breakdown
- value, risks, and prerequisites
- build vs buy or build vs integrate judgment when relevant
- what to do
- what not to do yet
- next-step validation plan

## Output Style Rules

### Default style switching

- Round 1 default: research memo + decision recommendation
- Round 2 default, if still exploratory: deeper memo-style analysis
- Round 2 default, if initiative/proposal/solution oriented: report-style, suitable for internal presentation

If the user explicitly asks for a format, follow the user's request.

### Always keep these sections

Regardless of stage, keep:
- key conclusions
- risks and boundaries
- unresolved questions
- next-step actions

### Writing style

- lead with conclusions
- prefer judgment over material dumping
- be direct, professional, and restrained
- avoid inflated trend language
- use wording like:
  - current judgment
  - more likely
  - still needs validation
  - more suitable
  - not recommended to prioritize yet

## Quality Control

### Depth checks

Research is not complete if it only:
- defines terms
- lists companies or articles
- repeats PR messaging
- explains value without constraints
- explains possibilities without dependencies
- gives no unresolved questions
- cannot answer "so what"

### Fact / judgment / recommendation separation

Always separate:
- facts: source-supported observations
- judgments: analysis based on facts
- recommendations: what should happen next

Do not present judgments as facts.
Do not present recommendations as industry consensus.

### Evidence strength

Treat evidence strength roughly as:
- strong: official docs, product pages, original case studies, multiple high-confidence sources
- medium: strong technical articles, talks, open-source docs, substantial retrospectives
- weak: single commentary article, media summary, community thread
- very weak: unattributed claims or vague marketing statements

Avoid using weak evidence alone for high-impact conclusions.

### Anti-hallucination rules

- do not invent capabilities, data, timelines, or cases
- if a detail is unverified, say so
- if only a direction is known, stay at direction level
- for time-sensitive claims, prefer current sources
- when in doubt, mark it as a working judgment or unresolved question

### Completeness checks before output

Before finalizing, check:
- topic was aligned
- the report answers a clear question
- scenarios, value, implementation outline, constraints, and maturity were covered where relevant
- risks and unresolved questions are present
- next actions are clear
- facts, judgments, and recommendations are separated

## Resources

- Use [analysis-frameworks.md](references/analysis-frameworks.md) for round-specific analysis lenses.
- Use [source-system.md](references/source-system.md) for source role definitions and validation guidance.
- Use [output-modes.md](references/output-modes.md) for style switching and report expectations.
- Use [report-template.md](assets/report-template.md) as the default report structure.

## One-Sentence Operating Principle

Do not aim to write something that merely looks like a report. Aim to produce research whose conclusions can withstand follow-up questions.
