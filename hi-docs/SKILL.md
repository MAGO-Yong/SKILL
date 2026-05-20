---
name: redoc
version: 1.0.0
description: hi 官方 REDoc 文档 Skill。当用户需要创建或编辑文档、修改文档内容、查看或回复文档评论、添加划词评论等文档操作时，必须使用此 skill。适用于通过 markdown 进行全文编辑、块级操作、查找替换、评论互动、文档历史版本恢复、创建文档副本、批量移动、查询文档目录树、文档版本对比
metadata: { 'openclaw': { 'requires': { 'bins': ["node", "hi"] } } }
---

技能核心能力通过 CLI 提供，在执行 CLI 命令时，必须查看运行命令的参数，**禁止**猜测命令用法：

```bash
# 查看具体命令的参数、示例和输出格式
hi docs --help
```

# 环境准备

若执行 `hi` 命令时提示 `command not found`，通过以下任一方式全局安装：

```bash
# 方式一：npm
npm install -g @xhs/hi-cli --registry=http://npm.devops.xiaohongshu.com:7001

# 方式二：bun
bun install -g @xhs/hi-cli --registry=http://npm.devops.xiaohongshu.com:7001
```

# 文档 shortcutId

Hi 文档的 shortcutId 是文档的唯一标识符。

# 文档 spaceId

Hi 文档的 spaceId 是文档空间的唯一标识符。

# Markdown 语法

**对文档进行创建或编辑前，必须先执行以下命令查看 REDoc Markdown 语法规范：**

```bash
hi docs:markdown-syntax
```

当用户描述中涉及以下任意内容时，同样必须先查看语法规范，再执行操作：

- 高亮块（highlight）
- 分栏（columns）
- @提及 / 艾特用户（mention）：需要获取被提及用户的邮箱等信息时，可通过 hi-search 查询
- 评论（comment）

**内容中含有 `<`、`>`、`{`、`}`、`|` 等特殊符号时，必须按 REDoc 转义规则处理，否则会导致解析报错或渲染异常。**

# 最佳实践

## 编辑模式选择

| 场景 | 推荐模式 | 理由 |
|------|---------|------|
| 修改一段已有文字 | `--ops edit` | 精准，只动目标 block |
| 在某个位置后插入新内容 | `--ops insert_after` | 精准定位，不影响其他 block |
| 删除若干 block | `--ops remove` | 批量删，一次到位 |
| 同时修改 + 删除 + 插入（复杂排版） | `--ops`（多条组合） | 一次提交，原子性更强 |
| 整节内容乱了 / 顺序全错 | `--content` 全量替换 | 比一堆 ops 可控，不会插错位置 |
| 修改已有文字（简单） | `--target + --replace` | 无需 blockId，适合简单文字替换 |
| 表格 / 代码块内容修改 | 禁止使用 `--target + --replace` | 对富文本节点无效，必定失败 |

## 全量替换注意事项

全量替换时，文档标题由 content 中**第一个 `#` 标题行**决定。若 content 不以 `# 标题` 开头，文档标题会被**清空**。

## op 注意事项

以多条 `insert_after` 为例：指向同一个 anchor `blockId` 时，后写的先插入，最终顺序与写法顺序**相反**。

想要最终文档顺序为 `anchor → A → B → C`，ops 数组须**倒序**书写：

```json
[
  {"op": "insert_after", "blockId": "anchor", "content": "C"},
  {"op": "insert_after", "blockId": "anchor", "content": "B"},
  {"op": "insert_after", "blockId": "anchor", "content": "A"}
]
```

## 创建文档命令说明

创建命令支持同时传入 `--title`（文档标题）和 `--content`（文档正文 Markdown）两个独立参数：

- `--title` 设置的是文档的**标题**
- `--content` 设置的是文档的**正文**，不需要在正文里重复写标题
- 两者相互独立，**不要**在 `--content` 中再次重复 `--title` 的内容

## 流程交互规则

### 1. 编辑文档前必须征得用户授权

当用户请求对某个 `shortcutId` 文档执行**任何编辑类操作**（包括但不限于全文修改、块级编辑、查找替换、版本恢复、内容追加等会改变文档内容的命令）时，**必须先向用户明确确认是否允许编辑该文档**，得到用户明确同意后才能执行编辑命令。

- 询问内容需包含目标文档的 `shortcutId`（如能获取到标题，也一并展示），让用户明确知道将要被修改的是哪一篇文档
- 用户未明确同意前，禁止调用任何编辑类 CLI 命令

### 2. 创建文档前必须确认创建位置

当用户请求创建新的 REDoc 文档时，**必须主动反问用户文档要创建在什么位置**。

- 需要向用户确认的内容至少包括：目标 `spaceId`（文档空间）以及可选的父文档 `shortcutId`（如需创建在某文档下作为子文档）
- 若用户提供的信息不足以唯一确定位置（例如只说了空间名而未给 `spaceId`），可结合 hi-search, hi-docs 等能力辅助查询候选项，并由用户最终确认
- "默认位置"即是空间的根目录
