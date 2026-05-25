---
name: xray-frontend-dev
description: Frontend delivery guidance for the xray monorepo. Use as lightweight coding conventions during normal frontend development, and as an explicit workflow only when the user asks for complex planning, validation, build, branch push, SIT release, production preparation, or MR/CR handoff.
---

# Xray Frontend Dev

## Overview

Use this skill as frontend delivery guidance for the xray monorepo.
Normal development is not a release/audit workflow. When the user asks for UI tweaks, bug fixes, or local iteration, apply the coding conventions quietly, move quickly, and do not present a process checklist. Escalate to the full workflow only when the user explicitly asks for validation, build, branch push, SIT release, production preparation, or MR/CR handoff.

## Workflow

1. For normal development, implement directly with the smallest safe change.
2. Check local environment only when it blocks coding or preview.
3. Run the smallest validation that matches the risk.
4. Start or reuse the local environment and give the user a manual verification URL when visual verification is useful.
5. Only for complex or ambiguous changes, analyze the request and write a concise requirement document.
6. Ask for confirmation only when scope, behavior, data contract, or release target is unclear.
7. Write the technical plan with a minimum-change approach only when the change has cross-page, cross-module, backend/API, build, release, or production impact.
8. Verify in SIT or BETA only when the user explicitly asks for deployment validation.
9. Verify in the NJ environment only when the user explicitly asks for NJ validation.
10. When the user says things like `提交 MR`, `提 MR`, or other equivalent release-preparation requests, automatically run the production release preparation flow.

Do not force confirmation gates for a small concrete UI fix such as spacing, truncation, scroll behavior, table height, label style, or a copy tweak in one known component.
Do not run full build/test by habit for tiny style-only edits while the user is actively iterating. Prefer `git diff --check` plus targeted local visual verification; run package build when the user asks for build readiness, SIT release, production preparation, or when the edit touches shared layout or compile-sensitive script/template logic.

## Environment Delivery Workflow

Use this section when the task needs environment-level verification or production preparation after local development.

### Test Environment Verification

Support both SIT and BETA validation.

#### SIT Test Environment Verification

- First run the scoped frontend release checklist in this skill.
- Then use `release-to-sit` to classify the actual release target: frontend
  Docker service, FE static platform package, backend service, or full-stack.
- For XRay service SIT, default to the direct service SIT path and its image /
  workload prevention gates. Do not use personal lanes, test projects, or
  `deploy_sit` branch merges unless the user explicitly asks for that path.

#### BETA Test Environment Verification

- Treat BETA like SIT with a different target environment: run the scoped
  frontend release checklist, then use `release-to-sit` target discovery for
  the correct service/artifact path.
- Do not merge into `deploy_beta` unless that branch is explicitly requested
  and confirmed as the team's current BETA release path.

### NJ Environment Verification

- NJ is environment-specific and can be production-like. Only verify NJ when
  the user explicitly asks for NJ.
- Use `release-to-sit`/production handoff rules to classify whether this is a
  test deployment or production-controlled release. Do not merge into
  `deploy_nj` or trigger a production release unless the user explicitly asks
  for that exact path and the production gates are satisfied.

Treat this path as mandatory when the task explicitly requires NJ validation.

### Production Release

- When the user says things like `提交 MR`, `提 MR`, or other equivalent release-preparation requests, automatically do the following:
1. Check whether the current branch is the canonical feature branch for this
   change and whether the working tree is clean.
2. Run the repo's Changesets version flow from the root of that branch.
3. Select only the owning application/package and the smallest appropriate
   semantic version bump unless the user explicitly requested a broader release.
4. Commit the generated changes again and push to remote.

Do not skip the versioning step for real production release work.

### Scoped Frontend Release Checklist

Use this checklist before pushing a frontend branch for SIT, CR, or production preparation.

1. Start from the current target branch, usually `origin/master` for production
   preparation, and use a canonical feature branch name without `/` so CI
   Docker tags do not become invalid.
2. Inspect `git diff --name-status origin/master..HEAD` before versioning. The
   diff must contain only the owning feature package/module plus intentional
   release metadata. First identify the owning module from the request,
   route, changed files, or existing package ownership, then use that module
   as the business-file allowlist.
3. Treat these as out of scope unless the user explicitly asks for them:
   dependency spec changes, lockfile churn, non-owning packages/modules,
   root/package lint config, global request utilities, and unrelated common
   styles.
4. If lint or build fails because of global config or environment issues, report
   that separately. Do not "fix" it by changing platform-level contracts in a
   feature branch unless that is the actual requested task.
5. Generate the frontend version with Changesets. Select only the owning app
   package, for example `x-ray-next`, and choose the smallest correct bump,
   usually `patch` for a frontend bug fix.
