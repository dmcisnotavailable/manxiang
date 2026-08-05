# 慢想输入设计

> 本文只讨论慢想的输入、收藏和来源解析边界。TodoList 只记录任务，不承载详细设计。

## 1. 核心判断

慢想收藏的不是材料本体，而是：

```text
一个来源 + 用户对这个来源的当下印象
```

因此，收藏阶段不做重解析，不把链接、图片、视频和文件全部展开存成长期内容。慢想要避免变成“大而全资料库”，它更像一个研究流程 Agent：先帮用户保留触发点，等用户真的选择某个主题进入研究任务时，再对相关来源做具体解析。

## 2. 输入阶段原则

### 2.1 先轻后重

收藏阶段只保存轻量信息：

- 来源类型。
- 来源地址或本地路径。
- 用户原始感想。
- AI 候选摘要。
- 用户确认摘要。
- 轻标签。
- 候选主题。
- 解析状态。

研究阶段才生成重内容：

- 网页正文抽取。
- PDF / 文档解析。
- 图片 OCR 或视觉解析。
- 视频转写。
- 可引用片段 `SourceChunk`。
- 证据节点 `EvidenceItem`。
- 引用锚点。

### 2.2 摘要优先表达用户印象

慢想里的摘要不是普通的“原文讲了什么”，而是“用户为什么收藏它”。

应该优先回答：

- 这条来源触发了用户什么问题？
- 用户被什么观点、表达、情绪或矛盾点吸引？
- 它可能属于哪个长期主题？
- 它对后续研究有什么线索价值？

因此建议命名为 `impression_summary` 或在模型里区分：

```text
ai_summary_draft: AI 猜测的用户印象
user_summary: 用户确认后的印象摘要
```

### 2.3 用户确认是质量闸门

AI 可以先生成候选摘要，但候选摘要不应直接等同于用户真实意图。

摘要状态建议分为：

```text
summary_pending: AI 已生成候选摘要，但用户还没确认
summary_confirmed: 用户确认或修改过摘要
summary_rejected: 用户认为摘要理解错了
```

主题发现可以临时参考 `summary_pending` 的内容，但权重要低；正式升级研究任务时，应优先依赖 `summary_confirmed` 的收藏。

### 2.4 所有重解析都延迟

统一规则：

```text
链接：不默认抓全文
图片：不默认 OCR
视频：不默认转写
文件：不默认解析
网页：不默认保存正文快照
文本：用户直接输入的文本可以原样保存
```

用户直接输入文本是例外，因为它本身就是输入内容，不需要额外解析。

## 3. 推荐存储形态

### 3.1 目录索引为主

采用“目录给人看，索引给机器读”的方式。

```text
manxiang_library/
  captures/
    2026/
      08/
        cap_xxx/
          index.json
          original.txt
          attachments/
  indexes/
    captures.jsonl
    topics.jsonl
```

说明：

- 一条收藏对应一个稳定目录。
- `index.json` 是这条收藏的说明卡片。
- `captures.jsonl` 是全局总目录，方便快速列表、筛选和迁移。
- 主题不要通过真实目录搬动文件，主题应该是索引关系，因为主题会变化，收藏时间和 ID 不会变化。

### 3.2 收藏目录内容

不同输入类型的目录内容可以不同。

文本输入：

```text
cap_xxx/
  index.json
  original.txt
```

链接输入：

```text
cap_xxx/
  index.json
```

图片输入：

```text
cap_xxx/
  index.json
  attachments/
    original.png    # 可选，取决于隐私和空间策略
```

视频输入：

```text
cap_xxx/
  index.json
```

文件输入：

```text
cap_xxx/
  index.json
  attachments/
    original.pdf    # 可选，也可以只存外部路径
```

### 3.3 `index.json` 建议字段

```json
{
  "capture_id": "cap_xxx",
  "source_type": "url",
  "source_uri": "https://example.com/article",
  "source_title": "可选标题",
  "source_saved_policy": "reference_only",
  "original_text_path": null,
  "user_note": "用户原始感想",
  "ai_summary_draft": "AI 候选摘要",
  "user_summary": "用户确认摘要",
  "summary_status": "summary_confirmed",
  "tags": ["AI 陪伴", "真实感"],
  "candidate_topics": ["AI 陪伴与亲密关系"],
  "parse_status": "not_parsed",
  "created_at": "2026-08-04T20:00:00+08:00",
  "updated_at": "2026-08-04T20:00:00+08:00"
}
```

`source_saved_policy` 建议取值：

