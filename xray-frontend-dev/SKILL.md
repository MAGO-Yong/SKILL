---
name: xray-frontend-dev
description: Frontend delivery skill for the xray monorepo. Use when Codex needs to handle frontend feature development, UI adjustment, page refactor, bug fixing, requirement clarification, technical方案产出, environment setup, lint/type cleanup, or local verification in this repository, especially for packages/xray-main, packages/xraygraph, packages/x-pilot, packages/xray-layout, packages/shared, and packages/click_visual_ui.
---

# Xray Frontend Dev

## Overview

Use this skill to deliver frontend work in the xray monorepo with a fixed collaboration flow that works for any user role.
Always check the local environment first, always write and confirm requirements and the technical plan before coding, then implement with the smallest safe change and finish with lint/type cleanup plus a local preview link.

## Workflow

1. Check the local environment.
2. Analyze the request and write a requirement document.
3. Wait for explicit user confirmation.
4. Write the technical plan with a minimum-change approach.
5. Wait for explicit user confirmation.
6. Implement the code.
7. Run lint and type checks for touched files or the owning package.
8. Start the local environment and give the user a manual verification URL.
9. Verify in SIT or BETA test environments when the task requires deployment validation.
10. Verify in the NJ environment when the task requires NJ validation.
11. When the user says things like `提交 MR`, `提 MR`, or other equivalent release-preparation requests, automatically run the production release preparation flow.

Do not skip the confirmation gates in steps 3 and 5.
Do not continue to the next gated step until the user gives a clear affirmative response.

## Environment Delivery Workflow

Use this section when the task needs environment-level verification or production preparation after local development.

### Test Environment Verification

Support both SIT and BETA validation.

#### SIT Test Environment Verification

- Option 1: push the current personal branch directly and publish a personal test environment in Ones.
- Option 2: merge the current personal branch into `deploy_sit`, push it to remote, then perform a non-production release in [fexray frontend default](https://ones.devops.xiaohongshu.com/app-next/fexray/fexray-frontend-default).

#### BETA Test Environment Verification

- Option 1: push the current personal branch directly and publish a personal test environment in Ones.
- Option 2: merge the current personal branch into `deploy_beta`, push it to remote, then perform a non-production release in [fexray frontend default](https://ones.devops.xiaohongshu.com/app-next/fexray/fexray-frontend-default).

### NJ Environment Verification

- Merge the personal branch into `deploy_nj` and push it to remote.
- Perform a production release in [fexray frontend default](https://ones.devops.xiaohongshu.com/app-next/fexray/fexray-frontend-default).
- In the release flow, choose `南京 2`.

Treat this path as mandatory when the task explicitly requires NJ validation.

### Production Release

- When the user says things like `提交 MR`, `提 MR`, or other equivalent release-preparation requests, automatically do the following:
1. Check whether the current branch is a personal branch and whether the working tree is clean.
2. Run `pnpm run version` in the root of the personal branch.
3. Select the appropriate application and semantic version number.
4. Commit the generated changes again and push to remote.

Do not skip the versioning step for real production release work.

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

### Lint and Type Checks

Check whether touched files introduce ESLint or TSLint errors and fix them before finishing.
Also run the owning package's type or build validation when available and when the task justifies it.

Typical commands:
- Root: `pnpm test`, `pnpm build`
- Main app: `pnpm -F x-ray-next exec eslint --ignore-path .gitignore . --ext .js,.ts,.tsx,.vue`
- Main app autofix: `pnpm -F x-ray-next exec eslint --fix --ignore-path .gitignore . --ext .js,.ts,.tsx,.vue`
- Graph app: use package-local validation or build flow if no direct lint script is available
- X-Pilot: `pnpm -F @xhs/x-pilot exec formula lint`
- Layout: `pnpm -F @xhs/xray-layout exec formula lint -p`

Pick the smallest command that gives confidence for the touched scope.

### Local Preview

Always help the user start the local environment after implementation when the task is a frontend change.
Show the user the URL and let them verify manually.
Do not use Playwright or similar tools to open the browser automatically.

Common local commands:
- Root main app: `pnpm run dev:main`
- Root graph app: `pnpm run dev:graph`
- X-Pilot: `pnpm -F @xhs/x-pilot exec formula dev`
- Click Visual UI: `pnpm -F click_visual_ui exec npm run dev`

Common local URLs:
- Main app: `http://local.xiaohongshu.com:1391`
- Other packages: derive from terminal output or package config, then report the exact URL you observed

## References

- Read [references/delight-design-spec.md](references/delight-design-spec.md) when Delight design rules, spacing, color, or component usage details are needed.
- Read [references/common-issues.md](references/common-issues.md) when the task looks blocked by environment problems or recurring repo issues.
- These reference files may start as placeholders and can be enriched later without changing the main workflow.