6. After `changeset version`, review the new diff again. The allowed release
   metadata should normally be limited to the owning package's `package.json`
   and `CHANGELOG.md`, or that package's documented equivalent release files.
   Do not accept unrelated dependency version changes just because the version
   command printed warnings.
7. Run `git diff --check` and the owning package build, for example
   `pnpm -F x-ray-next run build:test`. Run targeted lint only when the repo's
   current lint config supports it; if current master's lint config itself is
   incompatible with the installed ESLint version, do not edit global lint config
   to make a feature branch pass.
8. Commit in separated layers when useful: business fix first, scope cleanup if
   needed, then version/changelog. Push only after the final diff review still
   matches the allowed scope.

### Diff Scope Triage

Use this triage whenever a frontend release branch contains surprising files.
The default is to remove them from the release branch, not to justify them after
the fact.

Before using the table, determine the owning business scope. Examples:
`packages/xray-main/src/pages/<page-or-feature>/**` for main-app pages,
`packages/xraygraph/**` for graph app work, `packages/x-pilot/**` for X-Pilot
package work, and `packages/xray-layout/**` only for shared layout/nav work.
The owning scope changes per task; do not hard-code the previous feature module
as the allowlist.

| File Pattern | Default Decision | Exception |
|---|---|---|
| owning module files | allowed | still review for unrelated formatting-only churn |
| owning package `package.json` | allowed only as a separate version commit | must be generated by Changesets or clearly equivalent |
| owning package `CHANGELOG.md` | allowed only as release metadata | must match the selected package version |
| package/root lint config | reject | allowed only for an explicit lint-config task |
| global request/router/store utilities | reject | allowed only when the requested bug is global infrastructure behavior |
| other packages/modules | reject | allowed only when the feature explicitly owns cross-package changes |
| `pnpm-lock.yaml` | reject for pure frontend UI work | allowed only after dependency/specifier changes are intentional and reviewed |
| common/global styles | reject | allowed only when the request is explicitly global styling |
| mock/debug/demo/sample/test-fixture files or data | reject for release branches | allowed only when the task explicitly ships mock tooling and it is gated away from production |

If a validation command only passes after editing a rejected file, stop and
report the real validation blocker. Do not broaden a feature release by
changing global config, dependencies, or shared utilities.

### Mock And Debug Data Guard

Before pushing, creating CR, building for SIT, or preparing production, inspect
both the changed file list and the changed content for accidental mock/debug
payloads.

Check for:

- file or folder names containing `mock`, `mocks`, `fixture`, `fixtures`,
  `demo`, `sample`, `fake`, `debug`, `test-data`, or equivalent Chinese names
  such as `测试数据` and `示例数据`;
- hard-coded fake ids, fake users, fake tokens, fake project ids, temporary API
  responses, local JSON blobs, local fallback lists, or generated sample rows;
- dev-only switches such as `IS_MOCK`, `USE_MOCK`, `DEBUG`, `localMock`,
  forced env overrides, or comments like `TODO remove before release`;
- local-only assets, screenshots, CSV/JSONL samples, or fixtures added during
  UI debugging.

Default action:

1. Remove mock/debug/test data from the release diff.
2. If the feature genuinely needs mock support, keep it behind an explicit
   development-only switch that cannot activate in SIT/production by default.
3. Report any retained mock-related file in the release readiness summary with
   why it is safe.

### Platform Contract Guardrail

Feature work must not change platform-level contracts just to make one module
lint, build, or release. This applies even when the changed file is not listed
in the triage table.

Treat a file or setting as platform-level when changing it can affect unrelated
X-RAY modules, packages, builds, runtime behavior, or release pipelines.
Examples include:

- lint, formatter, TypeScript, Babel, Rspack/Vite/Webpack, Formula, Changesets,
  package manager, workspace, Docker, CI/CD, or root config;
- dependency ranges, lockfiles, package manager metadata, registry settings,
  postinstall/build scripts, or monorepo workspace topology;
- shared request, auth, routing, menu/layout, telemetry, error handling,
  environment detection, storage, permission, or global state utilities;
- global styles, theme tokens, Delight overrides, shared component primitives,
  CSS resets, typography, spacing, z-index, overlay, or table defaults;
- shared assets, generated API clients, service definitions, deployment
  manifests, ONES/RedCloud/HCMP configuration, or release scripts.

If a feature appears to require a platform-level change:

1. Stop and classify it as a separate platform task.
2. Explain the blast radius and why the feature cannot be solved locally.
3. Ask for explicit user approval before changing the platform contract.
4. Commit it separately from the feature change.
5. Validate at the broader scope that could be affected, not just the feature
   page.

