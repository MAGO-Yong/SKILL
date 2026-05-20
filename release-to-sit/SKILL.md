---
name: release-to-sit
description: Use when the user asks to validate, build, push, deploy, or release code to SIT, especially when they expect Codex to complete the full workflow with minimal participation. Covers dependency repair, verification, commits, branch push, CI/build discovery, ONES deployment, and SIT smoke validation with a status table.
metadata:
  short-description: 验证、构建并发布到 SIT 的端到端流程
---

# Release To SIT

## Goal

Complete the full path from local code to a validated SIT deployment with minimal user involvement.
Default to acting from context. Ask the user only when a choice is genuinely ambiguous, security-sensitive, destructive, or blocked by external approval.

This skill is intentionally reusable. It must work for:

- personal independent projects on this machine;
- X-RAY product repositories;
- Xiaohongshu internal DevOps deployments;
- frontend-only, backend-only, and full-stack changes.

Current XRay AI Evaluation work is only an incubation case, not the default scope.

## Trigger

Use this skill when the user says:

- `验证发布到 sit`
- `发到 SIT`
- `构建发布`
- `发布一下`
- `我开发完了，帮我验证并发布`
- equivalent requests involving validation, build, branch push, ONES, service deploy, or SIT smoke test

Also activate this skill locally as a coding preflight whenever Codex is about
to write code in a repository that may later need SIT or production delivery.
In coding-preflight mode, run only the early non-deploy steps:

- identify repo, branch, remote, and target environment assumptions;
- detect duplicate/stale feature branches for the same task;
- confirm the canonical branch strategy before edits;
- inspect current diff scope and unrelated local changes;
- note expected validation/build/release path for later.

Coding-preflight mode must not build, push, create CR/MR, deploy, or ask for
production approval. It exists to keep branch, diff, and release assumptions
clean from the first code edit.

When the user says `发布生产`, `发 prod`, `上线`, or equivalent production
language, use this skill only for production readiness checks, version
selection, and manual handoff. Do not trigger production deploys or create prod
changeflows. Production is a manual user-owned release step and usually
requires human review, CR/MR approval, merge to `master`, production change
approval, and a production image/version selected from `master`.

If the request is XRay AI Evaluation related, also use the case notes in [references/xray-ai-eval.md](references/xray-ai-eval.md). Do not apply those repository paths, services, or smoke cases to unrelated projects unless the current request clearly points there.

## Applicability Labels

Every step should be interpreted through one or more labels:

- `[Universal]`: required for almost any repository or product release.
- `[Local Project]`: applies to personal/local projects, including plain Docker, local scripts, or GitHub-style workflows.
- `[XHS DevOps]`: Xiaohongshu-specific platform behavior such as ONES, RedCloud, HCMP, internal Maven/npm mirrors, company SSO, deployment groups, or changeflows.
- `[X-RAY]`: X-RAY product conventions and monorepo patterns.
- `[Case]`: current incubation examples, such as XRay AI Evaluation dataset/version work. Treat these as examples only.

When reporting status, include the relevant label when it helps explain why a step exists or why it is skipped.

## Interaction Policy

Do not make the user confirm every step.

Ask only for:

- Target ambiguity: cannot infer whether the target is local validation, SIT, beta, NJ, or production.
- Service ambiguity: multiple candidate services/apps are plausible and none is clearly indicated by repo history.
- Destructive or high-impact action: rollback, force push, merge to shared branch, delete environment, production release.
- Missing external access: login, 2FA, approval, or permissions that Codex cannot complete.
- Secret handling: credential source is unknown.

Otherwise proceed and keep the user informed with compact status updates.

User guidance mode:

- Assume the user should not have to remember the release process.
- At the start of any coding, validation, SIT, or production-readiness work,
  show a compact flow card: current goal, repo/branch, phase, what Codex will
  do automatically, and what the user may need to do manually.
- During execution, show only the current step, next step, and whether user
  action is needed. Do not dump the full 16-step flow unless the user asks.
