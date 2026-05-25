---
name: dev-cicd
description: 通用项目开发到发布的完整 CICD 流程。当用户要求构建、发布、部署、推镜像、新建服务、创建项目、上线，或涉及 Dockerfile、Makefile、CICD、ONES、RedCloud、HCMP 改动时使用。
metadata:
  short-description: 开发、构建、推镜像、ONES 发布全流程
---

# Dev CICD

负责从代码检查到镜像构建、制品推送、ONES 发布的完整开发发布流程。用户偏好是少问确认、直接执行；确定的事情直接做，不确定且会影响发布结果的事情再问。

## 触发判断

| 用户说 | 应做事项 |
|--------|----------|
| “改完了”、“好了”、“你看看” | 先按当前上下文做轻量检查；只有用户明确要验证/构建/提交/发布时才跑完整 `make check` 或交付流程 |
| “验证发布到 sit”、“发 SIT”、“发布 SIT” | 执行标准 SIT 流程：preflight -> dependency repair -> validation -> commit -> push -> image/build discovery -> deploy -> smoke check |
| “发一下”、“部署”、“上线”、“发布” | 先判断目标环境；测试环境直接走标准流程；生产环境只做准入检查、版本确认和手动发布交接，不自动触发生产发布 |
| 开始写代码/修改文件/实现功能/修 bug | 只做轻量开发前置预检：确认仓库、分支、remote、重复分支、diff 范围、后续最小验证路径；不构建、不推送、不部署 |
| “新建项目/服务” | 引导 RedCloud 创建应用 -> `ones-cli` 创建服务 -> 提醒 HCMP 资源审批 |
| 改了 `Dockerfile` / `Makefile` / CICD 文件 | 自动执行 Dockerfile 和构建预检 |
| `docker push` 报 unauthorized | 检查 registry 和登录态，指导用户通过安全方式登录，不在 skill 中保存或打印密码 |
| 发布后报“部署组为空” | 告知需要去 HCMP 审批资源，并给出入口 |
| 需要 RedCloud/HCMP 网页操作 | 给链接并说明用户需要在页面做什么 |

报错时先定位和修复，不要只把日志原样丢给用户。

## 专项 Skill 路由

通用 CICD 只负责总入口。遇到明确项目或平台时，先调用对应专项
skill 的门禁，避免把不同发布路径混在一起。

| 场景 | 必须先用的专项规则 |
|------|--------------------|
| XRay 前端开发、构建、CR、SIT、生产准备 | `xray-frontend-dev`：检查业务 diff 白名单、Delight/前端标准、Changesets 版本和构建证据 |
| 任意 SIT 发布或 ONES 部署 | `release-to-sit`：分类服务类型、镜像/制品、workload group、changeflow 和 smoke |
| 生产发布 | `release-to-sit` 的生产 handoff 规则；Codex 不自动触发生产 changeflow |

如果专项 skill 和通用流程冲突，以更具体的专项 skill 为准。例如
XRay 前端发布时，不能因为通用 Node 项目习惯而修改平台级契约、升级
无关 workspace 依赖、用 FE static artifact 冒充 ONES Docker image，或用
feature/SIT-only 版本做生产发布。

平台级契约包括但不限于 lint/format/TS/build/CI 配置、依赖和 lockfile、
workspace 拓扑、全局 request/auth/router/layout/store/telemetry/error
handling、全局样式和主题 token、共享组件基础设施、部署配置和发布脚本。
功能迭代如果必须改这些内容，应拆成单独平台任务、说明影响面、单独提交，
并做更大范围验证；不能为了单个功能快速过 lint/build/release 顺手带入。

## 状态化输出

执行验证或发布时必须维护一个简短状态表，并在关键节点更新，不要只输出流水账。状态可用：

- `pending`: 未开始
- `running`: 执行中
- `passed`: 通过
- `blocked`: 被外部条件阻塞，例如权限、登录态、依赖安装需要授权
- `failed`: 失败，需要修复后重试
- `skipped`: 有明确理由跳过

状态表至少包含：

