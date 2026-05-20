---
name: hi-calendar-focus-time
description: hi-calendar 的专注时间参考。处理创建、编辑、取消专注时间及其与普通会议的边界时读取。
---

# hi-calendar-focus-time

用于处理专注时间（Focus Time）相关场景。

专注时间是一种特殊日程类型，用于屏蔽时间段以进行深度工作。

## 管理专注时间

推荐顺序：

1. 把专注时间视为个人事项处理，不走参会人 / 会议室 workflow。
2. 创建或编辑前应使用 `get-user-schedules` 检查用户自身日程冲突，叠加在已有会议上可能是有意为之，需让用户确认。
3. 专注时间使用专门的 create / edit / cancel-focus-time 命令，不和普通会议取消 / 编辑流程混用。
4. 若用户操作的是循环专注时间，仍需先确认是单次还是整个系列。
5. 在真正调用创建 / 编辑 / 取消命令前，必须先复述本次即将执行的操作类型、时间范围和系列范围（如适用），并获得用户明确确认。
6. 若用户尚未明确确认，不得直接执行专注时间写命令。

## 专注时间约束

- **无需 operateCode**：与 `create` / `create-recurring` 不同，专注时间不使用幂等键。
- **无参会人和会议室**：专注时间是个人事项，无需参会人确认和会议室冲突检测。
- **API 返回 void**：创建 / 编辑后需通过 `get-user-schedules` 查询确认并获取 scheduleId。
- 不能复用 `cancel-schedule` 取消专注时间，须使用 `cancel-focus-time`。
- 取消整个循环系列时，传主日程 scheduleId（即 `sequenceScheduleId`）。

## 与其他 reference 的关系

- 若涉及循环实例确认，可参考 `references/hi-calendar-manage-existing.md` 的系列/单次判断思路。
- 若要说明日程冲突或展示输出结果，遵循 `references/hi-calendar-output-guidelines.md`。
