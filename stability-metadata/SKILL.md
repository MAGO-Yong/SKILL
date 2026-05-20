---
name: stability-metadata
description: >-
  HA DevOps 稳定性元数据：业务线树、场景列表、应急配置、流量分组、场景核心服务、员工查询、服务依赖治理（POST：可选 scene 限定场景内下游链路，Service/Redis/MySQL 等）、LLM Skill 直连上下游（可按业务线/场景剪枝）、服务标准名与别名。
  路径中的 bizLineSegment / scenePathSegment 为动态段；HA meta 类接口不带 sceneId Query。触发：稳定性元数据、业务线、场景、应急响应、流量入口、核心服务、服务依赖、下游依赖、上下游剪枝、标准名别名。
---

# 稳定性元数据（HA Meta）

通过 **`HA_DEVOPS_API_BASE`** 拉取业务线、场景、应急与流量元数据、场景核心服务、服务下游依赖、员工信息等。响应以实际 JSON 为准，勿编造 `sceneId` 或其它 ID。

---

## 文档地图

| 你要做的事 | 读哪里 |
|------------|--------|
| 基址、认证、动态路径段约定 | **§1** |
| 接口路径总览 | **§2**（**§2.2～2.6** 为 Query / Body 参数详解 |
| 推荐调用顺序 | **§3** |
| Agent 如何展示结果 | **§4** |
| 本地 `curl` 脚本 | **§5** |

---

## 1. 基址与环境变量

| 用途 | 默认值 | 说明 |
|------|--------|------|
| HA 元数据与 v3 | `HA_DEVOPS_API_BASE`=`https://ha.devops.xiaohongshu.com` | 路径接在基址后，以 `/api/` 开头 |

SIT/beta 若部署同源网关，只替换 host，路径不变（以实际为准）。

**认证**：内网/VPN + 登录态；`curl` 加 Cookie/Token。失败如实说明，勿伪造数据。

**响应壳**：`/api/meta/*` 常见 `{ "success", "code", "data" }`；`/api/v3/*` 以实际为准。

### 1.1 动态路径段（勿写死）

| 占位符 | 含义 | 从哪里取 |
|--------|------|----------|
| **`{bizLineSegment}`** | 业务线在 URL 中的路径段 | 业务线树等返回（字段名以接口为准） |
| **`{scenePathSegment}`** | 场景在 URL 中的路径段 | 场景列表/详情等；与 `configs`、`groups`、Edith 共用 |

### 1.2 `sceneId` 易混点

| 接口域 | 是否使用 `sceneId`（Query） | 说明 |
|--------|------------------------------|------|
| **`/api/meta/...`**（configs、groups 等） | **否** | 范围由 **`{scenePathSegment}`** 体现，**禁止**拼 `?sceneId=` |
| **`GET /api/v3/scene`** | **是** | Query 参数 **`id`** = 场景 ID，见 **§2.3** |
| **`POST /api/v3/dependence/governance`** | **否**（Body 内可选 **`scene`** 字符串） | 见 **§2.4** |

---

## 2. 接口速查

### 2.1 `/api/meta/...`（仅路径或固定 Query）

| 能力 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 业务线树 | GET | `/api/meta/biz-line/tree` | Query：`treeType=biz` |
| 业务线下场景列表 | GET | `/api/meta/biz-line/{bizLineSegment}/scenes` | 仅路径 **`{bizLineSegment}`**；**无**额外 Query |
| 应急/协同人员配置 | GET | `/api/meta/biz-line/scene/{scenePathSegment}/configs` | 仅路径 **`{scenePathSegment}`**；**无** Query |
| 流量入口分组 | GET | `/api/meta/{scenePathSegment}/groups` | 仅路径 **`{scenePathSegment}`**；**无** Query |
| Edith 未绑 HA 入口 | GET | `/api/meta/{scenePathSegment}/request_group/edith` | 仅路径；**无**仓库脚本，自行 `curl` |

**生产 URL 示例**（`outflowrec` 仅为 **`scenePathSegment`** 示例，须替换）：

```
https://ha.devops.xiaohongshu.com/api/meta/biz-line/tree?treeType=biz
https://ha.devops.xiaohongshu.com/api/meta/biz-line/{bizLineSegment}/scenes
https://ha.devops.xiaohongshu.com/api/meta/biz-line/scene/outflowrec/configs
https://ha.devops.xiaohongshu.com/api/meta/outflowrec/groups
https://ha.devops.xiaohongshu.com/api/meta/outflowrec/request_group/edith
```

---

### 2.2 `GET /api/v3/scene`（场景核心服务）

```http
GET /api/v3/scene?with_microservices=true&id={sceneId}
```