| 节点 | 状态 | 证据/下一步 |
|------|------|-------------|
| 分支与工作区复核 | pending | 当前分支、是否落后远端、是否有无关改动 |
| 依赖与工具链 | pending | Node/pnpm/Java/Maven/ones-cli/docker 等是否可用 |
| 本地静态检查 | pending | `git diff --check`、lint/typecheck/test 的结果 |
| 本地构建 | pending | package build、Maven/Gradle/package 构建结果 |
| 提交与推送 | pending | commit、remote branch、MR/CR 链接 |
| 镜像/制品 | pending | image tag 或平台构建记录 |
| SIT 发布 | pending | project/service/workload/image/changeflow |
| 发布后验证 | pending | SIT 页面/API/smoke check 结果 |

生产发布时不要把 `SIT 发布` 当成可直接复用节点。改用：

| 节点 | 状态 | 证据/下一步 |
|------|------|-------------|
| 生产准入 | pending | CR/MR 是否已通过、是否合并 master、是否关联需求/工作项、是否过封网/发布窗口 |
| 生产版本 | pending | 最新可发布的 master 镜像/版本，不使用 feature/SIT-only 镜像 |
| 生产发布交接 | pending | 用户手动发布步骤、推荐版本、平台入口、剩余阻塞项 |

生产前必须先做分支收敛，避免多天开发留下多个 feature 分支、多个 CR、多个镜像：

| 节点 | 状态 | 证据/下一步 |
|------|------|-------------|
| 生产分支收敛 | pending | 唯一 canonical 分支、唯一 CR/MR、重复分支处理建议、是否已合 master |

每次遇到阻塞，先尝试修复；修不了再把阻塞条件写进状态表，不要直接用“交给 CI”替代本地可补齐的验证。

## 用户引导模式

默认假设用户不需要记住 CICD 和发布细节。普通开发只做简短状态说明；进入验证/发布流程时，再用轻量引导卡带用户走完整链路。

开工时展示：

| 项 | 内容 |
|----|------|
| 当前目标 | `<实现功能 / 修 bug / 验证 / SIT / 生产准备>` |
| 当前仓库/分支 | `<repo> / <branch>` |
| 当前阶段 | `<开发前置预检 / 编码 / 本地验证 / SIT / 生产准入>` |
| 我会自动做 | `<检查分支、改代码、跑验证、推分支等>` |
| 需要你做 | `<暂无 / 关联 PingCode / 找 reviewer / 手动发布>` |

执行中只提示当前节点和下一步，不要一次性给用户 10 多个步骤。用户需要动作时，必须给可执行指引：

- 链接：打开哪个 CR/MR、ONES、PingCode、发布页面。
- 对象：找哪个 reviewer 或负责人。
- 内容：可复制的标题、描述、评论、reviewer handoff。
- 完成信号：用户完成后应该告诉 Codex 什么，例如“已 review 通过”“已合 master”“已手动发布”。

对生产流程，Codex 的职责是引导和交接，不替用户完成人工准入或生产发布。

## 操作流程

根据用户请求选择 `init`、`check`、`build`、`push`、`deploy`、`new-service`、`full`。如果用户没有指定操作，根据当前上下文自动判断。

### 开发前置预检

只要 Codex 准备在本地仓库写代码，就先做这个轻量预检。它不是发布，也不是构建；目的是从第一处代码改动开始，就避免分支、CR、镜像和发布路径混乱。

1. 确认当前仓库、当前分支、remote、是否落后远端。
2. 检测同一需求是否存在多个相似 feature 分支或旧 CR/MR。
3. 选定或提示 canonical 分支策略；不在多个分支上分散同一批改动。
4. 检查当前未提交 diff，识别用户已有改动和无关改动。
5. 对 monorepo 先判定 owning package/module，并记录不应触碰的
   out-of-scope 文件或 workspace。
6. 扫描 diff 文件名和内容里是否有 mock/debug/demo/sample/fixture/test-data
   等临时数据或开关；默认不能带入发布分支。
7. 记录后续最小验证路径：本地静态检查、测试、构建、SIT 或生产准入。
8. 不执行 build/push/deploy，不创建 CR/MR，不触发生产动作。

如果后续进入发布，必须再次复核 diff。开发期间为了绕过 lint、install、
build 而临时改过的平台级契约、依赖、lockfile、公共工具文件，不能默认带入
CR/SIT/生产分支。

### 依赖与工具链修复

