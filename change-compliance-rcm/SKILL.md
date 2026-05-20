---
name: change-compliance-rcm
description: 查询小红书 RCM 变更合规数据：各产品线汇总（complianceRate/riskFreeCoverage）、按操作人变更明细（operator）、变更不合规详情（nonCompliantChanges）、RiskFree 未覆盖详情（riskFreeCoverageGaps）。
---

# RCM 变更合规数据查询

## 脚本

在项目根目录执行：

```bash
python3 scripts/query_product_line_scores.py
python3 scripts/query_product_line_scores.py --from-time <ms> --to-time <ms>

python3 scripts/query_product_line_scores.py --fetch operator --operator <工作邮箱>
python3 scripts/query_product_line_scores.py --fetch operator --operator 从之

python3 scripts/query_product_line_scores.py --fetch non-compliant --product-line <编码>

python3 scripts/query_product_line_scores.py --fetch riskfree-gaps --product-line <编码>
```

- 未传 `--from-time` / `--to-time` 时默认「截至昨天结束的最近 7 天」，**自然日按东八区（UTC+8）** 计算；须成对传入或同时省略。
- `--fetch` 默认 `scores`；`operator` 须带 `--operator`（**工作邮箱或中文署名**；署名会先 `GET /api/users/bySignatureZh` 换邮箱再查明细）；`non-compliant` / `riskfree-gaps` 须带 `--product-line`。
- `--json`：输出完整 JSON；**operator / non-compliant / riskfree-gaps** 会将 `data[].startTime` 转为东八区 ISO（`...+08:00`）。**operator / non-compliant** 另会调用用户批量接口，为每条增加 `operatorDisplay`（`署名(真名)`，优先接口 `displayName`，否则 `sname(name)`），原字段 `operator` 仍为邮箱。
- 表格模式下「开始时间」为东八区墙钟；**operator / non-compliant** 的「操作人」列展示上述中文署名（与 `operatorDisplay` 一致）。
- `--base-url`、`--timeout` 见脚本 `--help`。

## 接口约定

- `GET /api/changeScore/productLine`：`fromTime`、`toTime`（毫秒）。`data[]`：`productLine`、`complianceRate`、`riskFreeCoverage`。
- `GET /api/changeScore/operator`：`operator`（操作人邮箱）、`fromTime`、`toTime`（毫秒）。`data[]`：如 `orderId`、`changeSystem`、`changeSystemCn`、`changeType`、`changeTypeCn`、`operator`、`resourceName`、`haProductLine`、`haProductLineCn`、`startTime`、`changeUrl`、`qualified`、`nonComplianceReason`。单条变更类型字段为 `data[i].changeType`（JSONPath 示例：`$.data[0].changeType`）。
- `GET /api/users/bySignatureZh`：查询参数 `signatureZh`（URL 编码的中文署名）。`data` 含 `workEmail`、`redMail`、`operator` 等；其中 **`operator` 可能为无 @ 的账号**，脚本按顺序取 **含 `@` 的 `workEmail` → `redMail` → `operator`** 作为 `changeScore/operator` 查询邮箱。
- `POST /api/users/batchGet`：请求体 `{"emails":["..."]}`；`data[]` 含 `email`、`name`、`displayName`、`sname` 等。脚本用其与 `--base-url` 同源 RCM 域名拉取展示名（邮箱较多时分批，每批至多 80 个）。
- `GET /api/changeScore/nonCompliantChanges`：`productLine`、`fromTime`、`toTime`。
- `GET /api/changeScore/riskFreeCoverageGaps`：`productLine`、`fromTime`、`toTime`。
- 成功：`code == 200`，`data` 为数组。