| Query 参数 | 必填 | 说明 |
|------------|------|------|
| `id` | 是 | 场景 ID（`sceneId`），来自场景列表或业务约定 |
| `with_microservices` | 是 | 固定 `true` 以拉核心微服务列表 |

**完整 URL 示例**：

`https://ha.devops.xiaohongshu.com/api/v3/scene?with_microservices=true&id={sceneId}`

---

### 2.3 `GET /api/v3/employee/query`（用户信息）

```http
GET /api/v3/employee/query?key={key}
```

| Query 参数 | 必填 | 说明 |
|------------|------|------|
| `key` | 是 | 检索关键字：内部**署名（花名）**、**邮箱**、**中文姓名**、**姓名拼音**等；含中文或特殊字符时须 **URL 编码** |

**完整 URL 示例**：

`https://ha.devops.xiaohongshu.com/api/v3/employee/query?key=ruanrenzhao@xiaohongshu.com`

---

### 2.4 `POST /api/v3/dependence/governance`（服务下游依赖）

用于「服务依赖管理 / 场景拓扑」：**按上游服务**查 **Service、Redis、MySQL** 等下游及依赖强弱、归属场景等；返回字段以接口为准。

```http
POST /api/v3/dependence/governance
Content-Type: application/json
```

完整 URL：`{HA_DEVOPS_API_BASE}/api/v3/dependence/governance`

#### 2.4.1 请求体（JSON 对象）

字段名一般为 **camelCase**；**后台新增字段时只需扩展 JSON**，不必改 shell 脚本（见 **§5** 调用约定）。

| 字段 | 必填 | 说明 |
|------|------|------|
| `source` | 是 | 上游 **serviceName**，与页面「上游服务」一致 |
| `scene` | 否 | 场景标识（如场景 code / 英文名）。**有则只查该场景内依赖链路**；无则不限定场景 |
| `isValid` | 否 | `true` / `false` / `null`，与页面「满足高可用规范」等筛选语义对齐；`null` 常表示不按该维度过滤 |

**Body 示例（不限定场景）**

```json
{
  "source": "adchips3-service-new",
  "isValid": null
}
```

**Body 示例（限定场景 + 筛选）**

```json
{
  "source": "adchips3-service-new",
  "scene": "shequsearch",
  "isValid": false
}
```

#### 2.4.2 调用约定（与 chaos-blade 写接口一致思路）

- Body **整段**放入 **JSON 文件**或 **stdin（`-`）** 传给 **`fetch_dependence_governance.sh`**，避免为每个字段维护 positional 组合。  
- 列表类返回在 `data` 内时，常见列与门户表格对齐：**上游服务（等级）**、**上游类型**、**下游服务/资源（等级）**、**下游类型**（`service` / `Redis` / `MySQL` 等）、**依赖关系（预期/实际）**、**归属场景** — 具体键名以响应为准。

---

### 2.5 `POST /api/llm-skill/direct-relations`（服务上下游，业务线/场景剪枝）

用于按服务查 **直连上下游**；可选 **`bizLines`**、**`scenes`** 缩小范围（剪枝）。字段以后台为准。

```http
POST /api/llm-skill/direct-relations
Content-Type: application/json
```

完整 URL：`{HA_DEVOPS_API_BASE}/api/llm-skill/direct-relations`

| 字段 | 必填        | 说明                                               |
|------|-----------|--------------------------------------------------|
| `svc` | 是         | 服务名（如 `searchapi-service-default`）               |
| `direction` | 服务拓扑保留的范围 | upstream(上游)/ downstream(下游) / both(都保留)，默认 both |
| `bizLines` | 否         | 业务线标识数组，用于剪枝                                     |
| `scenes` | 否         | 场景名数组，用于剪枝                                       |

**Body 示例（获取服务上下游拓扑）**

```json
{
  "svc": "searchapi-service-default",
  "direction": "both"
}
```

**Body 示例（获取根据业务线剪枝后的上下游拓扑）**

```json
{
  "svc": "searchapi-service-default",
  "direction": "both",
  "bizLines": ["search"]
}
```

**Body 示例（获取根据业务线和场景剪枝后的上下游拓扑）**

```json
{
  "svc": "searchapi-service-default",
  "direction": "both",
  "bizLines": ["search"],
  "scenes": ["shequsearch"]
}
```

**调用约定**：与 **§2.4.2** 相同，整段 JSON 交给 **`fetch_direct_relations.sh`**（文件或 stdin `-`）。

---

### 2.6 `GET /api/llm-skill/std-alias`（服务标准名与别名）

```http
GET /api/llm-skill/std-alias?svc={svc}
```

| Query 参数 | 必填 | 说明                                |
|------------|------|-----------------------------------|
| `svc` | 是 | 服务名称|

**完整 URL 示例**：