如果发布验证需要的工具缺失，默认尝试补齐，而不是直接跳过：

- Node/pnpm：优先使用项目 `packageManager` 和 `engines`；缺依赖时运行项目建议的 install 命令。
- Java：读取 `pom.xml`、`build.gradle` 或 README 判断 Java 版本；缺 Java Runtime 时优先安装/切换匹配版本。
- Maven：若有 `mvnw` 优先用 wrapper；没有 wrapper 且缺 `mvn` 时安装 Maven 或使用本机包管理器补齐。
- Gradle：若有 `gradlew` 优先用 wrapper。
- ONES：先跑 `ones-cli --help` 和必要的 `auth`/`meta` 命令确认登录态；不要在登录态不明时猜项目名。
- Docker：需要本地构建镜像时确认 Docker daemon、登录态和架构。

安装或修改系统级依赖需要授权时，直接请求授权并说明用途；用户已要求“补齐依赖让流程丝滑”时，不要反复询问是否要装。

### 标准 SIT 发布流程

1. Preflight：确认 cwd、仓库、分支、remote、是否落后远端、是否有无关改动；同时检查是否存在同一需求的相似/旧 feature 分支（例如 `feat/foo` 与 `feat-foo`），先确定唯一 canonical 分支，避免 CR、镜像和发布入口选错。
2. Dependency repair：补齐 Node/pnpm/Java/Maven/ones-cli/docker 等发布必要依赖。
3. Validation：按项目类型跑最小可靠检查，再跑构建。失败先修复；确认是仓库既有配置问题时记录证据。
4. Commit：只 add 本次相关文件；提交信息使用清晰 conventional commit。
5. Push：推当前 feature 分支，默认不合 master，不污染 master/deploy 分支，除非用户明确要求。
6. Image/build discovery：通过 ONES/平台 CLI 查当前服务可用镜像或触发构建；优先使用刚推送分支对应镜像。
7. Deploy：发布到目标 SIT project/service/workload group。`ones-cli project list` 为空不等于不能发布，要继续查服务详情、发布历史、部署组和平台入口。
8. Monitor：轮询 changeflow/detail 到 success/failed；失败时拉诊断日志并修复可修问题。
9. Smoke check：用 SIT 页面或 API 验证核心路径可访问，最后给状态表和链接。

发布前必须先按服务类型分流：

| 类型 | 发布凭证 | 关键检查 |
|------|----------|----------|
| 前端 Docker 服务 | ONES 服务镜像 tag | `ones-cli meta images list --service <service> --query <sha/tag>` 必须能查到 |
| FE 静态制品 | FE Platform/formula app version | 上传成功不等于 ONES Docker 镜像，也不等于 SIT 生效 |
| 后端服务 | ONES 服务镜像 tag | 镜像应匹配 branch/commit，并且服务部署组可发布 |
| 生产发布 | master 镜像/版本 | Codex 只做准入和交接，不自动点生产发布 |

不要把一种类型的产物当成另一种类型发布。尤其是前端：
`formula deploy-fe -e test` 的静态制品版本不能直接作为
`fexray-frontend-default` 这类 ONES Docker 服务的镜像 tag。

进入 deploy 之前必须完成发布前预防门禁：lockfile/specifier 一致、分支/tag
Docker-safe、目标服务镜像真实存在且匹配 commit、FE static 与 ONES service
类型不混用、workload group 可发布、CLI 权限与 UI/服务读权限不矛盾、没有
误带 mock/debug/test data。任一门禁失败都先修输入，不创建 changeflow。

如果 ONES changeflow 卡在 `Running` 且 Pod 是 `ErrImagePull` /
`ImagePullBackOff`：

1. 用 `ones-cli deploy diagnose --changeflow <name> -o json` 确认缺失镜像。
2. 用 `ones-cli deploy workloadgroups check ...` 确认部署组是否被占用。
3. 不要继续创建第二个发布。
4. CLI 没有 cancel 命令时，打开 ONES 页面让用户点
   `取消并暂停当前阶段` 或同等取消动作。
5. 只有部署组回到 `canDeploy` 后，才用真实存在的新镜像重发。

当 CLI 不能完成发布但页面可以完成时，用 Chrome 登录态继续操作 ONES 页面；只有需要用户二次认证、审批或权限缺失时才停下来。