- When user action is needed, provide concrete instructions: exact link, person
  or role to contact, copyable title/comment/description, and the signal that
  tells Codex it can continue.
- For production, user actions such as PingCode linkage, reviewer approval,
  protected `master` merge, and manual prod release must be labeled clearly as
  user-owned handoff steps.

Production exception:

- Production release is a high-impact action. Pause at the production gate and
  show what is ready, what is blocked by human/platform approval, and which
  exact item the user or reviewer must complete.
- Do not click/trigger production deployment and do not create production
  changeflows. The expected final output is a manual production release handoff
  for the user.
- If CR/MR approval, reviewer sign-off, PingCode/work item linkage, or merge to
  `master` is missing, mark the production step `blocked` and give the user the
  smallest actionable handoff instead of trying to work around it.

## Dry Run Mode

If the user asks to simulate, review, rehearse, or "do not really build/trigger",
run the same 16-step flow in dry-run mode.

Dry-run mode may run:

- repository status, diff, remotes, latest commit;
- `git diff --check`;
- tool versions and harmless environment probes;
- read-only Git remote checks;
- read-only platform metadata queries;
- script/manifest inspection.

Dry-run mode must not run:

- real build, package, publish, docker build, or image push;
- real tests if the user explicitly asked not to build/verify with execution;
- commit, push, merge, or branch mutation;
- deployment/changeflow creation;
- destructive operations.

For skipped execution steps, report the exact command that would be run and the
current evidence that suggests whether it is likely to pass.

## Credential And Permission Preflight

Before a real release, run harmless probes to distinguish "missing permission"
from "wrong command" or "empty result". Prefer these checks before asking the
user for login, token, password, or approval.

Universal probes:

- Git read: `git ls-remote --heads origin | head`
- Git push permission: `git push --dry-run origin HEAD`
- Package registry: read the configured registry and run a non-mutating install/build command where possible.
- Container daemon: `docker info --format '{{.ServerVersion}}'`

XHS DevOps probes:

- ONES login: `ones-cli auth status`
- ONES service read: `ones-cli meta services detail --service <service> -o json`
- ONES image read: `ones-cli meta images list --service <service> -o json`
- Service SIT deploy target: discover the service's `sit` deploy group from service metadata, deployment history, or platform UI.

Interpretation rules:

- The user's normal SIT release flow is direct service SIT deployment, not a
  personal test project/lane. Do not ask for a test project just because a CLI
  help page or `project list` mentions project-based deploy.
- `ones-cli project list` returning an empty list is usually irrelevant for the
  service SIT flow. It does not mean ONES is logged out.
- Do not run or report `npm whoami` by default. Only check npm login when the
  task includes publishing an npm package, refreshing private dependency
  credentials, or dependency install fails with an authentication error. If the
  repo can install/build from the configured registry, npm account login is
  irrelevant and should be skipped silently.
- Browser UI login is separate from CLI login. If a controlled browser reaches
  an enterprise login page, prefer CLI for release operations. Ask for browser
  login only when the workflow truly requires UI-only actions or visual smoke
  on an authenticated page.
- Never request or print raw tokens/passwords. If credentials are required,
  guide the user through the platform login flow, such as device code or SSO.

## Required Status Board

Maintain a status board while working. Update it when major state changes.

Statuses:

- `pending`: not started
- `running`: in progress
- `passed`: completed successfully
- `failed`: failed because of code/config and needs fixing
- `blocked`: cannot proceed without access, approval, or missing external dependency
- `skipped`: intentionally skipped with a reason

Minimum board:

| Step | Type | Status | Evidence / Next Action |
|---|---|---|---|
| 1. Intent | Universal | pending | target, scope, environment |
| 2. Repo And Branch | Universal | pending | cwd, branch, remote, ahead/behind |
| 3. Diff Scope | Universal | pending | files, diff stat, unrelated changes |
| 4. Toolchain | Universal / XHS DevOps | pending | project runtime, package manager, deploy CLI/browser |
| 5. Dependencies | Universal / XHS DevOps | pending | install/sync result, internal mirror status |
| 6. Static Checks | Universal | pending | diff check, lint, typecheck |
| 7. Tests | Universal | pending | unit/integration result |
| 8. Local Build | Universal | pending | frontend/backend/image build result |
| 9. Local Preview | Universal / X-RAY | pending | URL or skipped reason |
| 10. Commit And Push | Universal | pending | commit, branch, CR/MR |
| 11. CI Or Image | Universal / XHS DevOps | pending | pipeline or image tag |
| 12. Deploy Target | XHS DevOps / Local Project | pending | application/service/SIT deploy group or local target |
| 13. SIT Deploy | XHS DevOps | pending | changeflow and status |
| 14. Deploy Monitor | XHS DevOps / Universal | pending | success/failure/diagnosis |
| 15. SIT Smoke | Universal / X-RAY / Case | pending | URL/API/product behavior result |
| 16. Final Report | Universal | pending | summary and residual risks |

For production requests, replace steps 13-15 with the production gate:

| Step | Type | Status | Evidence / Next Action |
|---|---|---|---|
| 13P. Production Readiness Gate | Universal / XHS DevOps | pending | CR/MR approval, `master` merge, prod change window/freeze, release owner |
| 14P. Production Version Selection | Universal / XHS DevOps | pending | latest publishable `master` image/version candidates |
| 15P. Production Manual Handoff | XHS DevOps | pending | manual handoff or approval blocker |

Production readiness includes a branch consolidation gate before review:

| Step | Type | Status | Evidence / Next Action |
|---|---|---|---|
| 12P. Production Branch Consolidation | Universal | pending | one canonical branch, one CR/MR, no stale duplicate release branches |

## Decision Surfaces

Each step should expose the minimum information needed for the user to judge
what is happening. Do not create decorative tables when there is only one clear
fact. Use richer tables only when there are multiple candidates, risk tradeoffs,
or a real decision point.

Default output principle:

- One clear path: state the decision and evidence, then continue.
- Multiple plausible paths: show a compact comparison table and recommend one.
- Risk or ambiguity: show the risk, why it matters, and the smallest question
  needed to unblock.
- Repeated/noisy checks: skip silently unless they affect the decision.

Step-specific decision surfaces:

| Step | User-facing surface | Auto-continue when | Ask/stop when |
|---|---|---|---|
| 1. Intent | One-line intent summary: target, scope, environment | Target is inferable from context | Target could mean SIT vs PROD, deploy vs verify-only |
| 2. Repo And Branch | Repo table with path, role, branch, remote, ahead/behind | Feature branches and remotes are clean/expected | On shared/prod branch, detached HEAD, or ambiguous repo |
| 3. Diff Scope | Diff summary grouped by repo/module; call out unrelated changes | Diff matches requested scope | Unrelated risky changes would be included |
| 4. Toolchain | Capability checklist only for tools actually needed | Required tools pass harmless probes | Missing runtime, daemon, CLI login, or browser route |
| 5. Dependencies | Dependency source/status summary; no npm auth noise | Install/build can use configured sources | Dependency install fails due auth/network/missing mirror |
| 6. Static Checks | Check result list with exact failed command and classification | Checks pass or known repo-level debt has a safe fallback | Touched-file syntax/type failure |
| 7. Tests | Test matrix: command, scope, result, skipped reason | Relevant tests pass or intentionally skipped | Regression/failing test not explained |
| 8. Local Build | Build artifact summary: command, env, duration/result | Build passes or dry-run reports command only | Build fails |
| 9. Local Preview | Preview URL plus what was visually/API verified | Preview/smoke is accessible or not needed | Login/network blocks required product validation |
| 10. Commit And Push | Commit preview: staged files, message, target branch | Scope is clean and branch is expected | Staged files include unrelated changes or push would hit protected branch |
| 11. CI Or Image | Ranked version/image candidate table with recommended choice | One candidate clearly matches branch/commit and is publishable | Latest candidate does not match intended branch/commit |
| 12. Deploy Target | Target table: app/service/env/deploy group/SIT URL | Target is uniquely resolved from service metadata | Multiple services/groups or PROD-like target ambiguity |
| 13. SIT Deploy | Release plan: service, image, env, deploy group, command/UI path | SIT target and image are unambiguous | Production/destructive action or platform asks approval |
| 14. Deploy Monitor | Timeline/status board with stage, status, log link/diagnosis | Changeflow reaches success | Failure needs code/config fix or external approval |
| 15. SIT Smoke | Smoke checklist with pass/fail evidence per user-facing behavior | Critical behaviors pass | A critical behavior fails or cannot be checked |
| 16. Final Report | Final concise report: what shipped, evidence, residual risk | Always | N/A |

