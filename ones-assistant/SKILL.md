---
name: ones-assistant
description: "ones 发布平台操作助手。当用户需要进行以下操作时触发：查询有权限的应用/服务、查看服务部署组信息、查询可用镜像版本、查询或浏览发布流程模板、触发 SIT 或 staging 环境发布、查询发布进度或发布详情、查询发布历史、查询 Pod 状态、诊断发布卡住或异常、查询我的发布列表、查询我的测试项目、创建测试项目（创建测试泳道/创建泳道环境）、下线测试项目、对测试项目泳道发起发布（泳道发布）、查询预算子账号信息（budget-sub-account-id）、对指定部署组发起扩缩容（修改副本数）、查询扩缩容状态与进度、在服务树中创建新服务（含查询 scene_path、引导 Git 仓库创建、可选绑定域名）、重启服务工作负载、重建 Pod。Use when: deploying services to ones platform, checking deploy status, querying workload groups, browsing image tags, diagnosing deploy failures, scaling workload replicas, querying budget accounts, creating new services in the service tree, restarting workloads, rebuilding pods, or managing person projects (create/delete/deploy)."
---

# ones 发布平台操作助手

帮助用户通过 `ones-cli` 完成 ONES 发布平台的日常操作。Agent 根据用户意图构造并执行对应的 `ones-cli` 命令。

---

## Agent 行为指南

### 前置检查（仅会话首次）

1. 运行 `which ones-cli`，未找到则执行安装：
   ```bash
   npm install -g @xhs/ones-cli --registry http://npm.devops.xiaohongshu.com:7001/
   ```
   如权限不足，改用用户目录安装：
   ```bash
   mkdir -p ~/.npm-global && \
   npm install -g @xhs/ones-cli --prefix ~/.npm-global --registry http://npm.devops.xiaohongshu.com:7001/ && \
   export PATH="$HOME/.npm-global/bin:$PATH"
   ```
2. 安装后运行 `ones-cli auth status` 检查登录态，未登录则运行 `ones-cli auth login`。**`ones-cli auth login` 会返回一个鉴权链接，必须将该链接原样返回给用户，让用户点击链接完成认证**。

### 核心原则

1. **直接执行**：用户描述意图时，直接构造并运行 `ones-cli` 命令，不要只给命令让用户自己跑
2. **解析输出**：运行命令后解读结果，用简洁中文总结关键信息，不要原样转发大段输出
3. **链式操作**：多步操作自动串联（如：查模板 → 查镜像 → 校验部署组 → 创建发布）
4. **结构化优先**：所有查询命令加 `--output-format json` 获取结构化数据便于解析

### 命令探索

ones-cli 的命令由后端 tool 动态生成，**优先参考本文档**；如果返回不符合预期，尝试以 `--help` 实际输出为准，不要依赖本文档索引。

```bash
ones-cli --help                          # 列出所有顶层命令（noun）
ones-cli <noun> --help                   # 列出 noun 下的子命令（verb）
ones-cli <noun> <verb> --help            # 查看具体命令的 flag 列表
ones-cli schema [--format pretty|json]   # 内省完整 tool schema（含参数类型、CliFlag 等元数据）
```

### 交互与安全

| 场景 | Agent 行为 |
|------|-----------|
| 查询类（list、detail、status） | 直接运行，加 `--output-format json` 获取结构化数据 |
| 发布创建 / 扩缩容 / 项目创建 | 展示参数让用户确认后执行，代用户决策时加 `-y` 跳过 |
| 危险操作 | 执行前必须向用户二次确认 |

### 结果附带平台链接

命令输出中如果包含 ones 平台链接，**在摘要末尾附上**，方便用户直接跳转查看。

### 易错点

- **changeflowInfoName vs changeflowName**：
  - `changeflowInfoName`：发布流程**模板**名（固定不变），来自 `deploy changeflow-infos list`
  - `changeflowName`：发布流程**实例**名（每次发布生成新的），来自 `deploy create` 返回值