### 标准生产发布准备流程

生产发布不是 SIT 自动流的延伸。默认只做到“可发布交接”，生产发布动作由用户手动完成，Codex 不自动创建或触发 prod changeflow。

1. Preflight：确认目标是生产，确认仓库、服务、生产环境和发布影响面。
2. Branch consolidation：把多天开发收束到一个 canonical feature 分支；确认没有第二个分支/第二个 CR 承载同一批改动。
3. Release diff：确认本次生产包含哪些提交，重点核对用户关心的修复是否已经进入 canonical 分支。
4. CR/MR gate：打开或更新唯一 CR/MR 到 `master`；确认 CodeWiz/人工阻塞评论已处理或明确接受。
5. Work item gate：确认平台要求的 PingCode/需求/提测/变更单已关联。Codex 可以给标题、描述和链接清单；如果平台权限不足，由用户创建或关联。
6. Review gate：找评审人 review 并 approve。Codex 可以整理 reviewer handoff，但不能替代人工通过。
7. Merge gate：确认 canonical 分支已合并到 `master` 或项目约定的生产分支；没有合并时标记 blocked，让用户找评审人/负责人完成。
8. Freeze gate：查询封网/发布窗口；如被封网阻塞，标记 blocked。
9. Build/image discovery：查找最新可发布的 `master` 镜像或版本，并展示候选表；不要默认使用 feature 分支或 SIT-only 镜像。
10. Handoff：给出服务、环境、推荐版本、CR/MR、SIT 验证证据、发布平台入口和剩余手动动作。
11. Manual publish：用户在平台手动发布。Codex 不点击生产发布、不创建 prod changeflow。
12. Post-check：用户发布完成后，Codex 可以协助查看发布结果、生产 smoke、回滚入口和风险提示。

### 生产分支收敛规则

多天开发后，生产只认一个候选分支。执行生产准备时必须：

1. `git fetch --all --prune`，查找相关分支和 CR/MR。
2. 按分支名、提交历史、diff、CR/MR 链接判断是否存在重复分支。
3. 选择一个 canonical 分支承载全部改动；不要让前端/后端各自之外的同仓库改动散落在多个分支。
4. 把需要发布的提交合入 canonical 分支；把无关依赖、mock、调试、临时文件排除。
5. 对 canonical 分支创建或更新唯一 CR/MR 到 `master`。
6. 重复/废弃分支只在用户确认后删除；删除前报告本地和远端分支名。
7. 合并后用 `git merge-base --is-ancestor <canonical-tip> origin/master` 验证 master 是否包含全部改动。

推荐展示：

| 分支 | 角色 | 最新提交 | CR/MR | 与 master 差异 | 动作 |
|------|------|----------|-------|----------------|------|
| `<branch>` | canonical | `<sha>` | `<link>` | `<summary>` | 保留并评审 |
| `<branch>` | stale | `<sha>` | `<link/无>` | 与 canonical 重叠 | 用户确认后删除 |

不可自动化或不应绕过的动作：

- 找评审人通过 CR/MR；
- 关联或审批需求/工作项/变更单；
- 合并受保护分支；
- 选择或确认生产发布窗口；
- 对未通过准入的生产发布做风险接受。
- 点击生产发布或创建 prod changeflow。

这些不是工具缺失，而是组织控制。遇到时要给用户明确 handoff，不要伪装成“我已经发布”。

### 新建服务

1. RedCloud 创建应用：`https://redcloud.devops.xiaohongshu.com/GetStart/Create`
2. 使用 CLI 创建服务：

```bash
ones-cli meta services create \
  --application <应用名> \
  --service <服务名-service-default> \
  --deploy-type k8s \
  --language <Java/Go/Node\ js/Python/C++/其他> \
  --level 3 \
  --scene-path "<业务线/产品/场景>" \
  --git-addr <git仓库地址> -y
```

首次发布通常会触发 HCMP 资源申请，CPU/内存审批通过后才能发布成功。

### 项目初始化

通用文件：

| 文件 | 作用 |
|------|------|
| `.gitignore` | 排除构建产物、IDE 文件、`.env`、数据文件 |
| `.dockerignore` | 排除构建产物、`.git/`、依赖目录 |
| `.editorconfig` | 统一编辑器设置 |
| `Makefile` | 包含 `check`、`build`、`push` target，`build` 必须依赖 `check` |