Production decision surfaces:

| Step | User-facing surface | Auto-continue when | Ask/stop when |
|---|---|---|---|
| 13P. Production Readiness Gate | Gate table: CR/MR status, reviewers, work item, merge commit, freeze window, SIT evidence | All gates pass and user already explicitly asked to continue to prod | Any gate needs reviewer/user/platform action |
| 14P. Production Version Selection | Ranked `master` image/version table with latest publishable version and matching merge commit | One latest publishable `master` candidate matches the merge commit | Candidate is from feature/SIT branch, stale, or ambiguous |
| 15P. Production Manual Handoff | Handoff card with exact links, version, owner action, and remaining blockers | Readiness and version are clear | Production deploy would need to be triggered by Codex |

For production branch consolidation, show a branch/CR table when multiple
branches or multiple CRs could contain the same feature. Recommend exactly one
canonical branch and mark the others as stale or already-merged.

For image/version selection, always use the ranked candidate surface. It should
answer "what is latest?", "is it publishable?", and "does it match my branch or
commit?" without requiring the user to inspect raw JSON.

## Step Guide

### 1. Intent

Type: `[Universal]`

Infer intent from the request.

Default mapping:

- "看看能不能发" -> validate only unless prior context says release is desired.
- "验证发布到 SIT" -> validate, commit, push, build, deploy to SIT, smoke test.
- "上线/生产" -> run production readiness checks, then pause at the
  production gate unless the user explicitly confirms the final production
  deployment target and all gates pass.

For personal/local projects, infer whether the user wants only local validation, a local deploy, or a remote release.
For Xiaohongshu/X-RAY projects, infer whether the target is SIT, beta, NJ, PROD, or only branch/CI.

### 2. Repo And Branch

Type: `[Universal]`

For every affected repo:

- Run `git status --short --branch`.
- Run `git remote -v`.
- Run `git fetch origin` when network is available.
- Confirm branch is a feature branch unless the user explicitly asked for shared branch work.
- Detect near-duplicate feature branches for the same task before commit, build,
  CR/MR, or deploy. Examples include `feat/foo` and `feat-foo`, or old branch
  names left from earlier iterations. Pick one canonical branch, report it in
  the status board, and do not create/push/build from a second branch for the
  same change. If a stale remote branch could confuse CR/MR or release image
  selection, ask once before deleting it, then remove both local and remote stale
  refs after confirmation.
- Do not merge to `master`, `deploy_sit`, or production branches unless explicitly requested.

For multi-repo work, classify each repo as frontend, backend, library, infra, docs, or test fixture before running validation.

### 2P. Production Branch Consolidation

Type: `[Universal]`, plus `[XHS DevOps]` when CR/MR and work items are on
internal platforms.

Use this section before production readiness when development lasted multiple
days or involved multiple pushes, branches, CRs, SIT builds, or backend/frontend
repos.

Goal: one production candidate branch, one CR/MR per repo, then merge to
`master`.

Checklist:

- Fetch all remotes and list branches that look related to the feature by name,
  commit ancestry, or CR/MR links.