- **发布确认**：`deploy create` 默认需用户输入 `y` 确认，代用户决策时加 `-y`
- **全局输出 flag**：`--output-format json`（短写 `-o json`），`schema` 命令用独立的 `--format pretty|json`
- **生产环境扩缩容需审批**：`capacity scale` 在生产环境会触发审批流程，提示用户关注 ones 平台进度并用 `capacity scale-status` 轮询
- **budget-sub-account-id 可选**：扩缩容时 `--budget-sub-account-id` 为可选参数，不传时后端自动从预算账户中选取第一个可用子账号；如需精确控制先查 `capacity budget-account list`

---

## 场景路由

| 用户意图 | 对应命令 |
|----------|---------|
| 在服务树中创建新服务 | 见「创建服务工作流」 |
| 查应用的 scene_path | `ones-cli meta applications cost-scene detail --application <app>` |
| 查我有权限的应用 | `ones-cli meta applications permissions list` |
| 查我有权限的服务 | `ones-cli meta services permissions list` |
| 查应用详情（含服务、部署组） | `ones-cli meta applications detail --application <app>` |
| 查服务部署组 | `ones-cli meta services detail --service <service>` |
| 查可用镜像 | `ones-cli meta images list --service <service>` |
| 查发布流程模板 | `ones-cli deploy changeflow-infos list --service <service>` |
| 校验部署组发布状态 | `ones-cli deploy workloadgroups check --service <svc> --workload-groups '["wg"]'` |
| 发布到 sit/staging | `ones-cli deploy create --service ... --changeflow-info ... --workload-groups ... --image-tag ...` |
| 查发布进度/详情 | `ones-cli deploy detail --changeflow <changeflowName>` |
| 诊断发布卡住/失败 | `ones-cli deploy diagnose --changeflow <changeflowName>` |
| 查 Pod 状态 | `ones-cli meta services workloads list --service <svc> --workload-group <wg>` |
| 查 Pod YAML | `ones-cli meta pods detail-yaml --zone <zone> --namespace <ns> --pod <pod>` |
| 查 Pod 日志 | `ones-cli meta pods log --pod <pod> --cluster <cluster> --namespace <ns>` |
| 查我最近的发布 | `ones-cli deploy history list-by-user` |
| 查我在某应用的发布 | `ones-cli deploy history list-by-app --application <app>` |
| 查部署组发布历史 | `ones-cli deploy history list-by-workload-group --service <svc> --workload-group <wg>` |
| 查预算账户/budget-sub-account-id | `ones-cli capacity budget-account list [--service <svc>]` |
| 对部署组扩缩容 | `ones-cli capacity scale --service <svc> --workload-group <wg> --replicas <n> [--budget-sub-account-id <id>]` |
| 查扩缩容状态 | `ones-cli capacity scale-status --service <svc> --workload-group <wg>` |
| 查我的测试项目列表 | `ones-cli project list` |
| 查测试项目详情 | `ones-cli project describe --project <项目名>` |
| 创建测试项目 | `ones-cli project create --alias ... --lane ... --expire-days ... --applications '<json>'` |
| 下线/删除测试项目 | `ones-cli project delete --project <项目名>` |
| 测试项目泳道发布 | `ones-cli project deploy --project ... --service ... --image-tag ...` |
| 重启服务工作负载 | `ones-cli meta workloads restart --application <app> --service <svc> --env <env> --zone <zone> --namespace <ns> --name <name> --workload-type <type>` |
| 重建 Pod | `ones-cli meta pods rebuild --application <app> --service <svc> --cluster <cluster> --namespace <ns> --pod <pod>` |

---

## 工作流

### 1. 完整发布流程

```bash
# Step 1 — 确认服务权限
ones-cli meta services permissions list --output-format json

# Step 2 — 查询可用镜像
ones-cli meta images list --service <service> --output-format json

# Step 3 — 查询发布流程模板及部署组
ones-cli deploy changeflow-infos list --service <service> --output-format json

# Step 4 — 校验部署组状态
ones-cli deploy workloadgroups check \
  --service <service> \
  --workload-groups '["<wg1>", "<wg2>"]' \
  --output-format json

# Step 5 — 创建发布（展示参数让用户确认，代用户决策时加 -y）
ones-cli deploy create \
  --service <service> \
  --changeflow-info <changeflowInfoName> \
  --workload-groups '["<wg1>"]' \
  --image-tag <tag> \
  --description "发布描述" \
  -y \
  --output-format json

# Step 6 — 轮询发布进度（status 变为 success 或 failed 时结束）
ones-cli deploy detail --changeflow <changeflowName> --output-format json

# Step 7 — 发布异常时诊断
ones-cli deploy diagnose --changeflow <changeflowName> --output-format json
```

