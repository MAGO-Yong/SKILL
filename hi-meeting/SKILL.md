---
name: hi-meeting
version: 1.0.0
description: 'hi 官方会议详情 Skill，支持按 meetingId 批量查询会议纪要详情'
metadata: { 'openclaw': { 'requires': { 'bins': ["node", "hi"] } } }
---

# 环境准备

若执行 `hi` 命令时提示 `command not found`，通过以下任一方式全局安装：

```bash
# 方式一：npm
npm install -g @xhs/hi-cli --registry=http://npm.devops.xiaohongshu.com:7001

# 方式二：bun
bun install -g @xhs/hi-cli --registry=http://npm.devops.xiaohongshu.com:7001
```

技能核心能力通过 CLI 提供，在执行 CLI 命令时，必须查看运行命令的参数，**禁止**猜测命令用法：

```bash
# 查看具体命令的参数、示例和输出格式
hi meeting --help
```

# 最佳实践

## 核心事实

- 当前 meeting 域**唯一**的纪要查询入口是 `meeting:get-detail-minutes --meeting-ids <meetingId>`
- `meetingCode` / `txMeetingCode` / 会议链接 `joinUrl` **都不是**当前 meeting 命令支持的入参
- `calendar:get-user-schedules` / `calendar:get-schedule-detail` 只能帮助定位候选会议；只有当返回中**真实存在** `tencentMeetingDetail.meetingId` 时，才能继续查询纪要

## meetingId 获取方式

`meetingId` 是查询会议纪要详情的核心标识。获取途径：

1. **用户直接提供**：用户给出 meetingId 时，作为 `--meeting-ids` 入参
2. **从日程获取**：通过 `calendar:get-user-schedules` 或 `calendar:get-schedule-detail` 查询日程，优先从 `tencentMeetingDetail.meetingId` 字段提取
   - 部分日程只会返回 `tencentMeetingDetail.meetingCode` / `txMeetingCode` / `joinUrl`，不一定返回 `meetingId`
   - 当 `tencentMeetingDetail.meetingId` 为空时，应告知用户该日程未返回可用 meetingId，无法继续查询会议纪要
   - **不得**把 `meetingCode` / `txMeetingCode` / `joinUrl` 当作 `meetingId` 使用
   - **不得**根据 `meetingCode`、会议链接、标题、参会人等信息猜测或拼接 `meetingId`
   - 多个日程匹配时，须向用户确认具体是哪一个

## 调用方式

具体参数、示例和输出字段以 `meeting:get-detail-minutes --help` 为准。当前命令使用 `--meeting-ids` 批量查询，支持单个或多个 meetingId（逗号分隔）。

## 自然语言定位的正确理解

- 用户通过时间、标题、参会人、最近一次会议等自然语言描述时，应先使用 calendar 域命令定位候选日程
- 这些自然语言线索**只用于筛选候选会议**，不等于已经具备查询纪要的必要参数
- 只有当候选日程里存在 `tencentMeetingDetail.meetingId` 时，才能继续调用 meeting 域命令
- 如果用户给的是会议号、腾讯会议链接、截图识别出的会议链接或 `meetingCode`，当前 meeting 域也**不能直接查询**

## 自然语言定位策略

### 1. 相对时间默认策略

- 遇到“刚才”“上一场”“最近一次”“昨天”“上周三下午”这类相对时间表达时，先使用 `calendar:get-timezone` 获取用户当前时区
- 将相对时间解释为**绝对时间窗**后，再调用 `calendar:get-user-schedules`
- “上一场会”“最近那个会”这类说法，若用户未提供更具体线索，应先在**最近的合理时间窗**内查候选日程；若候选过多，再让用户确认
- 不得跳过时间换算直接猜测某个具体 `scheduleId` 或 `meetingId`

### 2. 标题 / 参会人 / 主题定位策略

- 遇到按会议标题、参会人、主持人、讨论主题来找纪要的场景时，先把这些信息当作**候选筛选条件**
- 若用户**没有提供时间范围**，应优先补问，例如：
  - “你说的是哪天/哪一周的那场会？”
  - “是最近一次那场吗？”
  - “大概是昨天、这周，还是上周？”
- 按参会人定位时，可先用 `search:employee` 查人；若存在同名，必须先确认具体是哪位
- 在没有足够时间范围时，不要假设可以仅凭标题或参会人直接定位到唯一日程

### 3. 批量场景策略

- 遇到“昨天所有会议的纪要”“这周参加过的会有哪些有纪要”这类批量场景时，应先用 `calendar:get-user-schedules` 按时间范围查询日程
- 若查询结果 `hasMore=true`，应继续翻页，直到拿到该时间窗内的完整候选集合，或用户明确表示只看首页结果
- 对每条候选会议，只有在存在 `tencentMeetingDetail.meetingId` 时，才能纳入后续纪要查询
- 若部分会议有 `meetingId`、部分没有，应返回可查询的部分，并明确说明其余会议因缺少 `meetingId` 无法继续

### 4. 固定停止条件

- 当候选日程未返回 `tencentMeetingDetail.meetingId` 时，必须停止后续自动查询
- 停止时应使用清晰、稳定的说明，表达以下意思：
  - “我已经定位到候选会议，但当前日程结果没有返回可用 `meetingId`”
  - “当前 CLI 仅支持通过 `meetingId` 查询纪要”
  - “因此我现在无法继续自动查询这场会议的纪要”
- 不得在停止前尝试把 `meetingCode`、`txMeetingCode`、`joinUrl`、标题、参会人等信息转换成 `meetingId`

## 输出说明

返回值为数组，每个元素对应一个请求的 meetingId；详细字段以 `meeting:get-detail-minutes --help` 的输出说明为准。

## 约束

- `meetingId` 不得猜测或默认，必须由用户提供或从日程结果中的 `tencentMeetingDetail.meetingId` 提取
- 若用户通过模糊描述（时间、名称、参会人等）定位到候选会议，但日程结果未返回 `tencentMeetingDetail.meetingId`，应明确说明当前无法继续自动查询会议纪要
- 若用户只提供 `meetingCode`、`txMeetingCode`、会议链接、截图内容等信息，应明确说明“当前 CLI 仅支持通过 meetingId 查询纪要”
