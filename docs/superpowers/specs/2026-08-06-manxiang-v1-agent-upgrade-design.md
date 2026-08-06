# 慢想 Manxiang v1 Agent 升级详细设计方案

> 面向目标：把当前 V0b Demo 升级成一个适合投递 Agent 研发岗位、能被面试官追问也站得住的 v1 项目。
>
> 当前基线：Python 核心 + Pi Agent TypeScript 桥 + Function Calling 工具协议 + JSON/JSONL 存储 + SSE Demo + 55 个本地测试通过；真实 LLM 验收测试需要 `MANXIANG_LLM_PROVIDER` 和 `MANXIANG_LLM_MODEL` 环境变量。

## 1. v1 一句话目标

慢想 v1 要从“低脑力收藏 Demo”升级为“证据驱动的研究流程 Agent”：

```text
轻量收藏
  -> 主题发现
  -> 研究立项
  -> 按需解析来源
  -> RAG 召回证据块
  -> Agent 生成知识地图
  -> Reducer 强校验落库
  -> 用户确认补证据
  -> 地图版本化更新
  -> 自动化评测与回放
```

这句话里最重要的是“证据驱动”。也就是说，v1 不是让大模型更会写，而是让它在工具、状态、证据、评测的约束下可靠工作。

## 2. 岗位 JD 对齐

| JD 能力 | v1 对应设计 | 面试时怎么讲 |
|---|---|---|
| Planning | `Surprise -> Research -> Patch -> Review` 状态机 | Agent 不是自由聊天，而是在明确阶段内行动 |
| Memory | `SourceRepository` + `KnowledgeRepository` | 长期记忆交给仓储层，Agent 只读写受控上下文 |
| Tool Use | Pi Agent Function Calling + Python Reducer | LLM 只提交意图，业务状态由可信 Reducer 写入 |
| Multi-Agent | v1 暂不做多 Agent，只保留可扩展接口 | 先保证单 Agent 闭环可靠，避免过度设计 |
| RAG | SourceChunk + 向量索引 + rerank + citation | 证据块可追溯，不把用户印象当事实 |
| Eval | Mock 协议回归 + 真实 LLM Rubric | 非确定性隔离，用评测指导 Prompt 迭代 |
| 工程化 | SQLite、JSONL、Checkpoint、SSE、测试 | 可恢复、可回放、可观测，不是聊天套壳 |
| Demo 展示 | Workbench 前端 | 面试可现场演示完整链路 |

## 3. 推荐方案

### 方案 A：继续强化 V0b 原型

只补文档、补测试、修 Prompt。

优点是快；缺点是没有真正的向量检索、来源解析、版本化地图，和 JD 的 RAG/Vector DB 对齐不够。

### 方案 B：v1 面试增强版，推荐

保留现有 Python 核心和 Pi Agent 桥，新增 SQLite 仓储、SourceChunk、轻量向量检索、地图版本化和评测框架。

这是最适合你的路线：工作量可控，但能覆盖 Agent 岗位最看重的“架构、RAG、工具、评测、工程鲁棒性”。

### 方案 C：重构成 LangGraph/LlamaIndex 全家桶

看起来更贴 JD，但风险很高：你会花大量时间迁移框架，项目特色反而被淹没。

v1 不推荐。可以在面试里说：我了解这些框架，但本项目为了证明底层 Agent 工程能力，先手写状态机和工具协议，后续可适配 LangGraph。

## 4. v1 范围

### 必做

- SQLite 持久化业务快照，替代纯 JSON 快照。
- JSONL 保留追加事件日志，作为审计和 replay 来源。
- 新增 `SourceArtifact`、`SourceChunk`、`SourceRef`，实现来源可追溯。
- 新增本地向量检索接口，默认实现可用 Chroma 或 SQLite FTS + embedding 缓存。
- 新增 `ResearchRun` 状态机，明确 `surprise`、`research`、`patch`、`review` 阶段。
- 知识地图节点新增 `confidence` 和 `source_refs`。
- `KnowledgeMap` 支持版本递增和 diff。
- 外部搜索和重解析必须经过 `EvidenceGap`、`search_goal`、`stop_condition`。
- 增加自动化评测目录 `evals/manxiang/`。
- Workbench 展示事件流、证据引用、地图版本和补证据确认点。

### 不做

- 不做多用户权限。
- 不做复杂图编辑器。
- 不做生产级分布式队列。
- 不做自动发布内容。
- 不做模型微调。可以作为学习加分项，但不是 v1 主线。