- Identify the canonical branch that should represent the production candidate.
- Verify all intended commits are on the canonical branch.
- Verify unrelated dependency/build/mock/debug changes are not included unless
  explicitly intended.
- Compare canonical branch against `origin/master` with `git diff --stat` and
  critical file spot checks.
- If multiple branches contain overlapping work, do not open or update multiple
  CRs. Pick one canonical branch and mark the rest stale. Ask once before
  deleting remote stale branches.
- Open or update exactly one CR/MR from the canonical branch to `master`.
- Link required PingCode/work items if the platform requires them. If Codex
  cannot create or link the work item because of platform permission or missing
  product context, produce a handoff with the exact CR link and needed item
  title/type.
- Ask the user/reviewer owner to complete review approval. Codex can summarize
  diffs and address comments, but it must not fake approval.
- After review is complete and the protected branch merge happens, verify:
  `git fetch origin` and `git merge-base --is-ancestor <canonical-tip> origin/master`.

Recommended branch table:

| Branch | Role | Tip | CR/MR | Diff To Master | Action |
|---|---|---|---|---|---|
| `<branch>` | canonical | `<sha>` | `<link>` | `<summary>` | keep / update CR |
| `<branch>` | stale | `<sha>` | `<link-or-none>` | overlaps canonical | delete after user confirms |

If the branch is already merged, report the merge commit and proceed to
production version selection. If it is not merged, mark production as `blocked`
with the needed reviewer/work item/merge action.

### 3. Diff Scope

Type: `[Universal]`

- Run `git diff --stat`.
- Inspect changed files relevant to the request.
- Stage only files related to the current task.
- Never revert unrelated user changes.

For generated artifacts, decide whether they are intended release artifacts or local build noise. Exclude local build output such as `target/`, `dist/`, coverage, and caches unless the repo intentionally tracks them.

### 4. Toolchain

Type: `[Universal]`, plus `[XHS DevOps]` when internal release tools are involved.

Check required tools before validation:

- Frontend: Node plus the repo package manager, such as npm, pnpm, yarn, or bun.
- Backend: Java/Maven/Gradle, Go, Python, Rust, or the runtime declared by the repo.
- Container: Docker or OrbStack daemon if image build or image inspection is required.
- Internal release: ONES/RedCloud/HCMP CLI or authenticated browser session when required.
- Browser: Browser or Chrome login if smoke testing or platform UI operation needs cookies.

If a required tool is missing, install or switch it. On macOS prefer Homebrew when available. Prefer project wrappers before global tools.

Do not assume a tool is usable just because the binary exists. Verify one harmless real command, for example `docker info`, `mvn -version` under the intended Java version, or `ones-cli meta ...`.

Probe the runtime that the real command will use, not a misleading global
default. For example, if a Java project requires Java 11 and has a helper such
as `scripts/java11-env.sh`, source that helper before checking `java -version`
or `mvn -version`. Do not surface a naked macOS Java shim failure as a blocker
when the project-specific runtime path works.

### 5. Dependencies

Type: `[Universal]`, plus `[XHS DevOps]` for internal mirrors/registries.

- Frontend: use the repo `packageManager`; install with lockfile-respecting commands.
- Backend Maven: prefer `./mvnw`; otherwise use `mvn`.
- Backend Gradle: prefer `./gradlew`.
- If install fails due network, retry once; if still failing, record the exact dependency/resource and mark blocked.

For Xiaohongshu repos, check internal npm/Maven/Gradle/Docker registry configuration before treating dependency resolution as a code issue.
For personal projects, prefer public registry defaults unless the repo pins a mirror.

### 6. Static Checks

Type: `[Universal]`

Always run:

- `git diff --check`

Then run project checks:

- Frontend: lint/typecheck for touched package when configured.
- Backend: compile or test command that catches Java syntax and dependency errors.

If a repo-level lint command fails because of known existing config incompatibility, run the smallest alternative check and record the original failure as a repository issue.