---

### 2. 扩缩容流程

生产环境扩缩容会触发审批流程，需等待 ones 平台审批通过后生效。

```bash
# Step 1 — 查询预算账户，获取 budget-sub-account-id（子账号 accountId）
ones-cli capacity budget-account list [--service <service>] --output-format json

# Step 2 — 发起扩缩容（展示参数后用户确认，代用户决策时加 -y）
ones-cli capacity scale \
  --service <service> \
  --workload-group <workloadGroupName> \
  --replicas <n> \
  [--budget-sub-account-id <accountId>] \
  --description "扩容原因" \
  -y \
  --output-format json

# Step 3 — 查询扩缩容进度（可轮询，isScaling=false 时完成）
ones-cli capacity scale-status \
  --service <service> \
  --workload-group <workloadGroupName> \
  --output-format json
```

---

### 3. 创建服务工作流

在服务树中注册新服务（ones_service 类型），需要 Git 仓库地址和应用归属的 scene_path。

```bash
# Step 1 — 查询应用详情，获取 scene_path（应用关联的成本场景路径）
ones-cli meta applications cost-scene detail --application <appName> --output-format json
# 返回字段：scene_path（直接用于 --scene-path）、path、prd_line、biz_line
# 若应用不在用户权限列表内，提示前往 https://tree.devops.xiaohongshu.com 申请权限
```

```bash
# Step 2 — 确认 Git 仓库地址
# 询问用户："请提供该服务的 Git 仓库地址（如：https://code.devops.xiaohongshu.com/xxx/yyy）"
#
# 如果用户没有仓库：
#   → 使用 project-skeleton-skill 创建仓库
#       适用场景：新建 IDL 工程、Thrift API 工程、后端 Java 工程
#       非 Java 工程建议提示用户手动创建仓库（project-skeleton-skill 主要面向 Java）
#       建议在本地 CodeWiz 环境中使用，远程环境可能运行异常
#   → 如果 project-skeleton-skill 未安装，尝试自动安装：
#       clawhub install project-skeleton-skill
#   → 如自动安装失败，提示用户前往以下链接手动安装后继续：
#       https://skills.devops.xiaohongshu.com/hub/search?q=project-skeleton-skill&skill=project-skeleton-skill
#   → 如果 project-skeleton-skill 运行异常或初始化失败，降级提示用户前往以下链接手动新建代码仓库：
#       https://code.devops.xiaohongshu.com/projects/new
```

```bash
# Step 3 — 创建服务（展示所有参数让用户确认后执行）
ones-cli meta services create \
  --application <appName> \
  --service <serviceName> \          # 建议三段式，如 myapp-service-default
  --level <1|2|3> \                  # 服务等级：1=S1 2=S2 3=S3
  --deploy-type k8s \                # 默认 k8s
  --scene-path <scene_path> \        # 来自 Step 1 的 scene_path 字段
  --git-addr <gitRepoUrl> \
  --language <Java|Go|Python|...> \
  -y \
  --output-format json
# 后端自动从当前登录用户信息中获取 creator 和 email，无需手动传入
```

```bash
# Step 3 成功后，向用户提供服务平台链接：
# https://ones.devops.xiaohongshu.com/app-next/{application}/{service}

# Step 4 — 询问是否需要绑定域名
# "服务已创建，是否需要新建域名并将服务挂载到域名上？"
#
# 如果需要：
#   → 使用 edith-tools skill 完成域名创建与服务挂载
#   → 如果 edith-tools skill 未安装，尝试自动安装：
#       clawhub install edith-tools
#   → 如自动安装失败，提示用户前往以下链接手动安装后继续：
#       https://skills.devops.xiaohongshu.com/hub/search?q=edith-tools&skill=edith-tools
```