`https://ha.devops.xiaohongshu.com/api/llm-skill/std-alias?svc=com.xiaohongshu.ads.sdk.AdsService`

---

## 3. 推荐调用顺序

1. **`GET …/biz-line/tree?treeType=biz`** → `bizId`、名称、**`bizLineSegment`**。  
2. **`GET …/biz-line/{bizLineSegment}/scenes`** → 场景列表；解析 **`scenePathSegment`**。  
3. **应急**：`GET …/biz-line/scene/{scenePathSegment}/configs`（**§2.1**）。  
4. **流量**：`GET …/meta/{scenePathSegment}/groups`（**§2.1**）。  
5. **（可选）Edith**：`GET …/meta/{scenePathSegment}/request_group/edith`（**§2.1**）。  
6. **核心服务**：**§2.2**（`sceneId` 来自场景列表或业务约定）。  
7. **查人**：**§2.3**。  
8. **服务下游依赖**：**§2.4**；用户指定场景时 Body **必须**含 **`scene`**。  
9. **服务上下游服务拓扑**：**§2.5**。  
10. **服务标准名/别名**：**§2.6**。

---

## 4. Agent 输出建议

- **业务线 / 场景**：`bizId`、`sceneId`（若有）、名称；注明 **`bizLineSegment`** / **`scenePathSegment`**（若已解析）。  
- **应急 / 流量**：联系人、分组名、入口 path/host；Edith 与 `groups` 语义分开说明。  
- **核心服务**：服务名、`isEntrySvc` 等（**§2.2**）。  
- **用户信息**：多命中列候选并请用户确认（**§2.3**）。  
- **服务依赖**：是否带 **`scene`**；按 **§2.4.2** 与门户「服务依赖管理」列表展示，键名以 JSON 为准。  
- **服务上下游服务拓扑**：是否带 **`bizLines`** / **`scenes`** 剪枝（**§2.5**）。  
- **服务标准名/别名**：**§2.6**，键名以 JSON 为准。

---

## 5. 本地脚本（`scripts/`）

默认 **`HA_DEVOPS_API_BASE=https://ha.devops.xiaohongshu.com`**，可用环境变量覆盖。

**POST + JSON**：依赖治理用 **`<request.json>`** 或 **`-`（stdin）** 传入 **§2.4.1** 完整 Body；**不要**堆叠 positional。脚本内用 **`python3`** 校验 JSON。

| 脚本 | 参数 | 对应 |
|------|------|------|
| [fetch_biz_line_tree.sh](scripts/fetch_biz_line_tree.sh) | 无 | **§2.1** 业务线树 |
| [fetch_biz_scenes.sh](scripts/fetch_biz_scenes.sh) | `bizLineSegment` | **§2.1** 场景列表 |
| [fetch_scene_emergency_configs.sh](scripts/fetch_scene_emergency_configs.sh) | `scenePathSegment` | **§2.1** 应急配置 |
| [fetch_scene_traffic_groups.sh](scripts/fetch_scene_traffic_groups.sh) | `scenePathSegment` | **§2.1** 流量分组 |
| [fetch_scene_microservices.sh](scripts/fetch_scene_microservices.sh) | `sceneId` | **§2.2** |
| [fetch_employee_query.sh](scripts/fetch_employee_query.sh) | `key` | **§2.3** |
| [fetch_dependence_governance.sh](scripts/fetch_dependence_governance.sh) | `request.json` 或 `-` | **§2.4**（POST） |
| [fetch_direct_relations.sh](scripts/fetch_direct_relations.sh) | `request.json` 或 `-` | **§2.5**（POST） |
| [fetch_std_alias.sh](scripts/fetch_std_alias.sh) | `svc` | **§2.6**（GET） |

```bash
./stability-metadata/scripts/fetch_biz_line_tree.sh
./stability-metadata/scripts/fetch_biz_scenes.sh rec
./stability-metadata/scripts/fetch_scene_emergency_configs.sh outflowrec
./stability-metadata/scripts/fetch_scene_traffic_groups.sh outflowrec
./stability-metadata/scripts/fetch_scene_microservices.sh 21474836481
./stability-metadata/scripts/fetch_employee_query.sh 'user@xiaohongshu.com'
./stability-metadata/scripts/fetch_dependence_governance.sh ./my_dep_request.json
./stability-metadata/scripts/fetch_dependence_governance.sh - <<'EOF'
{"source":"adchips3-service-new","scene":"shequsearch","isValid":false}
EOF
./stability-metadata/scripts/fetch_direct_relations.sh - <<'EOF'
{"svc":"searchapi-service-default","direction":"both","bizLines":["search"],"scenes":["shequsearch"]}
EOF
./stability-metadata/scripts/fetch_std_alias.sh 'com.xiaohongshu.ads.sdk.AdsService'
```