Do not let a known repo-wide lint debt mask syntax failures in touched files. Use targeted checks where possible.

### 7. Tests

Type: `[Universal]`

Run relevant unit/integration tests when available.
If no tests exist or the command is not configured, mark `skipped` with a reason.

Classify failures:

- code regression: fix before release;
- missing local service or database: mark blocked or use CI if that is the accepted project gate;
- flaky/existing failure: record evidence and avoid silently treating it as success.

### 8. Local Build

Type: `[Universal]`

Run the environment-relevant build:

- Frontend: app/package build for the target environment.
- Backend: compile/package/build command for the target runtime.
- Container: image build when the release path depends on a local image.
- Static site or personal project: artifact generation command, if any.

Do not proceed to deploy after a genuine build failure. Fix first.

### 9. Local Preview

Type: `[Universal]`, plus `[X-RAY]` for logged-in product pages.

For UI changes, start or reuse a local dev server when feasible and give/verify the URL.
For backend-only changes, prefer API-level checks if the service can run locally.

For X-RAY/internal products, use Chrome when login state, SSO, or internal domains are needed. Use Browser for localhost or simple local previews.

### 10. Commit And Push

Type: `[Universal]`

- Stage only relevant files.
- Use clear conventional commits.
- Push the current feature branch.
- Capture commit hash and CR/MR link from git push output or platform query.

For user-owned local projects, pushing may be optional. For company release flows, pushing the feature branch is usually required before CI/image generation.

### 11. CI Or Image

Type: `[Universal]`, plus `[XHS DevOps]` for internal CI/image systems.

After push:

- Query CI/build status where possible.
- Query image list for the service.
- Select the image/tag that corresponds to the just-pushed branch/commit.
- If the platform builds images asynchronously, poll until success/failure.

For personal projects, this may mean GitHub Actions, a Docker image tag, or no CI at all.
For Xiaohongshu projects, prefer platform metadata over guessing from image names.
For frontend packages that use a platform publish CLI, inspect package scripts
such as `formula publish`, `formula build`, or internal pipeline links before
assuming the backend image flow applies.

When a deployable image/version must be chosen, present a small ranked candidate
table before asking or deploying. The table should make the latest usable option
obvious.

Recommended format:

| Rank | Image / Version | Created At | Branch / Commit | Status | Recommendation |
|---|---|---|---|---|---|
| 1 | `<tag>` | `<time>` | `<branch>` / `<sha>` | publishable | latest, recommended |
| 2 | `<tag>` | `<time>` | `<branch>` / `<sha>` | publishable | fallback |

Rules:

- Show the top 3-5 publishable candidates.
- Mark the newest publishable candidate as recommended by default.
- If there is a just-pushed branch/commit, prefer the image matching that
  commit over a merely newer unrelated image.
- Show non-publishable candidates only when explaining why they are skipped.
- Ask the user to choose only if multiple plausible candidates remain or the
  latest image does not match the intended branch/commit.
- If the user says "就发最新的", deploy the newest publishable image matching
  the target service/environment.

### 12. Deploy Target

Type: `[XHS DevOps]` for ONES/RedCloud/HCMP, `[Local Project]` for local or personal deployments.

Determine:

- application
- service
- environment
- workload group
- release flow or changeflow

For Xiaohongshu SIT release, the primary path is direct service SIT deployment:
find the service's SIT deploy group, select the image/tag, and create or open
the service SIT release flow. Do not route through personal test projects unless
the user explicitly asks for a lane/project release.

For personal projects, this may instead be a local port, Docker Compose service, cloud app, server path, or static hosting target.
For X-RAY projects, identify product module, frontend package, backend service, SIT URL, and any required mock/proxy mode.

### 13. SIT Deploy

Type: `[XHS DevOps]`

Use ONES CLI if it has all required parameters.
If CLI cannot express the current platform flow, use Chrome with the user's logged-in session.