```text
reference_only: 只保存来源引用
copy_saved: 保存了本地副本
text_inline: 用户文本已保存为 original.txt
external_managed: 原始材料由外部知识库或文件系统管理
```

`parse_status` 建议取值：

```text
not_parsed: 尚未解析
parse_requested: 已进入研究任务，等待解析
parsed: 已解析
parse_failed: 解析失败
parse_skipped: 用户选择不解析
```

## 4. 输入类型策略

### 4.1 链接

收藏阶段保存：

- 原始 URL。
- 可选标题。
- 用户原始感想。
- 候选摘要。
- 用户确认摘要。

不默认保存：

- 网页正文。
- 网页快照。
- 全文 chunk。

研究阶段需要引用时，再执行网页抓取、正文抽取和 chunk 生成。

### 4.2 文本

文本是用户直接提供的内容，可以直接保存 `original.txt`。

但主题发现仍然优先使用：

```text
user_summary > user_note > ai_summary_draft > original_text
```

这样可以避免一段很长的粘贴文本覆盖用户真正想研究的点。

### 4.3 图片

收藏阶段保存：

- 图片来源或本地路径。
- 用户原始感想。
- 候选摘要。
- 用户确认摘要。

不默认 OCR，不默认视觉解析。

如果用户明确要用这张图进入知识地图或证据补丁阶段，再执行 OCR / 视觉解析，并把结果转成 `SourceChunk`。

### 4.4 视频

收藏阶段保存：

- 视频地址。
- 可选标题。
- 用户原始感想。
- 候选摘要。
- 用户确认摘要。

不默认下载，不默认转写。

研究阶段需要使用视频内容时，再转写，并保留时间戳引用锚点。

### 4.5 文件

收藏阶段保存：

- 文件路径或附件副本。
- 文件类型。
- 用户原始感想。
- 候选摘要。
- 用户确认摘要。

不默认解析 PDF、DOCX、Markdown 等文件。研究阶段按需解析。

## 5. 阶段关系

### 5.1 收藏阶段

目标：低成本收下触发点。

输入：

```text
source_type + source_uri / original_text + user_note
```

输出：

```text
CaptureItem
```

此阶段不产生 `SourceArtifact` 和 `SourceChunk`。

### 5.2 摘要确认阶段

目标：让用户确认“这条收藏到底代表什么印象”。

流程：

```text
用户输入来源
  ↓
AI 生成候选摘要
  ↓
用户确认 / 修改 / 拒绝
  ↓
写入 user_summary 和 summary_status
```

### 5.3 主题发现阶段

目标：根据确认过的收藏印象发现重复兴趣。

推荐优先级：

```text
user_summary > user_note > ai_summary_draft > original_text
```

`summary_pending` 可以参与弱聚类，但不应直接触发正式研究任务。

### 5.4 研究任务阶段

目标：围绕用户选定主题解析一批来源。

此时才创建：

```text
SourceArtifact
SourceChunk
EvidenceItem
```

这些对象是研究任务内的派生物，不应该反过来污染原始收藏。

## 6. 与现有模型的关系

当前 `CaptureItem` 已经有：

```text
source
user_note
raw_text
summary
tags
candidate_topics
status
```

后续建议逐步演进为：

```text
source_type
source_uri
source_title
source_saved_policy
original_text_path
user_note
ai_summary_draft
user_summary
summary_status
parse_status
tags
candidate_topics
```

可以先兼容旧字段：

- `source` 过渡为 `source_uri`。
- `raw_text` 过渡为 `original_text_path` 或文本内容存储。
- `summary` 过渡为 `user_summary`，如果用户未确认，则存 `ai_summary_draft`。

## 7. 与 TodoList 的边界

TodoList 只记录要做什么，例如：

- 新增输入设计文档。
- 调整 `CaptureItem` 模型。
- 实现目录索引存储。
- 增加摘要确认状态。
- 将来源解析后置到研究任务阶段。

本文记录为什么这样做、字段怎么设计、不同来源怎么处理。

## 8. 当前决策

- 采用目录索引为主的收藏存储方式。
- 收藏阶段保存来源和摘要，不承担重存储。
- 摘要强调用户印象，不强调原文完整内容。
- 摘要需要用户确认。
- 链接、图片、视频、文件都不默认重解析。
- 图片不默认 OCR，详细解析留到真正生成知识地图或补证据时。
- 文本输入可以保存原始文本。
- `SourceArtifact` / `SourceChunk` 是研究阶段产物，不是收藏阶段产物。
