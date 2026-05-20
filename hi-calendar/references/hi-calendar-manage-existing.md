---
name: hi-calendar-manage-existing
description: hi-calendar 的已有日程管理参考。处理定位、取消、编辑已有日程，以及循环日程范围确认时读取。
---

# hi-calendar-manage-existing

用于处理已有日程的定位、详情查看、取消和进入编辑流程。

## 定位原则

1. 有明确 `scheduleId` 时，优先用 `calendar:get-schedule-detail`。
2. 没有明确 ID 时，用 `calendar:get-user-schedules` 在用户给定时间范围内查找；不要擅自扩大范围。
3. 命中多个候选时，展示摘要并让用户选择。
4. 目标定位失败或查询失败时停止说明，不要用相似标题或第一个结果替代。

## 查看详情

- 查看会议详情时，用 `calendar:get-schedule-detail --schedule-items "scheduleId:type"`。
- 输出保留标题、时间、参会人、会议室、创建人、循环信息、文档等关键字段。
- 用户基于上一步列表说“第二个 / 那个会”时，可以使用上一轮已展示的 `scheduleId` 和 `scheduleInstanceType`。

## 编辑已有日程

1. 先定位目标并读取详情。
2. 展示当前状态，再确认用户要改什么。
3. 若修改时间、参会人、会议室或文档，转 `hi-calendar-writing.md` 的编辑流程收敛事实和风险。
4. 写前确认展示差异：旧值 → 新值。
5. 用户明确确认后，调用 `calendar:edit-schedule`。

## 取消日程

1. 先定位并确认目标日程。
2. 复述标题、时间、创建人、影响范围和不可逆风险。
3. 用户明确确认后，调用 `calendar:cancel-schedule`。
4. 若用户不是创建人或权限不足，说明限制，不要伪造取消成功。

## 循环范围

- `scheduleInstanceType=1`：普通日程。
- `scheduleInstanceType=2`：循环主日程。
- `scheduleInstanceType=3`：循环子日程，通常带 `sequenceScheduleId` 指向主日程。

处理循环日程时必须确认范围：

- 只取消 / 编辑本次：使用子日程或 occurrence 语义。
- 取消 / 编辑整个系列：定位主日程并确认会影响后续所有实例。

不得根据“周会”“以后都不开了”等模糊说法直接执行；先复述影响范围让用户确认。

## 与其他 reference 的关系

- 编辑变更涉及写入字段时，转 `hi-calendar-writing.md`。
- 需要解释忙闲、时区或冲突时，读 `hi-calendar-checks-and-timezone.md`。
- 输出遵循 `hi-calendar-output-guidelines.md`。