Record:

- service
- environment
- workload group
- image tag
- changeflow URL/name

If the user says they will publish manually, stop at branch/build readiness and provide exact branch, commit, image, and validation evidence.

If the installed `ones-cli` only exposes project-style deploy flags such as
`--project`, do not ask the user for a project by default. Instead treat it as a
CLI capability mismatch for the desired service SIT flow: inspect service
metadata and image tags, then use the direct service SIT release command if
available in a newer CLI, or use the authenticated platform UI. Ask the user
only if the service, SIT deploy group, image tag, or release target is still
ambiguous.

### 13P. Production Readiness Gate

Type: `[Universal]`, plus `[XHS DevOps]` for internal production releases.

Use this section when the target is production.

Production is not the same as SIT. Before any production release, verify and
report:

- The code was reviewed in CR/MR and required reviewers approved it.
- Required work items such as PingCode/需求/提测 items are linked when the
  platform requires them.
- The feature branch has been merged to `master` or the production branch
  required by the project.
- The production candidate is based on `master`, not the old feature branch or
  a SIT-only image.
- SIT/BETA/NJ validation evidence exists when the team process requires it.
- Code freeze/change window does not block production.
- The production service/application/deploy group is unambiguous.
- The user or designated release owner has done any required human action:
  reviewer approval, risk acceptance, CAB/change ticket, release window
  confirmation, or manual platform click.

If any item is missing, mark production as `blocked` and provide a handoff:

```text
Production blocked:
- Missing: <reviewer approval / master merge / work item / freeze approval>
- User action: <ask reviewer X to approve / merge CR / select prod image>
- Codex can continue after: <specific observable condition>
```

Do not try to bypass these gates. They are organizational controls, not tool
failures.

### 14P. Production Version Selection

Type: `[Universal]`, plus `[XHS DevOps]` for internal image/version systems.

After `master` merge, discover production-eligible images or versions and show
the ranked candidate table. The recommended production candidate should match
the `master` merge commit or a later `master` build that includes it.

Never recommend a feature branch image for production unless the user explicitly
accepts that exception and the platform/team allows it.

Recommended format:

| Rank | Image / Version | Created At | Source | Commit | Status | Recommendation |
|---|---|---|---|---|---|---|
| 1 | `<tag>` | `<time>` | `master` | `<sha>` | publishable | recommended |
| 2 | `<tag>` | `<time>` | `<feature>` | `<sha>` | SIT-only | do not use for prod |

### 15P. Production Manual Handoff

Type: `[XHS DevOps]`

Production publishing is manual and user-owned. Stop after readiness and version
selection. Provide:

- product/service name
- production target
- CR/MR link and merge commit
- recommended `master` image/version
- SIT validation evidence
- exact remaining manual steps

Do not trigger the production deploy from Codex. If the user later asks for a
production action, explain that production is intentionally a manual handoff
flow and provide the exact platform page, version, and checklist again.

### 14. Deploy Monitor

Type: `[Universal]`, plus `[XHS DevOps]` for changeflow details.

Poll deployment detail until terminal state.
On failure, fetch diagnosis/logs, classify cause, and fix/retry when it is code/config/tooling.

For non-XHS projects, monitor the equivalent pipeline, service logs, health endpoint, or hosting dashboard.

### 15. SIT Smoke

Type: `[Universal]`, with optional `[X-RAY]` or `[Case]` checklists.

Verify the deployed behavior, not only the deployment status.

Use:

- product SIT URL
- API endpoint checks
- browser UI path checks
- network console checks when relevant

Use case-specific smoke lists only when they match the current product area. Do not run XRay AI Evaluation smoke checks for unrelated X-RAY modules or personal projects.

### 16. Final Report

Type: `[Universal]`

Final answer must include:

- final deployment status
- branch and commit
- CR/MR links
- build/check results
- deployment/changeflow links
- SIT smoke evidence
- skipped/blocked items and why
- concrete next action if anything remains