## 5. 总体架构

```text
Workbench UI
  -> HTTP API / SSE
  -> RunService
  -> AgentRuntime(Pi Agent Bridge)
  -> ToolRegistry
  -> GuardrailPolicy
  -> Reducer
  -> Repository(SQLite + JSONL + Vector Index)
  -> Eval Runner
```

核心思想：

- API 层只接收请求，不直接相信 LLM。
- AgentRuntime 只负责让模型思考和调用工具。
- GuardrailPolicy 决定工具能不能执行。
- Reducer 负责把工具输出转成可信业务事件。
- Repository 负责保存快照、事件、证据块和索引。

这样做的好处是：大模型可以不稳定，但系统边界必须稳定。

## 6. 核心模块设计

### 6.1 Repository 抽象

当前 `JsonStore` 适合 Demo，但 v1 要拆成接口：

```text
CaptureRepository      保存收藏
SourceRepository       保存来源、解析产物、chunk、引用锚点
KnowledgeRepository    保存主题、任务、知识地图、证据、停车场
EventRepository        保存事件日志、checkpoint、replay 游标
VectorRepository       保存 embedding 和向量检索结果
```

新手理解：Repository 就是“数据出入口”。业务代码不应该关心数据到底在 JSON、SQLite、Chroma 还是云数据库里。

### 6.2 Source 证据模型

新增三个模型：

```python
SourceArtifact:
  id
  capture_id
  source_type
  uri
  content_hash
  parse_status
  parser_name
  parser_version

SourceChunk:
  id
  artifact_id
  text
  start_offset
  end_offset
  anchor
  embedding_status

SourceRef:
  artifact_id
  chunk_id
  quote
  anchor
```

为什么要这样拆：

- `CaptureItem` 是用户收藏的触发点。
- `SourceArtifact` 是被解析的来源。
- `SourceChunk` 是可检索、可引用的文本块。
- `SourceRef` 是知识地图节点的证据引用。

这样可以避免一句“伊莎贝拉和伊丽莎白有血缘关系”直接变成事实。

### 6.3 RAG 链路

v1 RAG 不追求复杂，追求可解释：

```text
EvidenceGap
  -> 生成检索 query
  -> 检索 SourceChunk
  -> rerank
  -> 过滤弱相关结果
  -> 交给 Agent 生成 Patch 建议
  -> Reducer 校验 source_refs
  -> 写入 EvidenceItem
```

检索策略：

- 第一阶段：关键词检索，保证可解释。
- 第二阶段：向量检索，召回语义相近内容。
- 第三阶段：rerank，按“是否回答当前 evidence gap”排序。
- 最终只给 Agent 3-5 个 chunk，控制 Token。

### 6.4 Agent 状态机

v1 状态建议：

```text
queued
exploring_surprise
scoping_research
drafting_map
waiting_user
patching_evidence
reviewing_map
completed
failed
aborted
```

状态机规则：

- `inbox_only` 不能搜索和重解析。
- 没有 `EvidenceGap` 不能搜索。
- 没有 `SourceRef` 不能把节点标成 `fact`。
- 用户未确认时，只能生成 `hypothesis` 或 `user_impression`。
- 每次地图更新都必须产生新版本。

### 6.5 Tool Contract

工具继续沿用现在的 Pi Agent submitTool 思路，但 v1 要强化 schema：

```text
record_collection_reading
create_research_contract
request_source_parse
retrieve_evidence_chunks
create_knowledge_map
mark_evidence_gap
request_web_search
attach_evidence
revise_knowledge_map
draft_expression_variants
```

关键原则：

- 工具参数必须包含真实 ID。
- 工具不能直接改数据库。
- Reducer 统一校验并落库。
- 未知工具一律拒绝。
- 缺少引用的事实节点一律降级或拒绝。

## 7. 数据流

### 7.1 收藏阶段

```text
POST /v1/captures
  -> CaptureProcessor
  -> CaptureRepository.save
  -> EventRepository.append(capture.created)
```

收藏阶段只轻量保存，不做全文解析。

### 7.2 研究阶段

```text
POST /v1/research-runs
  -> 创建 ResearchRun
  -> Agent 读 captures + summaries
  -> 生成 ResearchContract
  -> 生成 KnowledgeMap v1
```

v1 的 KnowledgeMap v1 只能是 `hypothesis`、`user_impression`、`needs_evidence`，不能直接是 `fact`。

### 7.3 补证据阶段