For a normal feature release, prefer adapting the owning module to the existing
platform contract, or record the repo-wide blocker as skipped/blocked evidence.

### Release Readiness Report

Before saying a XRay frontend branch is ready for SIT, CR, or production
handoff, include these facts in the final status:

- branch and latest commit;
- package/version, for example `x-ray-next@7.6.50`;
- exact changed file list relative to `origin/master`;
- whether version metadata was generated by Changesets;
- validation commands and results;
- known skipped/blocked checks, such as current-master lint config
  incompatibility;
- CR/MR link or the exact manual handoff link when available.

Avoid saying "发布完成" when only code was pushed, a static artifact was
uploaded, a CR was opened, or a dry-run/read-only check passed.

## Local Environment Check

Perform these checks before requirement analysis when the task needs coding, debugging, local startup, or package validation.

### Hosts

1. Inspect `/etc/hosts`.
2. If there is neither a mapping from `0.0.0.0` to `local.xiaohongshu.com` nor a mapping from `127.0.0.1` to `local.xiaohongshu.com`, help the user add both of them.
3. Explain why it is needed before requesting escalation or telling the user the next step.

Project fact:
- `packages/xray-main/formula.config.ts` uses `local.xiaohongshu.com` as the dev host.
- The main app dev URL is typically `http://local.xiaohongshu.com:1391`.

### Node.js and Package Manager

1. Check whether Node.js is installed.
2. If Node.js is missing, install a compatible version based on `package.json`.
3. Prefer the most specific project guidance when there is a difference between loose engine ranges and README examples.

Project fact:
- Root `package.json` declares `engines.node` as `>=18`.
- The repo README and package READMEs explicitly recommend `node 18.20.7` and `pnpm 8.15.8`.

Default rule:
- Install or switch to `Node.js 18.20.7` unless the user already has a compatible Node 18 environment and the task does not require changing it.
- Keep `pnpm 8.15.8` in mind when environment mismatch explains install or dev issues.

### Dependency Install

If dependencies are missing and the task requires running the app or validation, install from the repo root with `pnpm install`.
Do not run heavyweight installs unless the task needs them.

## Requirement Document

Write a concise requirement document after reading the relevant package and local code.
The document should be understandable to any function, not just engineers.

Include:
- Background and user goal
- In-scope changes
- Out-of-scope items
- Affected pages, packages, and modules
- User-visible behavior changes
- Edge cases or risk points
- Acceptance criteria

After writing it:
1. Present it to the user as the current understanding.
2. Ask for explicit confirmation.
3. Wait for a clear response such as “确认”, “可以”, or equivalent.
4. Do not generate the technical方案 before that confirmation.

## Technical Plan

After requirement confirmation, write a technical plan that follows the minimum-change principle.

The plan must:
- Avoid impacting existing features
- Reuse the existing package structure, framework, state model, styles, and utilities
- Reuse in-repo components and helpers before introducing new abstractions
- Prefer existing `@xhs/delight` components for UI when the page does not already rely on another component system
- Preserve the established visual language of the target package or page
- Keep changes local to the owning package unless the logic clearly belongs in a shared package

Include:
- Change entry points
- Key data flow or state updates
- Reuse plan for existing components, composables, stores, or utilities
- Validation plan
- Known risks and how to contain them

After writing it:
1. Present it to the user.
2. Ask for explicit confirmation.
3. Wait for a clear response.
4. Do not implement before that confirmation.

## Package Selection

Choose the owning package before editing:
- `packages/xray-main`: main product app, most feature and page work, `pnpm run dev:main`
- `packages/xraygraph`: graph and dashboard app, `pnpm run dev:graph`
- `packages/x-pilot`: pilot and AI-related Vue package, usually `pnpm -F @xhs/x-pilot exec formula dev`
- `packages/xray-layout`: shared top nav and side menu
- `packages/shared`: shared components and shared utilities
- `packages/click_visual_ui`: separate React/Umi app, use its own `npm run dev` or package-local dev script

Prefer editing the feature-owning package first.
Only change shared packages when reuse is clearly justified.

## Implementation Rules

### UI and Interaction

- Keep the existing page style visually consistent before optimizing for novelty.
- Prefer `@xhs/delight` components and tokens for common controls, layout, feedback, color, and spacing.
- When the target page already uses another component library, stay consistent with the existing page unless the task explicitly includes migration.
- UI must conform to Delight component library conventions unless the touched page has an explicit, incompatible legacy pattern.
- Colors, spacing, border radius, shadows, states, and typography must use existing Delight variables/tokens or in-repo semantic variables first. Do not introduce arbitrary hex colors, magic spacing, or one-off visual styles when a Delight token or existing local variable exists.
- Reuse Delight components for buttons, inputs, selects, tags, drawers, tables, pagination, tooltips, empty states, loading, and feedback before adding custom markup.
- For dense product pages, keep interaction surfaces restrained and table-like; avoid decorative cards, heavy borders, saturated backgrounds, and visually loud custom badges unless Delight already defines that treatment.
- If a design issue is caused by deviating from Delight spacing/color/component norms, fix the underlying token/component usage instead of layering more local CSS.
- Use colors, spacing, and component behavior that align with Delight conventions.
- When Delight guidance is needed, read [references/delight-design-spec.md](references/delight-design-spec.md).

