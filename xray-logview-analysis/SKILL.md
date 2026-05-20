---
name: xray-logview-analysis
description:
  "根据 CAT MessageId 分析 XRay Logview 调用链。用于以下场景：(1) 用户提供
  MessageId，需要分析请求调用链、耗时分布、性能瓶颈；(2) 定位某次请求的异常根因；(3)
  查看某次调用的下游依赖健康状态（SLA等级/强弱依赖）；(4)
  排查慢请求或失败请求。触发词包括：在上下文中包含messageId，分析 logview、分析
  messageId、查看调用链、分析这个请求、根因分析、性能瓶颈分析等。"
metadata:
  category: trace
  subcategory: logview
  platform: xray
  trigger: messageId
  input: [messageId, base_url]
  output: [call_chain, latency_distribution, exception_nodes, dependency_health]
  impl: python-script
---

# XRay Logview 分析

> `{SKILL_DIR}` 为本 skill 所在目录的绝对路径，执行脚本时必须使用绝对路径。

## 工作流程

1. 获取 `messageId` 和 `base_url`（xray-api 地址）
2. 调用 `scripts/analyze_logview.py` 获取并分析数据
3. 输出结构化分析报告，包含：基本信息、异常节点、失败 Transaction、耗时 TOP10、调用链树、性能瓶颈、下游依赖

## 输入格式识别（必须在分析前执行）

用户提供的 ID 可能是以下两种格式之一，**必须先判断格式，再决定后续行为**：

### CAT MessageId（本 skill 处理）

- 格式：`{服务名}-{ip十六进制}.{线程号}-{小时时间戳}-{序列号}`
- 特征：包含形如 `[0-9a-f]{8}\.[0-9]+-[0-9]+-[0-9]+`
  的片段（ip 为8位十六进制，后接点和线程号，再接两段纯数字）
- 示例：`checkoutcenter-service-defaultunit-0a25edef.62955-492924-345307`、`nvwa-service-default-0a72c586.0026606-492924-34329`
- **重要**：MessageId 必须严格使用用户提供的原始值，不得修改其中任何字符。服务名中的 `-default`
  等后缀是服务名的一部分，不要做任何拆分或重新拼接

### Trace ID（不属于本 skill，需转交）

- 格式：**16位或32位十六进制字符串**，仅包含 `0-9` 和 `a-f`（不区分大小写），无连字符、无点号
- 示例：`a1b2c3d4e5f6a7b8`、`a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6`
- 判断规则：`^[0-9a-fA-F]{16}$` 或 `^[0-9a-fA-F]{32}$`

### 识别后的处理规则

- 若输入匹配 **CAT MessageId** 格式 → 继续执行本 skill 的分析流程
- 若输入匹配 **Trace ID** 格式 → **立即停止**，告知用户："您提供的是 Trace
  ID，请使用 xray-single-trace-analysis skill 进行分析"，并停止后续步骤
- 若格式不明确 → 向用户说明两种格式区别，请用户确认后再继续

## 获取输入

向用户询问（如未提供）：

- **messageId**: CAT 消息 ID，格式为
  `{服务名}-{ip十六进制}.{线程号}-{小时时间戳}-{序列号}`（例：`checkoutcenter-service-defaultunit-0a25edef.62955-492924-345307`）。必须原样使用用户提供的完整 messageId，不得修改任何字符
- **base_url**: xray 平台地址（例：`https://xray-ai.devops.xiaohongshu.com`），未提供时使用默认值

## 执行分析

```bash
# 通过 API 获取并分析
python3 {SKILL_DIR}/scripts/analyze_logview.py <messageId> \
  --base-url <base_url>

# 直接分析用户粘贴的 JSON（保存为临时文件后执行）
python3 {SKILL_DIR}/scripts/analyze_logview.py --json /tmp/logview.json
```

## 报告解读指引

拿到输出后，重点关注并给出结论：

| 部分             | 关注点                                                      |
| ---------------- | ----------------------------------------------------------- |
| 数据状态 code    | 1003=数据缺失，1004=已归档，需告知用户                      |
| 异常节点         | 列出所有 Error/RuntimeException/Exception，说明所在调用位置 |
| 失败 Transaction | status 非 0/success 的节点，通常是根因所在                  |
| 耗时 TOP10       | 找出占总耗时比例最高的节点                                  |
| 性能瓶颈         | 单节点耗时 > 总耗时 30% 即为瓶颈，重点说明                  |
| 下游依赖         | 失败的强依赖（strongDependence=true）是服务不可用的高风险点 |

## 分析结论格式

报告输出后，用中文总结：

```
## 根因分析结论

**请求概况**: [服务名] 在 [时间] 发起请求，总耗时 [X]ms，状态 [成功/失败]

**异常/失败**: [有/无] — [具体描述]

**性能瓶颈**: [具体节点] 耗时 [X]ms，占 [Y]%

**根因判断**: [一句话结论]

**建议**: [针对性建议]
```

## 参考文档

- API 接口和数据结构详情：[references/logview-api.md](references/logview-api.md)
