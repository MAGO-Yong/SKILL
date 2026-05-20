# RCA Case Search API 参考

## 请求字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `title` | string | 标题关键词，空字符串不过滤 |
| `level` | string[] | 故障级别：`P0` `P1` `P2` `P3` `P4` `Notice`，不过滤传 `["null"]` |
| `scene` | string[] | 场景名称（中文），不过滤传 `["null"]` |
| `business_line` | string[] | 业务线（中文），不过滤传 `["null"]` |
| `case_type` | string[] | 故障类型：`服务端` `前端` `数据问题` `非技术`，不过滤传 `["null"]` |
| `rca_review_status` | string[] | 复盘状态：`已复盘` `未复盘`，不过滤传 `["null"]` |
| `feedback_label` | string[] | 反馈标签，通常传 `["null"]` |
| `mttr` | string[] | MTTR 过滤，通常传 `["null"]` |
| `type` | int | 1=全量，2=RCA专项 |
| `pageNo` | int | 页码，从 1 开始 |
| `pageSize` | int | 每页条数，建议 10~30 |

## 响应字段（list 中每条 case）

| 字段 | 说明 |
|---|---|
| `id` | 故障 ID |
| `title` | 故障标题 |
| `desc` | 描述 |
| `level` | 级别：P0/P1/P2/P3/P4/Notice |
| `case_status` | 状态：`fixed`=已修复，`unfix`=未修复 |
| `case_type` | 故障类型 |
| `scene` | 中文场景名 |
| `business_line` | 业务线 |
| `creator` | 创建人 |
| `create_time` | 创建时间 |
| `finish_time` | 修复时间 |
| `response_time` | 响应时间 |
| `location_time` | 定位时间 |
| `find_time` | 发现时间 |
| `start_time` | 故障开始时间 |
| `is_rca` | 是否产出 RCA：`y`/`n` |
| `rca_review_status` | 复盘状态：`已复盘`/`未复盘`/null |
| `related_rcaId` | 关联 RCA ID |
| `meeting_link` | 腾讯会议链接 |
| `groupAnnouncement` | 故障群公告对象（含 `item` HTML 内容） |
| `xray_id` | Xray 告警 ID |
| `feedback_effectiveness` | 反馈有效性：`valid`/`invalid` |
| `feedback_actual_scheme` | 实际处置方案 |
| `is_deleted` | `y`=已删除，`n`=正常 |
| `is_merged` | 是否被合并：1=已合并 |
| `source` | 来源，通常为 `xray` |

## MTTR 计算

MTTR = `finish_time` - `find_time`（分钟），如字段为 null 则无法计算。

## 分页信息

响应 `data` 中包含：`total`（总数）、`pageNum`、`pageSize`、`hasNextPage`、`pages`（总页数）。
