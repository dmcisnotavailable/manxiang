# 慢想 TodoList

> 这份清单只记录当前质询后确认缺失、且要把慢想从 MVP 原型推进到可靠研究 Agent 必须补齐的事项。

## P0：架构边界与知识库适配方向

- [ ] 明确长期方向：慢想是研究流程 Agent，不是通用数据库，也不是大而全知识库。
- [ ] 设计 `SourceRepository` 接口，负责来源元数据、抽取文本、引用锚点和内容哈希的读写。
- [ ] 设计 `KnowledgeRepository` 接口，负责主题、研究任务、知识地图、证据节点、停车场、草稿和复盘归档的读写。
- [ ] 设计 `EventRepository` 接口，负责事件日志、变更 diff、checkpoint 和 replay 数据的读写。
- [ ] 将当前 `JsonStore` 标记为 MVP 本地实现，后续作为 `Repository` 的一个适配器，而不是核心架构本身。
- [ ] 让 `ManxiangPipeline` 依赖仓储接口，而不是直接依赖具体 JSON 文件实现。
- [ ] 设计本地知识库方案：本地文件目录 + SQLite / JSON / 向量索引的组合边界。
- [ ] 设计云端知识库方案：云数据库、对象存储、向量检索、权限和同步策略。
- [ ] 设计第三方知识库适配方案：Notion、Obsidian、Logseq 或私有知识库 API。
- [ ] 明确 Agent 权限：Agent 可以读写知识库，但不能因为知识库里有新内容就自动无限扩展研究任务。
- [ ] 明确成功指标：不是存了多少资料，而是主题是否更清楚、证据是否更可追溯、用户是否更容易完成一轮研究。

## P0：来源读取与可追溯性

- [ ] 维护输入设计文档：`docs/manxiang-input-design.md`。
- [ ] 将输入阶段明确为轻量收藏：只保存来源、用户原话、候选摘要、用户确认摘要、轻标签和候选主题。
- [ ] 设计目录索引式收藏存储：一条收藏一个稳定目录，`index.json` 保存说明卡片，`captures.jsonl` 保存全局索引。
- [ ] 调整 `CaptureItem` 字段，区分 `ai_summary_draft`、`user_summary`、`summary_status` 和 `parse_status`。
- [ ] 明确所有重解析后置：链接不默认抓全文，图片不默认 OCR，视频不默认转写，文件不默认解析。
- [ ] 在研究任务阶段按需创建 `SourceArtifact` 和 `SourceChunk`，用于知识地图证据追溯。
- [ ] 知识地图中的证据节点必须能回链到 `SourceChunk`，不能只保存摘要。
- [ ] 证据补丁 `EvidenceItem` 要保存引用锚点，支持追溯到网页段落、文件页码、图片 OCR 区域或视频时间戳。
- [ ] 为来源读取增加失败状态：抓取失败、解析失败、OCR 失败、转写失败、来源不可访问。
- [ ] 为按需解析增加测试数据和 fixture，覆盖 URL、纯文本、PDF、图片 OCR 文本、视频转写文本。

## P0：变更历史、事件日志与 Checkpoint

- [ ] 将当前 `JsonStore` 的 upsert 存储扩展为“当前快照 + 追加事件日志”双层结构。
- [ ] 新增 `events.jsonl`，所有状态变化追加写入，不覆盖历史。
- [ ] 新增 `StateEvent` 数据模型。
  - `event_id`
  - `trace_id`
  - `entity_type`
  - `entity_id`
  - `event_type`
  - `before_hash`
  - `after_hash`
  - `payload_diff`
  - `actor`
  - `reason`
  - `created_at`
- [ ] 记录收藏项从 `captured` 到 `light_tagged`、`clustered`、`used_in_task` 等状态变更。
- [ ] 记录主题簇从 `fragment` 到 `gathering`、`ready`、`task_created` 等状态变更。
- [ ] 记录研究任务从 `scoping` 到 `line_chosen`、`map_drafted`、`evidence_patching` 等阶段变更。
- [ ] 记录用户主线覆盖行为，包括原主线、目标主线、风险提示、用户确认。
- [ ] 记录知识地图每次重建的版本号、输入来源、证据集合和变更 diff。
- [ ] 新增 `checkpoints.json`，保存关键阶段的可恢复快照。
- [ ] 新增 `Checkpoint` 数据模型。
  - `checkpoint_id`
  - `task_id`
  - `stage`
  - `map_version`
  - `captures_hash`
  - `topics_hash`
  - `evidence_hash`
  - `parking_hash`
  - `created_at`
  - `restore_pointer`
- [ ] 在收藏入库后自动创建轻量 checkpoint。
- [ ] 在主题发现后创建 checkpoint。
- [ ] 在创建研究契约后创建 checkpoint。
- [ ] 在主线确认后创建 checkpoint。
- [ ] 在知识地图初稿生成后创建 checkpoint。
- [ ] 在进入补证据阶段前创建 checkpoint。
- [ ] 在每次证据补丁写入后创建 checkpoint。
- [ ] 在用户确认知识地图后创建 checkpoint。
- [ ] 在写作升级前创建 checkpoint。
- [ ] 实现 checkpoint restore，支持回到某个研究任务的历史阶段。
- [ ] 实现 checkpoint diff，展示两个 checkpoint 之间新增、删除、修改了哪些主题、证据和地图节点。

