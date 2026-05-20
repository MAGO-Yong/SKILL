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

- Frontend: `/Users/mahengyang/Documents/New project/xray`
- Backend: `/Users/mahengyang/Documents/New project/langfuse4j-readonly`

## Common Branch

Type: `[Case]`

- Preferred feature branch for the current AI evaluation dataset version work:
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

Publish-related scripts observed in `packages/xray-main/package.json`:

```bash
pnpm -F x-ray-next run patch
pnpm -F x-ray-next run minor
pnpm -F x-ray-next run major
```

These wrap `formula publish <level>`. Do not assume backend image release
commands apply to the frontend package. For frontend release, first inspect the
Formula output or internal pipeline page, then map the generated version/build
to SIT release.

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

- `qcsh-sit.langfuseobs-service4j-diandian`

`ones-cli project list -o json` may return an empty list for the user. Treat it
as irrelevant to direct service SIT release unless the user explicitly asks for
a personal lane/project. Continue by checking:

- service detail
- workload groups
- image list
- deployment history
- ONES web UI with Chrome login state

Current CLI shape:

- The installed `ones-cli deploy` help currently shows project-style flags such
  as `--project`, `--service`, and `--image-tag`.
- Do not ask the user for a project by default. If this CLI cannot express
  direct service SIT release, treat it as CLI capability mismatch and use the
  service SIT platform flow or authenticated web UI.

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