**注意事项：**
- `--scene-path` 必须来自 `meta applications cost-scene detail` 接口返回的 `scene_path` 字段，**不得手动拼接**
- 用户权限不足时（无该应用权限），提示前往 https://tree.devops.xiaohongshu.com/?treePath=devops.cd.onesapi&treeShowType=1 申请
- `creator` 和 `email-alias` 由后端自动从当前登录用户信息中获取，**无需手动传入**
- 创建前务必通过 `--dry-run` 预览参数（如 ones-cli 支持），确认无误后再执行

---

### 4. 测试项目（泳道）创建流程

```bash
# Step 1 — 查询服务的部署组信息
ones-cli meta services detail --service <service> --output-format json

# Step 2 — 查询可用镜像
ones-cli meta images list --service <service> --output-format json

# Step 3 — 创建测试项目（展示参数后用户确认，代用户决策时加 -y）
ones-cli project create \
  --alias "项目别名" \
  --lane "my-lane-name" \
  --expire-days 7 \
  --applications '[{"name":"<appName>","children":[{"name":"<serviceName>","image_tag":"<tag>","workload_group_name":"<wg>","replicas":1}]}]' \
  --description "描述" \
  -y \
  --output-format json

# Step 4 — 查看项目详情
ones-cli project describe --project <project_name> --output-format json
```

---

### 5. 测试项目泳道发布流程

当用户需要向已有测试项目的泳道环境发布新镜像时使用：

```bash
# Step 1 — 查询测试项目详情，确认项目名、服务名和部署组
ones-cli project describe --project <project_name> --output-format json

# Step 2 — 查询可用镜像
ones-cli meta images list --service <service> --output-format json

# Step 3 — 向测试项目泳道发布（展示参数后用户确认，代用户决策时加 -y）
# 注意：--project 填写项目名称（非别名 alias），如 psit-songxixi
# --workload-groups 可选，不传则由后端自动查找项目下该服务的部署组
ones-cli project deploy \
  --project <project_name> \
  --service <service> \
  --image-tag <tag> \
  [--workload-groups '["<wg1>", "<wg2>"]'] \
  -y \
  --output-format json
# 返回：每个部署组对应的 changeflow_name，以及成功/失败统计
```

**注意事项：**
- `--project` 填写项目名（如 `psit-songxixi`），**不是别名 alias**
- 支持同时发布多个部署组，每个部署组独立创建一个发布流程
- `workloadGroups` 为可选参数，不传时后端自动查找该项目下对应服务的部署组
- 泳道发布**不需要**传 `--changeflow-info`
- 发布成功后可通过 `ones-cli deploy detail --changeflow <name>` 查询各部署组进度

---

### 6. 测试项目下线流程

```bash
# 下线前确认项目名（不可逆，Agent 必须向用户二次确认）
ones-cli project list --output-format json

# 下线测试项目（需二次确认）
ones-cli project delete --project <project_name> -y --output-format json
```

---

### 7. 服务重启流程

```bash
# Step 1 — 查询服务部署组及工作负载信息
ones-cli meta services detail --service <service> --output-format json
# 从返回中获取：env、zone、namespace、name（workload name）、workloadType

# Step 2 — 重启工作负载（展示参数后用户确认，代用户决策时加 -y）
# maxSurge/maxUnavailable 仅支持百分比格式（如 0%、20%），不允许整数
ones-cli meta workloads restart \
  --application <appName> \
  --service <childAppName> \
  --env <env> \
  --zone <zone> \
  --namespace <namespace> \
  --name <workloadName> \
  --workload-type <workloadType> \
  [--max-surge 0%] \
  [--max-unavailable 20%] \
  -y \
  --output-format json
# 返回：changeflowName，可通过 deploy detail 查询发布进度

# Step 3 — 查询重启进度
ones-cli deploy detail --changeflow <changeflowName> --output-format json
```

---

### 8. Pod 重建流程

