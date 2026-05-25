# Case Notes: XRay AI Evaluation SIT Release

Use this reference only when releasing XRay AI 应用评估 frontend/backend changes to SIT.
This file is an incubation case for the generic `release-to-sit` skill. Do not
treat these repositories, service names, branches, or smoke checks as defaults
for other personal projects or X-RAY product modules.

Applicability:

- `[Case]`: XRay AI Evaluation dataset/version work.
- `[X-RAY]`: useful X-RAY monorepo/package conventions.
- `[XHS DevOps]`: useful ONES/SIT/service lookup examples.

## Repositories

Type: `[Case]`

- Frontend examples seen on this machine:
  `/Users/mahengyang/Documents/New project 3/xray` and older
  `/Users/mahengyang/Documents/New project/xray`. Confirm the active cwd before
  editing, building, or publishing.
- Backend examples seen on this machine:
  `/Users/mahengyang/Documents/New project 3/langfuse4j` and older
  `/Users/mahengyang/Documents/New project/langfuse4j-readonly`. Confirm the
  active cwd before editing, building, or publishing.

## Common Branch

Type: `[Case]`

- Recent AI evaluation layout/runtime branch:
  `feat-ai-eval-layout-density`
- Older dataset hierarchy branch:
  `feat-ai-eval-dataset-hierarchy`
- Build and publish from the feature branch by default.
- Do not merge into `master`, `deploy_sit`, or any shared deploy branch unless the user explicitly asks.

## Frontend

Type: `[X-RAY]`, `[Case]`

Package:

- Main app package: `x-ray-next`
- Common local URL: `http://local.xiaohongshu.com:1391`

Useful commands:

```bash
git diff --check
pnpm -F x-ray-next run build:test
pnpm -F x-ray-next run dev
```

Validation caveats:

- In a local path containing spaces such as `New project 3`, `formula lint` may
  fail because formula-linter internally shells out with an unquoted `cd`. Do
  not confuse that local path bug with GitLab CI unless the same error appears
  in CI logs.
- Current `x-ray-next` lint history includes ESLint 9 / flat-config
  compatibility debt and large repo-wide formatting debt. For release
  readiness, prefer `git diff --check`, touched-package build, and CI status.
  Only change lint config when CI is demonstrably blocked by a config
  incompatibility; do not mass-format unrelated files.

Publish-related scripts observed in `packages/xray-main/package.json`:

```bash
pnpm -F x-ray-next run patch
pnpm -F x-ray-next run minor
pnpm -F x-ray-next run major
```

These wrap `formula publish <level>`. Do not assume backend image release
commands apply to the frontend package.

For `x-ray-next`, prefer the user's normal visible path: Git push -> internal
pipeline/ONES frontend release entry -> SIT/test effect check. The user should
not need to understand FE Platform or CI metadata in normal operation.

Use `formula deploy-fe -e test` only as a fallback/diagnostic when the standard
pipeline entry is unavailable or when you must confirm whether a frontend
version has been uploaded. If running it locally, set CI metadata from git/repo
context so FE Platform records the real branch and commit:

`CI_COMMIT_SHA=$(git rev-parse HEAD) CI_COMMIT_REF_NAME=<branch>
GITLAB_USER_EMAIL=<email> CI_PROJECT_URL=<repo-url>
CI_PIPELINE_URL=<pipeline-url> pnpm -F x-ray-next exec formula deploy-fe -e test`

If this returns `debug-version-debugId`, rerun with real CI metadata before any
publish. In user-facing updates, say "前端制品已上传/测试环境已生效" only when
those states matter; otherwise report the familiar branch, commit, pipeline,
SIT URL, and smoke result.

Important guardrail for `fexray-frontend-default`: `formula deploy-fe -e test`
uploads the FE static artifact; it is not the ONES Docker image tag. Before
running `ones-cli deploy create` for this service, always verify the exact tag
with:

```bash
ones-cli meta images list --service fexray-frontend-default --query <commit-or-tag> -o json
```

Only use a tag returned by this image list. If the list is empty, do not create
an ONES deployment with a FE static version such as
`<branch>-<shortSha>`; that produces `ErrImagePull` in the frontend CloneSet.

Observed frontend Docker image pattern:

```text
feat-ai-eval-layout-density-<shortSha>
```

Example of a valid image observed after CI/image generation:

```text
feat-ai-eval-layout-density-bf02a75d
```

Example of the bad release pattern that caused `ImagePullBackOff`:

```text
Deploying feat-ai-eval-layout-density-96a9b4f8 before it existed in
ones-cli meta images list --service fexray-frontend-default
```

If this happens:

1. Diagnose the changeflow and confirm the missing image in pod status.
2. Open the ONES changeflow page if CLI has no cancel command.
3. Ask/guide the user to click `取消并暂停当前阶段` or equivalent cancel action.
4. Verify the group is free:

```bash
ones-cli deploy workloadgroups check \
  --service fexray-frontend-default \
  --workload-groups '["qcsh-sit.fexray-frontend-default"]' \
  --output-format json
```

Continue only after `qcsh-sit.fexray-frontend-default` returns under
`canDeploy`.

Known issue:

- The package lint script currently uses ESLint 9-incompatible flags:
  `--ignore-path` is invalid under the flat config flow.
- Direct eslint on touched files may also fail if shared rule config passes
  `"never"` as the severity for `@typescript-eslint/semi`.
- If this happens, record it as repo-level lint configuration debt and rely on
  `git diff --check` plus `build:test` as the minimum local frontend gate.

## Backend

Type: `[XHS DevOps]`, `[Case]`

Service repo:

- `/Users/mahengyang/Documents/New project/langfuse4j-readonly`

Expected project:

- Maven Spring Boot project
- Java target: 11 from `pom.xml`
- Prefer `./mvnw` if it exists; currently the repo may not include a wrapper, so use global `mvn`.

Useful commands:

```bash
git diff --check
mvn test
mvn package -DskipTests
```

Local Maven may need company repository settings. If Maven fails with:

```text
Could not find artifact com.xiaohongshu:infra-root-pom:pom:3.3.0-SNAPSHOT
```

then Java/Maven are installed correctly, but `~/.m2/settings.xml` is missing the
internal Xiaohongshu Maven repository or credentials. Do not treat this as a
code failure. Search for an existing company `settings.xml`, ask only if no
credential source can be found, and otherwise rely on CI/SIT Maven settings for
the backend build gate.

For this machine, the working unauthenticated repository is:

```text
https://artifactory.devops.xiaohongshu.com/artifactory/maven-public
```

`~/.m2/settings.xml` should activate this repository for both dependencies and
plugins. It is enough to resolve `com.xiaohongshu:infra-root-pom:3.3.0-SNAPSHOT`.

If Java or Maven is missing on macOS:

```bash
brew install openjdk@11 maven
```

Then expose Java 11 for the current shell. Prefer the bundled helper. On this
machine, naked `/usr/bin/java` may still be the macOS shim and report
`Unable to locate a Java Runtime`; that does not mean Java 11 is unavailable.
Always source the helper before backend Maven commands:

```bash
source /Users/mahengyang/.codex/skills/release-to-sit/scripts/java11-env.sh
```

Or set it manually:

```bash
export JAVA_HOME="$(/usr/libexec/java_home -v 11)"
export PATH="$JAVA_HOME/bin:$PATH"
```

If `/usr/libexec/java_home` does not discover Homebrew Java, use:

```bash
export JAVA_HOME="/opt/homebrew/opt/openjdk@11"
export PATH="$JAVA_HOME/bin:$PATH"
```

## Docker

Type: `[Local Project]`, `[XHS DevOps]`

Docker CLI may point at OrbStack:

```text
unix:///Users/mahengyang/.orbstack/run/docker.sock
```

If `docker info` cannot connect, start OrbStack and retry:

```bash
open -a OrbStack
docker info --format '{{.ServerVersion}}'
```

## ONES / SIT

Type: `[XHS DevOps]`, `[Case]`

Known backend service from the AI evaluation dataset version work:

- `langfuseobs-service4j-diandian`

Known frontend service from the AI evaluation layout work:

- `fexray-frontend-default`

ONES commands to inspect:

```bash
ones-cli version
ones-cli auth status
ones-cli meta services detail --service langfuseobs-service4j-diandian -o json
ones-cli meta images list --service langfuseobs-service4j-diandian -o json
ones-cli deploy detail --changeflow <changeflow-name> -o json
```

When choosing the backend image, show the latest publishable candidates before
deploying. Example shape:

| Rank | Image | Created At | Status | Recommendation |
|---|---|---|---|---|
| 1 | `feat-ai-eval-dataset-hierarchy-e736153d-202605200122-jdk11` | `2026-05-20 01:22:42` | publishable | latest, recommended |
| 2 | `feat-ai-eval-dataset-hierarchy-a6531db8-202605200004-jdk11` | `2026-05-20 00:04:51` | publishable | fallback |

Prefer the newest publishable image matching the intended branch/commit. If a
new commit was just pushed, wait for and select the image containing that
commit hash instead of blindly selecting an older latest image.

The user's normal SIT flow is direct service SIT release, not personal test
project/lane release. For this case, target the service's SIT deploy group:

- backend: `qcsh-sit.langfuseobs-service4j-diandian`
- frontend: `qcsh-sit.fexray-frontend-default`

`ones-cli project list -o json` may return an empty list for the user. Treat it
as irrelevant to direct service SIT release unless the user explicitly asks for
a personal lane/project. Continue by checking:

- service detail
- workload groups
- image list
- deployment history
- ONES web UI with Chrome login state

Current CLI shape:

- Direct service SIT release for the XRay frontend service uses the top-level
  service release commands, not project/lane deploy:

```bash
ones-cli meta services detail --service fexray-frontend-default -o json
ones-cli meta images list --service fexray-frontend-default -o json
ones-cli deploy changeflow-infos list --service fexray-frontend-default --output-format json
ones-cli deploy workloadgroups check --service fexray-frontend-default --workload-groups '["qcsh-sit.fexray-frontend-default"]' --output-format json
ones-cli deploy create --service fexray-frontend-default --changeflow-info sit --workload-groups '["qcsh-sit.fexray-frontend-default"]' --image-tag <tag> -y --output-format json
ones-cli deploy detail --changeflow <changeflowName> --output-format json
```

- `ones-cli schema deploy.create --format json` maps this path to backend tool
  `create_deploy_with_watch`. The request payload fields are
  `applicationChildName`, `changeflowInfoName`, `repoTag`, and
  `workloadGroups`; there is no client-side `owner` field to repair.
- On 2026-05-21, the correct CLI command for
  `fexray-frontend-default` / `qcsh-sit.fexray-frontend-default` /
  `feat-ai-eval-layout-density-1ae6d4e6` returned:

```text
permission denied: application 'fexray' access denied: 无权限！如需要，您可到服务树申请当前应用「研发owner」角色
```

- Treat that error as an ONES backend authorization/precheck inconsistency when
  these read-only checks pass at the same time:
  `meta applications permissions list` shows `fexray` role `rd`,
  `workloadgroups check` returns `canDeploy`, and the image candidate has
  `properties.canPublish=true`.
- Also check the change-freeze window. On 2026-05-21, `ones-cli create` returned
  the misleading `研发owner` block at 21:33 after the 618 freeze window started
  at 20:00, even though the same service had successful SIT releases before the
  freeze. Treat this as a likely freeze-policy/CLI-tool permission escalation,
  not as proof that the user lost normal deploy permission.
- The ONES web release page for the same service uses a different API layer:
  `/api/v1/x/application/changeflow/info/...`, `/api/v1/x/deploy/check`,
  `/api/v1/x/tag/list`, and the modal submit path calls frontend request key
  `DEPLOY_CREATE`, which maps to `/api/v1/x/deploy/create`. The CLI create path
  posts to dynamic tool `/api/v1/a/tools/create_deploy_with_watch`. If CLI
  returns the `研发owner` block while the web precheck succeeds, treat it as a
  CLI/dynamic-tool backend permission mismatch, not as proof that the user lacks
  service deploy rights.
- Do not "fix" this by asking for a project/lane. If a real publish is required
  and CLI create is blocked this way, capture the failed command plus the
  permission evidence, then either use the authenticated ONES service release
  page with the same service/tag or escalate to ONES backend owners for
  `create_deploy_with_watch` permission logs.

- The installed `ones-cli deploy` help currently shows project-style flags such
  as `--project`, `--service`, and `--image-tag`.
- Do not ask the user for a project by default. If this CLI cannot express
  direct service SIT release, treat it as CLI capability mismatch and use the
  service SIT platform flow or authenticated web UI.
- CLI shape note: recent successful releases used the nested `deploy` command
  group (`ones-cli deploy create/detail/...`). If older notes mention
  top-level `ones-cli create`, verify the installed CLI schema first with
  `ones-cli schema deploy --format json` and use the command group that exists.

Observed credential state on this machine:

- Git remote read and dry-run push work for both the XRay frontend repo and
  langfuse4j backend repo.
- `ones-cli auth status` reports logged in.
- ONES can read service details and image lists for
  `langfuseobs-service4j-diandian`.
- `ones-cli project list -o json` can return `data: []`; this is not relevant
  for the direct service SIT flow and is not a login failure.
- Do not check or report `npm whoami` for this flow unless dependency install
  fails with authentication errors or the task is explicitly npm package
  publishing. The frontend build gate does not depend on npm account login.
- The controlled Chrome session may still be redirected to
  `login2.sit.xiaohongshu.com` for SIT pages. Prefer CLI for release actions
  and ask for browser login only if UI-only publishing or authenticated smoke
  testing is required.

## SIT Smoke Checklist

Type: `[Case]`

For AI 应用评估 dataset/version work, smoke at least:

- Dataset list renders parent datasets.
- Legacy no-version datasets expose a fallback version only when needed.
- Creating a dataset with no data does not create a meaningless V1 item state.
- Clicking Add Data on a no-version dataset first creates/reuses V1, then writes item to V1.
- Upload Data creates or reuses the intended version name and imports rows as dataset items.
- Version dropdown, edit version, delete version, and create version actions work.
- Dataset schema fields and item table columns match.
- Dataset item detail drawer displays empty fields as `-`, and update/create time in one row.
- Evaluation experiment detail dropdown keeps the current experiment selected.
- Analysis charts and experiment detail table still load without 4xx/5xx.