语言特定约定：

- Rust：`rustfmt.toml`、`.githooks/pre-commit`；`make check` = fmt + clippy + test
- Node.js：`eslint.config.*`；`make check` = lint + test
- Go：`make check` = go vet + golangci-lint + go test
- Java：`make check` = checkstyle + test

### 代码检查

Use `make check` only when the repo defines it as the accepted project check.
For XRay/frontend packages or repos without a Makefile, use the owning package's
documented validation command instead.

```bash
make check
```

所有代码必须通过适合当前仓库的检查后才构建或发布。若失败，优先修复再继续。

### 构建镜像

构建前必须完成 Dockerfile 预检：

1. Docker Hub 不可达时，用 `ARG REGISTRY=docker.m.daocloud.io/` 参数化镜像源。
2. 公司 git hook 不允许硬编码外网镜像地址时，用 ARG 参数化。
3. Node 镜像优先用 `artifactory.devops.xiaohongshu.com/library/`；Rust 镜像可用 DaoCloud 代理。
4. 确认运行需要的所有文件、数据、配置、证书都 COPY 或挂载到位。
5. COPY 目标目录不存在时先 `mkdir -p`。
6. 基础镜像版本满足所有依赖。
7. 目标架构使用 `--platform linux/amd64`。
8. `EXPOSE` 端口与代码默认端口一致。

```bash
make build
```

### 推送镜像

```bash
make push
```

约定：

- 镜像仓库：`artifactory.devops.xiaohongshu.com/devops/<项目名>`
- 镜像 tag：个人/自管镜像可用 `<git-short-hash>-<YYYYMMDD>`；公司平台或 ONES
  服务以平台真实生成并可查询到的 tag 为准，不手工编造。
- unauthorized 时不要在 skill 中保存或打印密码。先确认 registry，再引导用户使用公司推荐的 SSO/token/credential helper 登录：

```bash
docker login artifactory.devops.xiaohongshu.com
```

### 发布服务

ONES 发布命令会随服务类型和 CLI 版本变化。进入 ONES/SIT 发布时，使用
`release-to-sit` 的服务类型分流、预防门禁和当前 CLI 命令说明作为准则；
不要直接照抄旧的 `deploy create` 示例。

只读发现可以从这些命令开始：

```bash
ones-cli changeflow-infos list --service <服务名> --output-format json
```

```bash
ones-cli workloadgroups check --service <服务名> --workload-groups '<json>' --output-format json
```

```bash
ones-cli meta images list --service <服务名> --output-format json
```

真实创建 changeflow 前，必须确认服务、环境、workload group、image tag、
权限和预防门禁都通过；否则停在 handoff/blocked，不创建发布。

### 完整流程

下面只是自管项目的示例流程。XRay、ONES 或内部平台发布时，以专项 skill
和平台实际 gates 为准。

```bash
make check
git status
git add <相关文件>
git commit -m "<message>"
git push
make push
release-to-sit: discover service/image/workload -> prevention gates -> deploy or handoff
```

## 公司基础设施

- 镜像仓库：`artifactory.devops.xiaohongshu.com`
- Docker Hub 代理：`docker.m.daocloud.io/`
- Node 内部源示例：`artifactory.devops.xiaohongshu.com/library/node:<version>`；
  具体版本必须以项目 `engines`、README、CI 镜像或 package manager 配置为准。
- GitLab：`code.devops.xiaohongshu.com`
- 部署平台：ONES，命令为 `ones-cli`
- 应用创建：RedCloud，`redcloud.devops.xiaohongshu.com`
- 资源申请：HCMP，`hcmp.devops.xiaohongshu.com`
- 目标架构：`linux/amd64`

## 注意事项

- 发布前确认 `git status`，不要提交无关改动。
- 不要回滚用户已有改动。
- 写操作、发版、回滚等高影响动作如果用户意图不明确，需要先简短确认。
- 需要网页操作时，说明具体入口和用户应点击/填写的内容。
- 不要在 skill、命令或回复中保存、打印或复述密码/token；需要登录时使用公司推荐的 SSO、token 或 credential helper。
