---
name: xray-topology
description:
  查询 Xray 服务拓扑关系，支持三种拓扑类型：流量入口拓扑（按 HTTP 入口 URL
  查上下游）、服务拓扑（按服务名查上下游，含性能指标）、CAT 拓扑（降级用树形拓扑）。触发场景：(1)
  用户说"查看某服务的拓扑"、"某服务依赖了哪些下游"、"谁调用了某服务"；(2) 用户说"查某个 HTTP
  入口的拓扑"、"这个接口的上下游关系"；(3)
  用户说"服务依赖图"、"拓扑图"、"调用关系"、"上下游依赖"；(4) 用户需要了解服务的调用链路结构时。
---

# XRay 拓扑查询

> `{SKILL_DIR}` 为本 skill 所在目录的绝对路径，执行脚本时必须使用绝对路径。

## 概述

支持三种拓扑查询模式，根据用户意图自动选择：

| 模式                      | 适用场景                              | 接口                                        | 请求方式                    |
| ------------------------- | ------------------------------------- | ------------------------------------------- | --------------------------- |
| **SERVICE**（服务拓扑）   | 查某服务的上下游依赖（含性能指标）    | `POST /searchAdvancedRpcTopology`           | JSON Body，时间单位**秒**   |
| **ENTRY**（流量入口拓扑） | 查某 HTTP 入口 URL 的上下游           | `POST /searchEntryTopology`                 | JSON Body，时间单位**毫秒** |
| **CAT**（CAT 拓扑）       | 无 SERVICE 数据时降级、或仅需树形结构 | `GET /application/topology/serviceTopology` | Query 参数，时间单位**秒**  |

接口参数与响应字段详见 [references/api.md](references/api.md)。

---

## 工作流程

### Step 1：判断查询模式

| 用户意图                                                  | 选择模式                          |
| --------------------------------------------------------- | --------------------------------- |
| 提供了 HTTP URL（如 `mall.xiaohongshu.com/api/store/sc`） | **ENTRY**                         |
| 提供了服务名（如 `checkoutcenter-service-defaultunit`）   | **SERVICE**，无数据则降级 **CAT** |
| 明确要求"CAT 拓扑"或"树形拓扑"                            | **CAT**                           |
| 未明确时，默认                                            | **SERVICE**                       |

### Step 2：收集参数

**SERVICE / CAT 模式必要参数：**

| 参数            | 必填 | 说明                                         |
| --------------- | ---- | -------------------------------------------- |
| `app`           | 是   | 服务名，原样使用，禁止修改                   |
| `start` / `end` | 是   | 时间范围，转为秒级时间戳                     |
| `service`       | 否   | 具体接口名（RPC 方法名），不填则查整个服务   |
| `focusOption`   | 否   | 默认 `direct_relations_each_direction_top10` |

**ENTRY 模式必要参数：**

| 参数                    | 必填 | 说明                                                       |
| ----------------------- | ---- | ---------------------------------------------------------- |
| `entryList`             | 是   | HTTP 入口 URL 列表，如 `mall.xiaohongshu.com/api/store/sc` |
| `startTime` / `endTime` | 是   | 时间范围，转为**毫秒**时间戳                               |
| `level`                 | 否   | `app`（默认）或 `service`（接口级）                        |

**时间收集原则：**

- 若用户说"最近 1 小时" → `end=now, start=now-3600`
- 若用户未说明时间 → 主动询问
- 使用 `to_timestamp.py` 转换时间字符串：
  ```bash
  python3 {SKILL_DIR}/scripts/to_timestamp.py --range "2024-03-25 14:00:00 - 2024-03-25 15:10:10"
  ```

### Step 3：调用接口

```bash
# SERVICE 模式（推荐默认）
python3 {SKILL_DIR}/scripts/topology_query.py \
  --mode SERVICE \
  --app "<服务名>" \
  --start <秒级时间戳> \
  --end <秒级时间戳> \
  [--service "<RPC接口名>"] \
  [--focus-option "direct_relations_each_direction_top10"]

# ENTRY 模式
python3 {SKILL_DIR}/scripts/topology_query.py \
  --mode ENTRY \
  --entry "mall.xiaohongshu.com/api/store/sc" \
  --start-ms <毫秒时间戳> \
  --end-ms <毫秒时间戳> \
  [--level app]

# CAT 模式（降级或树形结构）
python3 {SKILL_DIR}/scripts/topology_query.py \
  --mode CAT \
  --app "<服务名>" \
  --start <秒级时间戳> \
  --end <秒级时间戳> \
  [--with-api false]
```

### Step 4：解析并输出结果

#### SERVICE / ENTRY 模式

输出以下内容（无数据时提示降级 CAT）：

1. **核心节点**（defaultNodeId 对应节点）：总调用次数、平均耗时、最大耗时、错误数
2. **上游来源**（入度 > 0 的 edges 按 total 降序）：调用方、次数、放大倍数、流量入口列表
3. **下游依赖**（出度 > 0 的 edges 按 total 降序）：被调用方、类型（RPC/Redis/SQL）、次数、平均耗时
4. **节点健康标签**：列出 status 非 info 的告警节点

#### CAT 模式

输出树形结构摘要：

1. **上游（upstream）**：列出所有调用该服务的上游服务名和调用类型
2. **下游（downstream）**：列出所有该服务依赖的下游服务名、调用类型（RPC/Redis/SQL）

---

## 降级逻辑

SERVICE 模式返回空 nodes/edges 时，自动降级 CAT 查询：

```bash
# 自动降级示例（脚本内部处理）
python3 {SKILL_DIR}/scripts/topology_query.py --mode SERVICE --app "xxx" ...
# → 若 nodes 为空，提示用户并建议改用 --mode CAT 重查
```

---

## 注意事项

- **服务名原样透传**：`--app` 严格使用用户提供的原始值，禁止补全或修改
- SERVICE 时间单位为**秒**，ENTRY 时间单位为**毫秒**，脚本参数已区分（`--start` vs `--start-ms`）
- `focusOption` 可选值：`direct_relations_each_direction_top10`（默认）/ `all_direct_relations` /
  `all_relations_of_entry_list` / `all_down_stream`
- `level` 可选值：`app`（应用级，默认）/ `service`（接口级，边会细化到具体 RPC 方法）
- CAT 拓扑为静态树形结构，无性能指标，仅反映调用关系
