import type { BridgeCapture, BridgeRunInput } from "./types.js";

function formatCapture(capture: BridgeCapture): string {
  return [
    `id: ${capture.id}`,
    `source_type: ${capture.source_type}`,
    `source_uri: ${capture.source_uri ?? ""}`,
    `original_text: ${capture.original_text ?? ""}`,
    `user_note: ${capture.user_note ?? ""}`,
    `ai_summary_draft: ${capture.ai_summary_draft ?? ""}`,
    `summary_status: ${capture.summary_status ?? ""}`,
    `parse_status: ${capture.parse_status ?? ""}`,
    `candidate_topics: ${capture.candidate_topics.join(", ")}`,
  ].join("\n");
}

export function systemPrompt(input: BridgeRunInput): string {
  return [
    "你是慢想 Manxiang V0b 的探索 Agent。",
    "用户没有给研究题目，只丢了收藏并请求惊喜。",
    "工具只负责记录你提交的结构化参数，不会替你生成内容；所有洞察、主线、知识图都必须由你分析后填入工具参数。",
    "你必须主动调用工具生成 CollectionReading、SparkCard、TweetSeed、ConnectionInsight、ExplorationThread、ExplorationBoard、KnowledgeMap 和 EvidenceGap。",
    "用户印象、图片摘要、OCR 或未确认摘要不能直接当事实。",
    "禁止输出模板话术，例如“我已知道什么 -> 我还不懂什么 -> 哪个问题最关键 -> 下一步验证什么”或“核心问题还不清楚”。",
    "你的价值是提出用户自己不容易想到的连接：比如译名误读、王朝联姻、王权合法性、普拉多图像证据、伊莎贝拉与哥伦布如何把家族问题转成帝国叙事。",
    "外部搜索必须通过 search_evidence 工具。",
    `run_id: ${input.run_id}`,
    `autonomy_level: ${input.autonomy_level}`,
    "captures:",
    input.captures.map(formatCapture).join("\n\n---\n\n"),
  ].join("\n\n");
}

export const runPrompt = [
  "请执行慢想 V0b 黄金链路。",
  "先提交 record_collection_reading，再生成至少 3 张灵感卡、3 条推文种子、1 个意外连接、2 条探索线程、探索面板、知识地图 v1、至少 2 个证据缺口。",
  "create_knowledge_map 的 map 必须包含：title、core_question、thesis、3 条 mainline、至少 3 个 non_obvious_insights、至少 2 个 known_unknowns、至少 2 个带 search_query 的 evidence_gaps。",
  "如果需要补事实证据，请调用 search_evidence。",
  "请优先使用工具完成结构化输出，不要只用自然语言回答。",
].join("\n");
