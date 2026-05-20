---
name: query_change
description: 查询小红书内部变更记录（发布、部署、配置变更等）。支持按时间范围、变更系统（ONES、Apollo、实验平台、Autobots）、服务名/应用名、变更人、环境等条件筛选变更事件。当用户提到查变更、查发布记录、查部署记录、谁发布了什么、最近有什么变更、某个服务的发布情况时使用。即使用户没有明说"变更"，只要涉及发布、部署、上线、配置变更、变更回溯等场景，也应使用此 Skill。
---

# Skill: 查询变更记录 (query_change)

## 能力说明

通过调用 Xray 变更平台 API，帮助用户查询小红书内部各类变更事件，包括服务发布、Apollo 配置变更、实验平台变更等。

**不支持**按业务线、组织架构、产品线维度查询，如遇此类需求请直接告知用户。

## API

### 变更查询接口

```
POST https://xray.devops.xiaohongshu.com/api/change/event_list
Content-Type: application/json
```

参数说明：

- `start` / `end`：必填，查询时间范围，格式 `YYYY-MM-DD HH:mm:ss`。用户未指定时默认查询最近 1 小时。
- `system_name`：非必填，变更系统名，例如：["switch", "racingweb"]。常见值：`ones`（服务发布）、`apollo`（服务配置变更）、`racingweb`（实验平台）、`switch`（客户端配置变更平台）、`autobots`。
- `env`：非必填，环境。生产为 `prod`，测试为 `staging`。用户未指定时默认 `["prod"]`。
- `event_type`：非必填，默认 `["human"]`（人工触发）；`system` 表示系统自动触发。
- `resource`：必填字段，但子字段非必填。ONES 发布按服务查传 `{"service": ["服务名"]}`，Apollo 按应用查传 `{"app": ["应用名"]}`，无具体资源时传 `{}`。
- `operator`：非必填，变更人的工作邮箱。用户提供的是署名时，需先调用署名查询接口获取邮箱。
- `content`：非必填，变更内容关键字搜索。
- `stage`：固定传 `"全量"`，不可修改。
- `tag` / `custom_tag`：固定传 `[]`。
- `page` / `page_size`：必填，默认 `1` / `20`。

返回值核心字段：`operator_name`（变更人）、`start`（变更时间）、`system_cn_name`（变更平台）、`event_cn_name`（变更类型）、`resource_name`（变更资源）、`env`（环境）、`link`（详情链接）、`total_pages` / `num_results`（分页信息）。

### 署名查询接口

当用户提供的变更人是署名（非邮箱）时，先调用此接口获取工作邮箱：

```
GET https://rcm.devops.xiaohongshu.com/api/users/bySignatureZh?signatureZh={署名URL编码}
```

> **重要**：`signatureZh` 参数值必须进行 URL 编码（Percent Encoding），例如"齐马"需编码为 `%E9%BD%90%E9%A9%AC`，直接传中文会导致查询失败。

返回值中 `data.workEmail` 即工作邮箱，用于变更查询的 `operator` 参数。