```text
用户确认 EvidenceGap
  -> request_source_parse
  -> retrieve_evidence_chunks
  -> attach_evidence
  -> KnowledgeMap v2
```

补证据阶段要能回答三个问题：

- 要补哪个缺口？
- 为什么这些 chunk 支撑它？
- 新地图比旧地图改变了什么？

## 8. API 设计

```text
POST /v1/captures
GET  /v1/captures

POST /v1/surprise-runs
POST /v1/research-runs
GET  /v1/runs/{run_id}
GET  /v1/runs/{run_id}/events

POST /v1/runs/{run_id}/confirmations
POST /v1/runs/{run_id}/source-parses
POST /v1/runs/{run_id}/evidence-patches

GET  /v1/tasks/{task_id}/maps
GET  /v1/tasks/{task_id}/maps/{version}
GET  /v1/tasks/{task_id}/maps/diff?from=1&to=2
```

SSE 事件最少包含：

```text
run.started
tool.started
tool.blocked
tool.completed
evidence.gap.detected
source.parse.started
source.chunk.created
map.created
map.updated
run.completed
run.failed
```

## 9. 质量与评测

v1 要有三层测试：

### 9.1 单元测试

测试 Reducer、Guardrail、Repository、RAG 检索、地图 diff。

目标：不依赖真实 LLM，跑得快，可重复。

### 9.2 协议回归测试

用 FakeBridge 固定工具调用序列，验证：

- 工具顺序正确。
- 缺引用会被拒绝。
- 未授权搜索会被拦截。
- 事件可以 replay。

### 9.3 真实 LLM 评测

用真实 fixture 运行 Agent，然后用 Rubric 打分：

```text
stage_compliance       阶段是否合规
source_grounding       是否引用真实来源
map_coherence          知识地图是否一致
evidence_precision     证据是否回答缺口
intervention_quality   跑偏干预是否合理
hallucination_penalty  是否编造事实
over_search_penalty    是否无边界搜索
```

真实 LLM 测试不要和普通 `pytest` 混在一起，建议命令：

```bash
uv run pytest -k 'not real_llm'
MANXIANG_LLM_PROVIDER=... MANXIANG_LLM_MODEL=... uv run pytest tests/test_v1_real_llm_eval.py
```

## 10. v1 验收标准

- 本地测试：普通测试全部通过。
- TypeScript：`npm run piagent:typecheck` 通过。
- Demo：Workbench 能展示一轮完整链路。
- RAG：至少一个 EvidenceGap 能召回真实 `SourceChunk`。
- 引用：地图中的 `fact` 节点必须有 `source_refs`。
- 版本：补证据后生成 KnowledgeMap v2，并能 diff v1/v2。
- 护栏：未确认搜索被拦截，并进入 `waiting_user`。
- 评测：至少 3 个真实 case 输出 rubric 分数。
- 面试演示：5 分钟内能讲清楚架构，10 分钟内能跑通 Demo。

## 11. 推荐实施里程碑

### M1：仓储和事件底座

- 抽象 Repository 接口。
- 实现 SQLiteStore。
- 保留 JSONL EventRepository。
- 加 checkpoint restore 和 replay 测试。

### M2：来源解析和 RAG

- 新增 SourceArtifact、SourceChunk、SourceRef。
- 实现文本/URL 的按需解析。
- 实现关键词检索 + embedding 接口。
- 接入 EvidenceGap 检索链路。

### M3：地图版本化

- KnowledgeMap 节点加 `confidence`、`source_refs`。
- 自动递增版本。
- 实现 v1/v2 diff。
- Reducer 拦截无证据 fact 节点。

### M4：Agent 工具升级

- 重构 Tool Contract。
- 加 `request_source_parse`、`retrieve_evidence_chunks`。
- Prompt 明确阶段规则和证据规则。
- FakeBridge + Real LLM 双验收。

### M5：Workbench 和评测

- 前端展示事件流、引用、地图版本。
- 新建 `evals/manxiang/`。
- 输出 rubric 报告。
- README 增加演示脚本。

## 12. 面试讲法

可以这样讲项目：

> 我做的是一个证据驱动的研究流程 Agent，不是普通聊天机器人。它先低成本接收用户收藏，等主题成熟后再启动研究状态机。Agent 通过 Function Calling 提交结构化工具参数，但不能直接改业务状态；所有输出都经过 Python Reducer 强校验，比如没有来源引用的事实节点会被拒绝或降级。RAG 部分采用按需解析，只有出现证据缺口才解析相关来源并召回 SourceChunk，避免一开始全量抓取导致 Token 爆炸。系统用 JSONL 事件日志和 checkpoint 做可回放，用 Mock 协议测试隔离 LLM 非确定性，再用真实 LLM + Rubrics 做质量评估。

