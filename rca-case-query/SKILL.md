---
name: rca-case-query
description: 查询小红书 RCA 故障平台（rca.devops.xiaohongshu.com）的故障 case 信息。使用场景：用户想搜索/查看故障列表，按标题、业务线、场景、级别、故障类型、复盘状态等条件筛选，或追问某条故障的稳定性建议。查询字段灵活，返回格式化结果，支持追问分析。
---

# RCA 故障查询 Skill

## 接口信息

- **URL**: `https://rca.devops.xiaohongshu.com/api/case/search`
- **Method**: POST
- **Content-Type**: application/json

详细字段说明见 [references/api.md](references/api.md)。

## 工作流程

### 1. 解析查询意图

从用户自然语言中提取过滤条件，映射到请求字段。未提及的过滤字段保持 `["null"]`，`type` 默认 `1`。

**常用字段映射：**
| 用户说 | 请求字段 |
|---|---|
| 标题关键词 | `title` |
| P0/P1/P2/P3/P4/Notice | `level` |
| 业务线（推荐/电商/...）| `business_line` |
| 场景（推荐问题排查/...）| `scene` |
| 故障类型（服务端/数据问题/...）| `case_type` |
| 复盘状态（已复盘/未复盘）| `rca_review_status` |
| MTTR | `mttr` |

### 2. 发起请求

```python
import urllib.request, json, os

url = "https://rca.devops.xiaohongshu.com/api/case/search"
payload = {
    "feedback_label": ["null"],
    "level": ["null"],           # 或 ["P0"] / ["P1","P2"]
    "scene": ["null"],
    "business_line": ["null"],   # 或 ["电商"]
    "case_type": ["null"],
    "rca_review_status": ["null"],
    "title": "",                 # 关键词，空字符串=不过滤
    "mttr": ["null"],
    "type": 1,
    "pageNo": 1,
    "pageSize": 10
}
data = json.dumps(payload).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
# 如有 cookie/token 需在 headers 中携带
with urllib.request.urlopen(req, timeout=10) as resp:
    result = json.loads(resp.read())
cases = result["data"]["list"]
total = result["data"]["total"]
```

> **认证**：如接口返回 401/403，需携带内网 SSO Cookie。参考 `data-fe-common-sso` skill 获取登录态。

### 3. 格式化输出

每条故障输出核心字段，见参考格式：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 #8494 [结算下单可用性低于99%持续两分钟（HA）]
   级别: Notice  |  类型: 服务端  |  状态: fixed
   场景: 电商购物车结算  |  业务线: 电商
   创建人: xray  |  创建时间: 2026-03-11 11:55:42
   修复时间: 2026-03-11 12:01:00  |  MTTR: ~5min
   是否RCA: ✅  |  复盘状态: 未复盘
   会议链接: https://meeting.tencent.com/dm/...
```

字段为 null 时省略或显示 `-`，不要显示原始 null。

共找到 **{total}** 条，本页展示 **{len}** 条。

### 4. 追问：稳定性建议

用户追问某条故障后，基于故障信息给出有针对性的稳定性建议，结构如下：

```
## 稳定性建议 — {故障标题}

### 根因分析
根据故障描述/公告，定位根因为：...

### 改进建议
1. **告警优化** - ...
2. **变更管控** - ...
3. **容量/降级** - ...
4. **止损加速** - ...
5. **复盘跟进** - 建议完成 RCA 复盘，沉淀 Action Item

### 参考指标
- MTTR 目标：P0 < 30min，P1 < 60min，Notice < 15min
- 响应时长：发现→响应 目标 < 3min
```

根据实际故障场景灵活增减建议点，避免泛泛而谈。若故障信息不足，可建议用户提供更多上下文。
