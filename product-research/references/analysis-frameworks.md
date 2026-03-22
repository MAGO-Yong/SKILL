# Analysis Frameworks

Use these as default lenses. Do not force every section into every report; select what helps answer the user's question.

## Round 1 Default

Use this order unless the user asks for something else:

1. Definition and boundary
2. Problem and drivers
3. Scenarios
4. Value logic
5. Industry practices and representative approaches
6. Implementation outline
7. Initial judgment and next-step recommendation

## Learning-Oriented Concept Research

Use when the user is unfamiliar with the topic and wants to understand it first.

Use this order unless the user asks for something else:

1. Plain-language definition
2. What this topic is and is not
3. Why it appeared now
4. What problem it solves
5. Difference from adjacent concepts
6. Core capability blocks, each explained in full sentences
7. Concrete examples or mini-scenarios
8. Industry maturity and representative practices
9. Initial judgment and suggested next deepening path

Rules:
- explain before compressing
- prefer examples over abstract labels
- do not assume prior familiarity
- keep enough detail that a first-time reader can follow

## Round 2 Default For Initiative / Proposal Work

Use this order unless the user asks for something else:

1. Background
2. Problem
3. External practices
4. Internal state and gap
5. Direction or solution path
6. Risks and prerequisites
7. Recommendation and next actions

Overlay this lens where helpful:
- current state
- gap
- opportunity
- path

## Internal Technical Product / Solution Planning

Use when the topic is about a platform, governance mechanism, observability system, diagnosis engine, workbench, map, evaluation platform, or internal product design.

Use this order unless the user asks for something else:

1. Background and concrete pain points
2. Quantifiable goals
3. Why traditional or generic approaches are not enough
4. Constraints, prerequisites, and dependencies
5. Existing platform split, reuse boundary, and build-vs-reuse judgment
6. Overall solution or workflow
7. Key design points, data model, state model, or capability structure
8. Concrete schema or object examples when available
9. Concrete managed or observed objects
10. Design tradeoffs and why this split is preferred
11. Demand priority matrix or module urgency when relevant
12. Consumption form such as page, report, interface, or workbench
13. Scope boundaries, phased rollout, and milestone expectations
14. Production rollout advice, risks, and next actions

When the topic is initiative-oriented, also ask:
- which existing internal platforms already own adjacent capability
- what should be reused versus rebuilt
- which user group or business line should land first
- what module priority is implied by real demand urgency
- what concrete examples make the model or architecture easier to understand
- what design tradeoffs should be explained so the audience trusts the solution

## AI Application Evaluation Planning

Use when the topic is about AI application evaluation, evaluation platforms, evaluation workbenches, or app-level evaluation systems.

Use this main axis:

1. Why application evaluation is needed
2. Boundary versus model evaluation
3. Why observability and trace return-flow are foundational
4. Current user pain points by business type
5. Existing platform split and reuse boundary
6. Core loop:
   observability -> data return-flow -> dataset -> evaluator -> experiment -> optimization or release gate
7. Concrete examples of trace fields, dataset samples, evaluator types, or experiment objects when available
8. Module priority:
   dataset / evaluator / evaluation object / experiment analysis / release gate
9. Platform-owned versus business-owned responsibilities
10. Product consumption form
11. Business landing targets and milestone plan

Prefer treating the data loop as the platform backbone rather than describing each module as fully independent.

## Example Density And Tradeoff Explanation

Use when the topic is platform-heavy, model-heavy, or architecture-heavy.

Prefer:
- 2-5 concrete examples rather than only abstract categories
- object-level examples rather than only layer names
- explicit explanation of major tradeoffs rather than only presenting the chosen design

Examples of useful tradeoffs to explain:
- static versus dynamic model
- direct query versus middle-layer query
- online computation versus precomputation
- build versus reuse
- unified schema versus local customization

## Supporting Lenses

Use these selectively:

### Composite Topic Parse

Use when the topic is a short compound phrase and the meaning could split in multiple directions.

Break the topic into:
- research object
- research lens
- user goal
- possible structural interpretations

Test at least:
- A for B
- B for A
- A/B as a category term

Lock the working definition only after the user confirms.

### Internal Term Safe Mode

Use when the topic appears to be an internal codename, internal methodology, or internal product name.

Do:
- state that the term may be internal-only
- avoid inventing a public meaning
- ask for the minimum context needed to continue
- if context is unavailable, produce a constrained note covering possible boundaries, likely object type, and the questions that must be answered next

Do not:
- map the term too quickly to a nearby public concept
- pretend certainty when the term is clearly organization-specific

### Scenario - Value - Constraint

Use when deciding whether a scenario is worth prioritizing.

Ask:
- who uses it
- what problem is solved
- what value is created
- what must be true for the value to hold

### User - Problem - Alternative - Value

Use when the topic is a product opportunity, user-facing product, or consumer-facing direction.

Ask:
- who the target user is
- what job, pain point, or unmet need exists
- what alternatives users already have
- why this product could create differentiated value

Also ask:
- why users would return repeatedly
- what the likely entry wedge is

### Market - Competition - Monetization

Use when the request needs more than capability analysis.

Ask:
- what market or adoption signals exist
- who the obvious competitors and substitutes are
- what business model or monetization path is plausible
- what this implies for the product direction

Also ask:
- whether the category is real, emerging, or mostly a packaging label
- what 3 or more representative products best anchor the space

### Build - Buy - Integrate

Use when the topic is initiative-oriented, platform-oriented, or capability-construction oriented.

Ask:
- should this be built internally
- should it be bought or adopted from an external platform
- should it be integrated rather than platformized
- what org maturity is required for each path

### Track - Player - Capability - Entry Point

Use when the request is strongly competitive or market-route oriented.

Ask:
- what track or category is forming
- who the representative players are
- what capabilities define the route
- what entry point seems most viable

### Capability System Map

Use when the topic is about a capability framework, platform ability, operating system, lifecycle system, or construction direction.

Ask:
- what the target object is
- what layers the system has
- what the core modules are
- which modules are foundational
- which modules are upper-layer product functions
- which representative products map to each layer
- what the likely evolution order is

### Current State - Gap - Opportunity - Path

Use when the topic is close to internal initiative planning.

Ask:
- what exists today
- what is missing
- where the most practical opportunity lies
- what path is realistic