### Code Organization

- Keep components reusable where practical.
- Avoid letting a single file exceed 500 lines, unless the file already exceeds 500 lines before the change.
- Split large additions into local subcomponents, composables, helpers, or style modules when that reduces risk and keeps ownership clear.
- Follow the existing naming, folder structure, import style, and state management pattern of the package.
- Preserve backward compatibility for existing flows.

### Change Scope

- Make the smallest change that solves the confirmed requirement.
- Do not broaden scope into unrelated cleanup.
- Avoid replacing existing frameworks, libraries, or architectural patterns unless the user explicitly asks for it.
- Search for existing components, stores, utilities, and patterns before writing new ones.

## Validation

### Validation Intensity

Pick validation by risk:
- Tiny style-only fix in one component: `git diff --check`; local dev server/visual check if already running or easy to start.
- Vue template/script change or shared style change: `git diff --check` plus package build/test when compile risk exists.
- Cross-page layout change, data flow change, API contract change, or release preparation: run the owning package build and any focused tests available.

When the user is in rapid UI review mode, optimize for fast iteration first. Do not spend more time on validation than the change itself unless release readiness is the explicit goal.

### Lint and Type Checks

Check whether touched files introduce ESLint or TSLint errors and fix them before finishing.
Also run the owning package's type or build validation when available and when the task justifies it.

Typical commands:
- Root: `pnpm test`, `pnpm build`
- Main app build gate: `pnpm -F x-ray-next run build:test`
- Main app lint gate: inspect `packages/xray-main/package.json` first; newer
  ESLint flat config rejects old flags such as `--ignore-path` and `--ext`.
  Prefer the package script or `formula lint --file <package-relative files>`
  when it is configured correctly.
- Main app warning: local paths containing spaces, such as
  `/Users/mahengyang/Documents/New project 3/xray`, can make `formula lint`
  fail because formula-linter internally runs an unquoted `cd`. Treat that as a
  local tooling/path issue unless the same error appears in CI.
- Graph app: use package-local validation or build flow if no direct lint script is available
- X-Pilot: `pnpm -F @xhs/x-pilot exec formula lint`
- Layout: `pnpm -F @xhs/xray-layout exec formula lint -p`

Pick the smallest command that gives confidence for the touched scope.

### Local Preview

For frontend changes, start or reuse the local environment when visual
verification is useful, when the change is user-facing, or when the user asks
for preview. For tiny style-only edits during rapid iteration, `git diff
--check` plus a concise manual verification URL can be enough.

Use Browser for localhost/simple local previews and Chrome when the page needs
the user's logged-in internal session. Report the exact URL and what state was
or was not verified.

Common local commands:
- Root main app: `pnpm run dev:main`
- Root graph app: `pnpm run dev:graph`
- X-Pilot: `pnpm -F @xhs/x-pilot exec formula dev`
- Click Visual UI: `pnpm -F click_visual_ui exec npm run dev`

Common local URLs:
- Main app: `http://local.xiaohongshu.com:1391`
- Other packages: derive from terminal output or package config, then report the exact URL you observed

## SIT / Production Handoff Notes

- Normal UI work should not trigger SIT/production by itself.
- When the user explicitly asks for SIT, use the `release-to-sit` skill and
  classify whether the target is a frontend Docker service, FE static package,
  backend service, or full-stack release.
- For `fexray-frontend-default`, ONES SIT requires a Docker image tag returned
  by `ones-cli meta images list --service fexray-frontend-default`; a
  `formula deploy-fe` static artifact version is not sufficient.
- If a wrong frontend image is deployed and ONES shows `ImagePullBackOff`, stop
  and release the occupied workload first; do not start another SIT deployment
  until `workloadgroups check` returns the target group under `canDeploy`.
- For production, do not trigger prod deploys from Codex. Prepare the branch,
  CR/MR, master/version evidence, and hand off the exact manual release steps.

## References

- Read [references/delight-design-spec.md](references/delight-design-spec.md) when Delight design rules, spacing, color, or component usage details are needed.
- Read [references/common-issues.md](references/common-issues.md) when the task looks blocked by environment problems or recurring repo issues.
- These reference files may start as placeholders and can be enriched later without changing the main workflow.
