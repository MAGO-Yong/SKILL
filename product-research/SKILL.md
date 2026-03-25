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
- the topic appears to be an internal codename, internal methodology name, or internal product name

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

If the topic appears to be an internal codename or internal framework and there is not enough context, explicitly state that this round is limited by missing internal context and switch into internal-term-safe mode:

- do not invent a public definition
- do not over-generalize from similar public concepts
- ask for the minimum context needed to continue
- if the user does not provide it, produce a boundary-managed first-round note rather than pretending full understanding

## Round 1 Light Intake

After topic alignment, ask only the minimum needed to start.

Confirm:
- why the user wants to research this now
- how familiar they already are with the topic
- what they most want to understand first

Do not ask for full internal context, target users, output form, and initiative constraints in the first round unless the user is already clearly in a proposal/initiative stage.

If the user explicitly signals that they are new to the topic or want to "understand", "learn", "get familiar", or "build complete cognition" first, switch round 1 into learning-oriented mode rather than compressed memo mode.

In learning-oriented mode:
- explain before abstracting
- prefer full-sentence explanation over short point-form bullets
- introduce adjacent concepts step by step
- use simple comparisons and concrete examples
- avoid dropping unexplained jargon too early
- assume the reader may be seeing the topic for the first time

## Pre-Research Source Coverage Checklist

Before starting Round 1 foundational research, complete this checklist. Do not begin writing the report until at least 3 of the 5 boxes are checked.

```
□ Discovery layer: searched at least one non-official source (blog, newsletter, PR, community discussion) to find leads
□ Verification layer: found at least one official doc, whitepaper, or product page to confirm core claims
□ Judgment layer: found at least one independent source (not Gartner, not the vendor) that assesses or critiques the topic
□ China check: determined whether this topic has China-market relevance; if yes, executed at least one Chinese-language search
□ Counter-evidence check: actively searched for criticism, failure cases, or data that contradicts the dominant narrative
```

### AI Engineering authoritative source scan (mandatory for AI-related topics)

For any topic related to AI agents, AI reliability, LLM engineering, Harness Engineering, AI system design, evaluation/observability, or platform AI-native transformation, **before** running any `web_search`, actively scan the following authoritative sources directly using `web_fetch` or `site:` search.

**Why:** Web search finds content that is already widely cited. The most valuable first-hand engineering practices from AI labs are often published as engineering blog posts or GitHub docs that are not yet widely indexed at time of research. Waiting for web search to surface them means missing the original.

#### Tier 1 — First-hand engineering practice (always check for AI topics)

Use `web_search` with `site:` operator to scan each source:

| Source | Search pattern | What to find |
|--------|---------------|-------------|
| Anthropic Engineering Blog | `site:anthropic.com/engineering {keyword}` | Claude / Agent SDK / Harness design technical articles |
| OpenAI Research & Index | `site:openai.com {keyword}` | Official experiments, engineering reports |
| LangChain Blog | `site:blog.langchain.com {keyword}` | Agent framework engineering practices |
| Google DeepMind | `site:deepmind.google {keyword}` | Research and applied AI engineering |
| Meta AI Blog | `site:ai.meta.com/blog {keyword}` | Meta AI engineering and model practices |

If a Tier 1 source returns a result, **fetch the full article** using `web_fetch` before continuing to other sources. These are primary sources — treat them with the same weight as official docs.

#### Tier 2 — Official product and SDK documentation (check when implementation detail is needed)

| Source | What to find |
|--------|-------------|
| `docs.anthropic.com` | Claude API, Agent SDK, prompt guides, tool use |
| `platform.openai.com/docs` | OpenAI platform API, Assistants, function calling |
| `docs.langchain.com` | LangChain / LangSmith integration docs |
| `github.com/anthropics` | Anthropic open-source repos including Claude Code, skills |
| `smith.langchain.com` | LangSmith observability and evaluation docs |

#### Tier 3 — Discovery and community (after Tier 1 and 2 are checked)

Then proceed with standard `web_search` discovery.

#### Concept origin tracing rule

When a new term or concept is discovered (e.g., "Harness Engineering", "context anxiety", "Ralph Wiggum loop"), **always attempt to find the original source**:
1. Search for the exact phrase in quotes: `"concept name" site:blog.langchain.com OR site:anthropic.com OR site:openai.com`
2. If the term was coined by a specific person (engineer, researcher), find their original post or blog
3. Record the original definition separately from secondary analysis and commentary

Do not rely on Chinese summaries or third-party analysis for the definition of a new technical concept. Always trace back to the original author's words.

### China-language search requirement

If the topic has any of the following characteristics, the China check is mandatory:
- topic originated or has major adoption in the China market (e.g., Superapps, AI governance, platform engineering)
- topic involves products or vendors with significant China presence
- the user or organization is based in China

When the China check is required, execute at least one search in Chinese using patterns like:
- `{topic中文名} 中国 实践 案例`
- `{topic中文名} 落地 企业`
- `{topic中文名} site:36kr.com OR site:huxiu.com OR site:infoq.cn`