```bash
# Step 1 — 查询异常 Pod 信息
ones-cli meta services workloads list --service <svc> --workload-group <wg> --output-format json
# 从返回中获取：pod 名、cluster、namespace

# Step 2 — 重建 Pod（需二次确认，操作不可逆）
ones-cli meta pods rebuild \
  --application <appName> \
  --service <serviceName> \
  --cluster <cluster> \
  --namespace <namespace> \
  --pod <podName> \
  -y \
  --output-format json
```

---

### 5. 发布环境说明

- ones 后端负责发布环境安全校验，线上环境发布需通过审批流程
- 部署组命名规则：

| 环境 | 命名格式 | 示例 |
|------|---------|------|
| SIT | `{zone}.{serviceName}` | `sit.onesapi-service-default` |
| Staging | `{zone}.{serviceName}.staging` | `qcsh3-tools.onesapi-service-default-staging` |
| 泳道 | `{zone}.{serviceName}.{laneName}` | `qcsh3-tools.onesapi-service-default-my-lane` |

---

## 全局选项

| Flag | 说明 |
|------|------|
| `--host <url>` | 临时覆盖 ONES 服务地址（默认 https://ones.devops.xiaohongshu.com） |
| `-o, --output-format <format>` | 输出格式：`table` / `json` / `yaml` / `pretty` / `csv`（默认 `table`） |
| `-h, --help` | 查看帮助信息 |

---

## 命令索引

> 快速索引，具体参数以 `ones-cli <noun> <verb> --help` 输出为准。

### auth — 鉴权管理

| 命令 | 说明 |
|------|------|
| `ones-cli auth login` | 登录 ONES（device code flow） |
| `ones-cli auth status` | 查看当前登录状态 |
| `ones-cli auth refresh` | 续期当前 token |

### meta — 元信息查询

| 命令 | 说明 |
|------|------|
| `ones-cli meta applications list [--application <关键字>]` | 获取应用列表 |
| `ones-cli meta applications detail --application <app>` | 获取应用详情（含服务、部署组） |
| `ones-cli meta applications permissions list` | 获取用户有权限的应用列表 |
| `ones-cli meta services list` | 获取所有服务列表 |
| `ones-cli meta services detail --service <svc> [--application <app>]` | 获取服务详情（部署组列表） |
| `ones-cli meta services favorite --service <svc>` | 查询服务被哪些用户收藏 |
| `ones-cli meta services users list` | 获取服务下有发布权限的人员 |
| `ones-cli meta services permissions list` | 获取用户有权限的服务列表 |
| `ones-cli meta images list --service <svc>` | 获取服务可用镜像版本（倒序） |
| `ones-cli meta applications cost-scene detail --application <app>` | 查询应用在服务树中的 scene_path、产品线、业务线等信息，用于创建服务时的 --scene-path 参数 |
| `ones-cli meta services create --application <app> --service <svc> --level <1\|2\|3> --deploy-type k8s --scene-path <path> --git-addr <url> --language <lang> [-y]` | 在服务树中新建在线服务（ones_service），写操作需二次确认 |
| `ones-cli meta pods log --pod <pod> --cluster <cluster> --namespace <ns> [--container <name>] [--lines <n>] [-f] [-P]` | 查看 Pod 日志，支持 follow 模式（实时追踪）、查看上一容器日志、指定行数 |
| `ones-cli meta pods rebuild --application <app> --service <svc> --cluster <cluster> --namespace <ns> --pod <pod> [-y]` | 重建 Pod（需二次确认） |
| `ones-cli meta workloads restart --application <app> --service <svc> --env <env> --zone <zone> --namespace <ns> --name <name> --workload-type <type> [--max-surge <pct>] [--max-unavailable <pct>] [-y]` | 重启服务工作负载（滚动重启，返回 changeflowName） |

### deploy — 发布管理

