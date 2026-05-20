---
name: biz-diagnosis-creator
description: "对话式业务排障 Skill 创建器。当用户想要为自己的业务创建一个排障诊断 Skill 时使用。通过多轮对话引导用户描述异常场景、排查链路（SOP）和数据来源，自动匹配原子 Skill，生成可视化排查流程图供用户确认，最终输出标准格式的业务排障 Skill 文件。触发关键词：创建排障Skill、业务排障、孵化Skill、我想做一个排障、帮我创建诊断Skill。注意：本 Skill 是元 Skill，用于生成其他业务排障 Skill，不直接执行排障动作。"
---

# biz-diagnosis-creator

通过对话引导，将业务方的排障经验结构化为可复用的 Claude Skill。

## 核心原则

- **用户讲故事，Agent 建模型**：不让用户填表，而是通过自然对话提炼结构
- **零 PQL**：用户只选大盘/图表，系统自动获取 PQL 和 datasource
- **零 MCP 感知**：原子 Skill 由系统根据图表类型自动匹配，用户无需了解
- **可视化确认**：流程图生成后用户对话修改，直到满意再生成 Skill

## 工作流程

完整流程分 6 个阶段，见 [references/creator-workflow.md](references/creator-workflow.md)。

## Mock API（本地测试用）

大盘/图表搜索和原子 Skill 匹配，使用 `scripts/mock_xray_api.py`：

```bash
SCRIPT="scripts/mock_xray_api.py"

# 搜索大盘
python3 $SCRIPT dashboards --service {service} --keyword {关键词}

# 搜索图表
python3 $SCRIPT panels --dashboard_id {id} --keyword {关键词}

# 匹配原子 Skill
python3 $SCRIPT skills --match_panel {data_type} --use_case {场景描述}
```

详细参数见脚本内注释。生产环境替换为真实 X-Ray API 即可，入参/出参格式一致。

## 生成产物格式

见 [references/output-template.md](references/output-template.md)
