---
name: codex-operator
description: Operate and repair this user's local Codex workbench. Use when Codex needs to inspect or fix Codex Desktop, Chrome/AppleScript/CDP/browser access, plugin or connector state, local service URLs and ports, workspace AGENTS.md setup, or recurring failures such as unable to read WeChat articles, browser automation not connected, or local API ConnectionRefused.
---

# Codex Operator

## Mission

Make the local Codex workbench more capable before doing the higher-level task. Prefer a small direct fix, then verify the capability actually works.

## Quick Triage

Start with the failing layer the user is touching:

| Symptom | First checks |
| --- | --- |
| WeChat or anti-bot page cannot be read | Open in the user's Chrome, then try AppleScript JS or CDP. See `references/web-article-access.md`. |
| Chrome tool cannot see or control tabs | Check whether Chrome is running, profile selected, Codex Chrome Extension installed, and CDP/AppleScript access available. |
| `API Error: Unable to connect to API (ConnectionRefused)` | Check local proxy ports before continuing upper-layer work. Inspect `8089`, `8090`, `ANTHROPIC_BASE_URL`, launchd, and stale processes. |
| User asks "where is the page/site/dashboard" | Find project directory, default port, route path, current listener state, and exact start command. |
| User asks to "arm", "upgrade", or "teach" Codex | Prefer creating/updating `AGENTS.md`, a focused skill, or a site-pattern note. |

## Browser Recovery

Use the least intrusive path that can retrieve the target content:

1. Static fetch or Jina for normal articles and docs.
2. User Chrome for sites that need login, cookies, or normal browser rendering.
3. AppleScript JS when Chrome has `View > Developer > Allow JavaScript from Apple Events` enabled.
4. CDP/web-access when remote debugging is enabled and the target needs DOM extraction or repeated browser actions.
5. Computer Use only when visual/manual UI state is the source of truth.

When a browser setting blocks extraction, fix the setting when the user asks for it, then immediately run a tiny verification such as reading `document.title` or `document.body.innerText.slice(0, 200)`.

## Local Codex Hardening

When improving the user's setup:

- Add or update a local `AGENTS.md` when the current workspace has repeatable behavior rules.
- Add a skill only when the workflow is reusable across future turns.
- Keep skill bodies short and actionable; put platform quirks in `references/`.
- Validate new skills with `quick_validate.py`.
- Avoid copying unstable product claims, prices, or model names into durable rules unless verified from official docs.

## Useful Local Anchors

- Global preferences: `/Users/mahengyang/.codex/AGENTS.md`
- Main config: `/Users/mahengyang/.codex/config.toml`
- User skills: `/Users/mahengyang/.codex/skills/`
- Web access skill: `/Users/mahengyang/.codex/skills/web-access/`
- XRay frontend skill: `/Users/mahengyang/.codex/skills/xray-frontend-dev/`
- Dev/CICD skill: `/Users/mahengyang/.codex/skills/dev-cicd/`

## Verification

Before reporting success, verify the exact capability the user wanted:

- Article reading: return title and a short extracted snippet.
- Browser setup: show which path works, such as AppleScript JS, CDP, Chrome extension, or Computer Use.
- Local service: report URL, port listener status, and start command.
- Skill/AGENTS update: run the skill validator or show the changed file paths.