这段话要背熟，但更重要的是你要能指到代码模块。

## 13. Grill-me 面试追问清单

你必须能回答这些问题：

1. 为什么不用 LangChain/LangGraph，而要自己写状态机？
2. `JsonStore` 为什么 v1 要升级到 SQLite？JSONL 又为什么还要保留？
3. 用户感想、AI 摘要、事实证据三者怎么区分？
4. 什么情况下知识地图节点可以从 `hypothesis` 升级为 `fact`？
5. 为什么收藏阶段不直接 OCR、抓网页、切 chunk？
6. RAG 召回结果弱相关时，你怎么防止 Agent 硬写进地图？
7. Reducer 和 Guardrail 的边界是什么？
8. 如果 LLM 按错工具顺序调用，你的系统怎么处理？
9. 真实 LLM 测试为什么不能替代 Mock 测试？
10. 如果 SSE 中断，前端怎么恢复事件？
11. 地图 v1 到 v2 的 diff 怎么算？
12. 你的 eval rubric 如何避免“看起来不错但其实胡说”？
13. 如果用户要求无限搜索，系统怎么限制预算？
14. 如果网页失效，SourceRef 怎么保持可追溯？
15. 这个项目和普通 RAG 问答有什么本质区别？

## 14. 高强度学习路线

### 第 1 周：读懂现有项目

- 画出 `capture -> run -> bridge -> reducer -> event -> workbench` 调用链。
- 手写解释 `before_tool_call` 和 `reduce_tool_result`。
- 跑通本地测试和 TypeScript typecheck。

### 第 2 周：补 Repository 和事件模型

- 学 SQLite 基础。
- 实现 Repository 接口。
- 理解 event sourcing：事件是历史，快照是当前状态。

### 第 3 周：补 RAG

- 学 chunk、embedding、rerank、citation。
- 实现 SourceChunk。
- 做一个 EvidenceGap 到 SourceRef 的闭环。

### 第 4 周：补 Agent 工具和 Prompt

- 学 Function Calling schema。
- 学 ReAct/Plan-and-Execute 的差异。
- 把工具调用顺序和状态机绑定。

### 第 5 周：补 Eval

- 学 golden case、rubric、非确定性隔离。
- 做 3 个真实 fixture。
- 输出评测报告。

### 第 6 周：准备简历和面试

- 把项目压缩成 3 分钟讲法。
- 准备 15 个 grill-me 问题答案。
- 准备 Demo 脚本和失败兜底方案。

## 15. v1 简历表达建议

当前简历描述可以升级成：

> 独立设计并实现证据驱动的研究流程 Agent，采用 `Surprise -> Research -> Patch -> Review` 状态机编排 Agent 行为；通过 Function Calling 暴露结构化工具，由 Python Reducer 对模型输出进行来源引用、状态迁移和事实置信度校验，避免无证据结论进入知识地图。设计延迟解析 RAG 架构，在收藏阶段仅保存用户印象和来源索引，在证据缺口触发后按需解析 SourceChunk 并召回引用片段，降低全量抓取带来的 Token 成本。系统使用 SQLite 快照、JSONL 事件日志和 Checkpoint 支持可恢复执行与 SSE 回放，并建立 Mock 协议回归 + 真实 LLM Rubric 评测体系，验证 Agent 工具调用、证据绑定和地图质量。

## 16. v1 最大风险

- 范围膨胀：不要同时做多用户、复杂图编辑、模型微调。
- RAG 做空：如果没有 SourceChunk 和 SourceRef，只写“RAG”会被面试官追问穿。
- 评测太虚：rubric 必须能扣分，不能只是“主观觉得好”。
- Demo 不稳：真实 LLM 环境变量、网络搜索、外部网页都要有降级方案。
- 代码和简历不一致：简历里写的每个词，都要能找到对应模块和测试。

## 17. 结论

v1 最应该做的是方案 B：在现有 V0b 上补齐“证据、检索、版本、评测、可恢复”五件事。

这条路线对 Agent 研发实习最有价值，因为它证明你不只是会调 Prompt，而是理解 Agent 系统的工程边界：模型负责生成候选动作，系统负责约束、验证、落库、回放和评测。