**Note on WeChat public accounts:** WeChat articles cannot be fetched by machine (returns environment error). Do not attempt to retry or find workarounds — this will stall research.

Instead, treat WeChat article titles and author names as **search leads only**:
- Take the article title or topic keyword and search for it on other platforms (Zhihu, Juejin, 36kr, InfoQ)
- If a similar article or discussion is found, use that as the source
- If nothing equivalent is found, move on — do not spend more than one search attempt on this

### Information retrieval tool priority

Use tools in this order based on the situation:

| Situation | Tool to use |
|-----------|------------|
| Standard web pages, blogs, docs | `web_fetch` |
| Pages with light anti-bot protection (36kr, Huxiu) | Jina Reader skill (`jina-reader`) |
| Pages with heavy anti-bot / JS-rendered content | Scrapling skill (`scrapling`) |
| WeChat public accounts | Cannot fetch directly — search for syndicated versions |
| Web search for discovery | `web_search` — include Chinese keywords when China check applies |

### Mandatory cross-validation

For any statistic, case study outcome, or market size figure that will be used as a key conclusion:
- identify the original source (not the article citing it)
- note the source type: primary analyst (Gartner/IDC/Forrester) vs. vendor-funded vs. independent research
- if the source is vendor-funded, add explicit note: "Source is vendor-published; treat with appropriate skepticism and seek independent corroboration"
- if only one source supports a key claim, mark it: "Single source; confidence: medium"

### Repeated topic handling

If this topic has been researched before (appears in multiple Gartner years or is a recurring theme):
- do not re-explain what was already established
- lead with: "What changed since the last research cycle"
- focus on new developments, updated maturity assessments, and revised judgment
- make the report self-contained without requiring the reader to have read prior versions

---

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

If the user's goal is first-time understanding, round 1 must also help them:
- understand why the concept appeared now
- distinguish it from nearby concepts
- understand each core capability with explanation and examples
- leave with a mental model rather than only a framework

### Default framework

Choose the default lens based on topic type:

For concept, system, platform, or capability topics, use:
1. definition and boundary
2. problem and drivers
3. scenarios
4. value logic
5. industry practices and representative approaches
6. implementation outline
7. limitations and tradeoffs when relevant
8. initial judgment and next-step recommendation

When the goal is first-time learning, expand this into:
1. what the term means in plain language
2. what exactly is being studied and what is not
3. why the concept emerged now
4. nearby concepts and differences
5. core capability blocks, each with explanation
6. concrete examples or mini-scenarios
7. current industry maturity
8. initial judgment and what to learn next

For internal technical product, platform-planning, governance, observability, diagnosis, or solution-design topics, use:
1. background and concrete pain points
2. quantifiable goals or target outcomes when possible
3. why traditional or generic approaches are not enough when relevant
4. current-state constraints and dependencies
5. existing platform split, reuse boundary, and build-vs-reuse judgment when relevant
6. overall solution or system flow
7. key design points, capability modules, or data/object model
8. concrete examples of schema, entity types, workflow steps, or object instances when available
9. concrete key objects to observe, govern, analyze, or control when relevant
10. design tradeoffs such as performance, complexity, maintainability, realtime versus offline split, or abstraction boundary when relevant
9. demand priority matrix, or at least module priority and urgency by user/business type when relevant
11. consumption form such as workbench, report, interface, or workflow when relevant
12. phased rollout, business landing targets, milestone expectation, scope boundary, and what is not covered yet
13. production rollout advice, implementation pitfalls, and next-step recommendation

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

For internal technical product, platform, governance, observability, diagnosis, or design topics, also cover when relevant:
- quantifiable targets
- why traditional or generic approaches are insufficient
- scope boundaries and non-goals
- upstream/downstream dependencies
- existing platform split and reuse boundary
- current gaps in data, tooling, or process
- concrete schema, entity, or module examples when available
- concrete key objects under management or observation
- key design tradeoffs and why a given split is preferred
- demand priority matrix or module/user priority when there is more than one major module
- workbench/report/interface consumption shape
- phased rollout path
- business landing targets or milestone expectations when the topic is initiative-oriented
- production pitfalls or rollout advice

For broad category or market-label topics, include at least:
- a judgment on whether the category is truly emerging, mostly marketing language, or just a feature layer
- at least 3 representative products, vendors, or substitutes when available

If the user's aim is learning rather than only scanning, do not stop at naming representative products. Explain what each representative product demonstrates about the category.

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

If the topic is closer to an internal technical product plan or solution design, do not stop at capability mapping. Also produce a plan-oriented structure covering:
- background
- target outcomes
- why common approaches are insufficient
- existing platform split and reuse boundary
- current constraints
- overall flow or architecture
- key design points
- concrete examples when available
- design tradeoffs and why the recommended split makes sense
- concrete managed or observed objects
- module priority or demand priority matrix when relevant
- consumption form
- phased rollout, landing targets, or milestone expectation

If the topic is about **AI Agent engineering, Agent reliability, Harness Engineering, or AI system stability**, treat the main research axis as:

`Agent failure modes → Harness capability layers (context / constraints / entropy) → measurement (eval harness / SLO) → PM ownership boundaries`

For these topics, explicitly cover when possible:
- what new failure modes emerge that traditional SRE/monitoring cannot detect (e.g. model drift, cognitive errors while system is operationally healthy)
- the three Harness Engineering capability layers and how they map to internal buildable capabilities
- the difference between "fixing the model" vs "adjusting the system" — and which is the PM's lever
- industry evidence of Harness-style improvements (prefer concrete benchmark data over general claims)
- who owns what: research/algo team vs SRE vs PM, and where PM's definition/measurement role is irreplaceable
- maturity signal: is this concept still exploratory, or are there production-grade practices to reference
- China-market adoption: is the concept being discussed domestically, and at what depth

If the topic is about **platform Agent-Native transformation** (how existing internal platforms evolve to be callable by Agents and accessible via conversational interfaces), treat the main research axis as:

`current platform design assumptions (human-facing GUI) → Agent-as-user shift → SKILL/capability layer design → conversational entry point redesign`

For these topics, explicitly cover when possible:
- why existing GUI-centric platform designs do not translate to Agent-callable interfaces
- the difference between "adding an AI assistant" and "redesigning user flow with conversation as primary path"
- SKILL design principles for Agent consumption: task-oriented vs feature-oriented, atomic capability decomposition
- what capabilities should be SKILL-ified first (frequency, value, boundary clarity)
- how conversational entry points should be designed: intent → Agent orchestration → SKILL execution → structured output
- PM's role in driving this: which decisions require PM leadership vs engineering execution
- maturity signal: what has been proven in industry vs what remains experimental

If the topic is specifically about AI application evaluation, AI evaluation platforms, or evaluation systems for AI applications, treat the main research axis as:

`observability -> trace data -> dataset -> evaluator -> experiment -> optimization/release loop`

Do not treat evaluation as an isolated module when the evidence indicates it depends on data return-flow, trace completeness, or platform integration.

For AI application evaluation topics, explicitly cover when possible:
- the difference between application evaluation and model evaluation
- why trace/data return-flow is the foundation
- what should be platform-owned versus business-owned
- how datasets, evaluators, evaluation objects, experiments, and release gates connect
- whether data loop or evaluation loop should be treated as the primary product backbone

## Learning-Oriented Writing Rules

Use this mode when the user is new to the topic or explicitly wants to learn first.

### Goals

The report should help a first-time reader:
- understand the concept without prior context
- build a usable mental model
- know why the topic matters
- understand the differences versus adjacent concepts
- understand the main capability blocks with examples

### Writing rules

- do not rely only on terse bullets
- explain each major point in 2-5 sentences when it introduces a new concept
- define a term before using it repeatedly
- when introducing jargon, explain it immediately in plain language
- use "for example" and mini-scenarios liberally when they improve comprehension
- prefer "this means..." and "in practice..." explanations
- do not jump directly from definition to judgment without explanation

### Preferred structure

1. plain-language definition
2. why this topic matters now
3. what problem it solves
4. how it differs from similar concepts
5. core capability blocks, each explained
6. one or more concrete examples
7. industry status and representative practices
8. current judgment and what to explore next

For platform, model, architecture, or data-model topics, do not stay at only the abstract layer when examples are available. Prefer including at least 2-5 concrete examples such as:
- entity or schema names
- relation examples
- workflow examples
- typical object instances
- source or discovery mechanism examples

When discussing architecture, also explain major tradeoffs when evidence supports it, for example:
- why graph versus relational or static config approaches differ
- why realtime versus precomputed paths are split
- why a middle layer is preferred over direct coupling
- why some modules should be reused instead of rebuilt

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

Also check:
- at least one Chinese-language source was consulted (if China check applies)
- at least one counter-evidence or failure case was searched for (even if none found — state that explicitly)
- repeated topics lead with "what changed" rather than re-explaining established context
- vendor-funded statistics are flagged as such
- capability map is present for capability-system topics (not substituted by bullet lists)

### Complexity warning requirement

For any topic where the implementation is non-trivial, include a **Complexity Warning** section covering:
- what organizations typically underestimate
- common failure modes in early adoption
- at least one documented case where adoption did not deliver expected results (if findable)

This section should be present even when the overall judgment is positive. Omitting it creates misleading optimism.

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

**Source type labeling (required for key statistics and case study outcomes):**

| Source type | Label to use in report |
|-------------|----------------------|
| Primary analyst (Gartner, IDC, Forrester) | No label needed |
| Independent academic / research institution | No label needed |
| Vendor-published study or press release | *(vendor-funded)* |
| Single source, unverified | *(single source; confidence: medium)* |
| Market size from non-primary analyst | *(source: [name]; verify with primary analyst)* |

When two sources conflict on the same claim, surface the conflict explicitly rather than picking one silently. Example: "GitHub reports 55% productivity gain; Google's independent study found 6%. The gap likely reflects different task types and measurement methods."

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