| 命令 | 说明 |
|------|------|
| `ones-cli deploy create --service <svc> --changeflow-info <name> --workload-groups '<json>' --image-tag <tag> [-y]` | 创建发布流程 |
| `ones-cli deploy changeflow-infos list --service <svc>` | 查询发布流程模板及部署组 |
| `ones-cli deploy workloadgroups check --service <svc> --workload-groups '<json>'` | 校验部署组发布状态 |
| `ones-cli deploy detail --changeflow <name>` | 查询发布流程实例详情 |
| `ones-cli deploy diagnose --changeflow <name>` | 诊断发布流程异常 |
| `ones-cli meta services workloads list --service <svc> --workload-group <wg>` | 查询部署组下工作负载及 Pod |
| `ones-cli meta pods detail-yaml --zone <zone> --namespace <ns> --pod <pod>` | 获取 Pod YAML 详情 |
| `ones-cli deploy history list-by-user [--user <user>]` | 查询我最近 7 天的发布 |
| `ones-cli deploy history list-by-app --application <app> [--user <user>]` | 查询我在应用下的发布 |
| `ones-cli deploy history list-by-workload-group --service <svc> --workload-group <wg>` | 查询部署组发布历史 |
| `ones-cli deploy history list-latest-by-app --application <app>` | 查询应用各服务最新发布记录 |

### capacity — 扩缩容管理

| 命令 | 说明 |
|------|------|
| `ones-cli capacity budget-account list [--service <svc>]` | 查询预算账户及子账号，获取 budget-sub-account-id |
| `ones-cli capacity scale --service <svc> --workload-group <wg> --replicas <n> [--budget-sub-account-id <id>] [--description <desc>] [-y]` | 发起扩缩容（生产环境需审批） |
| `ones-cli capacity scale-status --service <svc> --workload-group <wg>` | 查询扩缩容状态与进度 |

### project — 测试项目（泳道）管理

| 命令 | 说明 |
|------|------|
| `ones-cli project list` | 查询当前用户拥有的测试项目列表 |
| `ones-cli project describe --project <项目名>` | 查询测试项目完整详情（应用、路由、成员等） |
| `ones-cli project create --alias <别名> --lane <泳道名> --expire-days <天数> --applications '<json>' [-y]` | 创建测试项目 |
| `ones-cli project delete --project <项目名> [-y]` | 下线/删除测试项目（不可逆，需二次确认） |
| `ones-cli project deploy --project <项目名> --service <svc> --image-tag <tag> [--workload-groups '<json>'] [-y]` | 向测试项目泳道发布（支持多部署组并发，每组独立创建发布流程） |

### 其他命令

| 命令 | 说明 |
|------|------|
| `ones-cli version` | 显示 ones-cli 版本号 |
| `ones-cli update` | 更新 ones-cli 到最新版本 |
| `ones-cli schema [--format pretty\|json]` | 内省完整 tool schema（含 Group/Command/CliFlag 等 CLI 元数据） |
| `ones-cli completion` | 生成 Shell 自动补全脚本 |

---

## 错误处理

| 场景 | Agent 行为 |
|------|-----------|
| `ones-cli` 未安装 | 执行安装命令后重试 |
| 未登录 / token 过期 | 运行 `ones-cli auth login`，**该命令会返回一个鉴权链接，必须将链接直接返回给用户，让用户点击完成认证** |
| 服务/部署组不存在 | 用 `meta services list` 或 `meta applications detail` 确认名称是否正确 |
| 发布状态异常 | 用 `deploy diagnose` 诊断，结合 Pod YAML 和日志定位原因 |
| 扩缩容需指定资源池 | 先运行 `capacity budget-account list` 查询子账号 accountId，再加 `--budget-sub-account-id` 重试 |
| 生产扩缩容需审批 | 提示用户关注 ones 平台审批进度，轮询 `capacity scale-status` 追踪结果 |
| project create 参数格式错误 | 检查 `--applications` 是否为合法 JSON 数组，先通过 `meta services detail` 和 `meta images list` 查询填入 |
| 测试项目泳道发布报错 | 使用独立的 `ones-cli project deploy` 命令（不再使用 `deploy create --is-person-project`），检查参数 `--project`（项目名非别名）和 `--service` 是否正确 |
| workloads restart maxSurge/maxUnavailable 格式错误 | 只支持百分比格式如 `0%`、`20%`，不接受整数，检查参数格式后重试 |
