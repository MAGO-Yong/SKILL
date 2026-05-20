---
name: hi-calendar-recommend-room
description: hi-calendar 的推荐会议室参考。处理找会议室、按区域推荐会议室、固定时段查可用房间时读取。
---

# hi-calendar-recommend-room

用于生成空间候选。会议室推荐只解决“空间资源”问题，不直接创建会议。

## 何时进入纯会议室分支

只有用户目标明确是“只找会议室 / 只看房间 / 固定时间换房间”，并且不需要一体化时间 + 会议室方案时，才进入本 reference。

如果用户要创建单次会议，且已经有开始时间、结束时间、参会人，并且没有明确只看房间或排除参会人空闲分析，应回到 `hi-calendar-writing.md`，默认使用 `calendar:get-intelligent-recommendation`。

## 命令选择

| 命令 | 适用场景 | 作用 |
| --- | --- | --- |
| `calendar:get-room-schedules` | 固定目标时段内看哪些会议室可用，或检查指定会议室冲突 | 返回房间占用 / 空闲情况 |
| `calendar:get-room-free-time` | 已知区域和查询窗口，只想推荐会议室及其可预约时间 | 返回会议室候选和 `freeTimeList` |
| `calendar:query-room-schedule` | 已知会议室，需要看更长时间窗排期 | 返回该房间排期 |

## 固定时段找房

1. 先确认区域范围；`areaId` 不能猜。用户可以指定单区域或多个区域。
2. 使用 `calendar:get-room-schedules --filter-busy` 查询固定时段可用房间。
3. 展示会议室名称、区域、容量/楼层（如有）、可用状态。
4. 多个候选时等待用户选择，不要自动选第一个。
5. 用户选中会议室后，回到 `hi-calendar-writing.md` 做最终确认。

## 时间窗口内找房

1. 确认区域范围和查询时间窗口。
2. 使用 `calendar:get-room-free-time` 获取会议室和 `freeTimeList`。
3. `duration` 仅在用户给出时长或上下文可靠时传入。
4. 按推荐顺序或时间顺序展示候选。
5. 用户选择后回到写入流程。

## 注意事项

- 区域未明确时不要猜测，也不要默认只查某一区域。
- 多区域是同一轮筛选范围，不要强行提前收敛为单一区域。
- 没有满足条件的房间时，说明无结果，并建议调整区域、时间或会议室约束。
- 纯会议室分支处理完必须回流；不要在本分支中调用 create / edit。