## P0：Agent 评测系统

- [ ] 新建 `evals/manxiang/` 目录。
- [ ] 新建 `evals/manxiang/cases/`，保存固定评测输入。
- [ ] 新建 `evals/manxiang/rubrics/`，保存评分标准。
- [ ] 新建 `evals/manxiang/run_eval.py`，统一运行慢想评测。
- [ ] 新建 `evals/manxiang/reports/`，保存评测输出。
- [ ] 设计评测 case schema。
  - 收藏输入序列
  - 用户追问
  - 跑偏请求
  - 证据缺口
  - 期望阶段变化
  - 期望主线
  - 禁止行为
- [ ] 增加流程合规评测：收藏阶段不能深挖，补证据阶段必须有 `evidence_gap`、`search_goal`、`stop_condition`。
- [ ] 增加来源追溯评测：知识地图证据节点必须绑定 `SourceChunk`。
- [ ] 增加研究质量评测：核心问题、主线、概念、证据缺口和下一步动作是否一致。
- [ ] 增加跑偏干预评测：同一 detour 在 `strict_mentor`、`gentle_editor`、`research_buddy` 下应触发不同强度干预。
- [ ] 增加证据精度评测：搜索结果是否只服务当前证据缺口，不能扩展新主题。
- [ ] 增加 replay 回归评测：同一批收藏输入在版本升级后不能出现异常主题漂移。
- [ ] 增加幻觉惩罚项：没有来源的事实性结论必须扣分。
- [ ] 增加过度搜索惩罚项：无明确缺口、无停止条件或搜索结果弱相关时扣分。
- [ ] 输出评分字段。
  - `stage_compliance`
  - `source_grounding`
  - `map_coherence`
  - `intervention_quality`
  - `evidence_precision`
  - `user_agency`
  - `over_search_penalty`
  - `hallucination_penalty`
- [ ] 将评测命令接入 README 或开发文档。

## P1：产品化数据边界

- [ ] 明确哪些原始来源会本地保存，哪些只保存引用和抽取片段。
- [ ] 增加隐私/敏感信息处理策略，避免把私人文件、聊天记录、截图内容无提示地发送给外部模型。
- [ ] 为每个外部模型调用记录 `model`、`prompt_version`、`input_hash`、`output_hash`。
- [ ] 为每个 extractor 记录 `extractor_name` 和 `extractor_version`，保证后续结果可复现。
- [ ] 设计来源删除策略：删除收藏时是否删除 artifact、chunk、evidence、map 引用。
- [ ] 设计来源不可用策略：原网页失效后是否保留快照、摘要和引用锚点。

## P1：知识地图版本化

- [ ] 当前 `KnowledgeMap.version` 总是 1，需要改为同一 `task_id` 下自动递增。
- [ ] 每个地图版本保存生成输入：capture ids、source chunk ids、evidence ids、parking item ids。
- [ ] 地图节点新增 `source_refs` 字段，支持节点级引用。
- [ ] 地图节点新增 `confidence` 字段，区分事实、推测、用户感想和待核查内容。
- [ ] 地图版本之间支持 diff：新增节点、删除节点、合并节点、证据变化、停车场变化。
- [ ] 用户确认地图后锁定版本，后续补证据生成新版本。

## P1：停车场与跑偏管理闭环

- [ ] 当前 `InterventionPolicy` 只返回决策，需要接入 pipeline 并真正写入 `parking.json`。
- [ ] 停车场条目要记录来源、触发上下文、相关主线节点和建议未来产出。
- [ ] 同一分支被用户连续提起 2-3 次时，触发“新主题浮现”判断。
- [ ] 新主题浮现时提供三个选择：继续原主题、切换新主题、暂停当前任务。
- [ ] 记录用户选择，并写入事件日志。

## P2：写作升级能力

- [ ] 设计 `WritingEditor` 模块，把确认后的知识地图升级为报告骨架、短札记或主题报告。
- [ ] 写作升级必须遵守知识地图中的主线、证据和停车场约束。
- [ ] 写作输出要标注事实、推测、待核查和个人感想。
- [ ] 写作时不能把弱证据写成确定结论。
- [ ] 写作时不能擅自把停车场内容写入主线。
- [ ] 增加“去 AI 味”风格偏好沉淀，但不能覆盖用户原始表达。

## 当前已有能力，不重复建设

- [x] 轻量收藏处理：`CaptureProcessor`
- [x] 主题发现与成熟度评分：`TopicDiscoverer`
- [x] 研究任务创建与主线推荐：`TaskNavigator`
- [x] 知识地图文本视图 + 树状图：`KnowledgeMapBuilder`
- [x] 证据补丁阶段搜索约束：`EvidencePatcher`
- [x] 三种模式下的干预策略：`InterventionPolicy`
- [x] 本地 JSON MVP 存储：`JsonStore`
- [x] 慢想模块单元测试：`tests/test_manxiang_*.py`
