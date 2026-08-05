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
    "你必须主动调用工具生成 SparkCard、TweetSeed、ConnectionInsight、ExplorationThread、ExplorationBoard、KnowledgeMap 和 EvidenceGap。",
    "用户印象、图片摘要、OCR 或未确认摘要不能直接当事实。",
    "外部搜索必须通过 search_evidence 工具。",
    `run_id: ${input.run_id}`,
    `autonomy_level: ${input.autonomy_level}`,
    "captures:",
    input.captures.map(formatCapture).join("\n\n---\n\n"),
  ].join("\n\n");
}

export const runPrompt = [
  "请执行慢想 V0b 黄金链路。",
  "先探索收藏，再生成至少 3 张灵感卡、3 条推文种子、1 个意外连接、2 条探索线程、探索面板、知识地图 v1、至少 1 个证据缺口。",
  "如果需要补事实证据，请调用 search_evidence。",
  "请优先使用工具完成结构化输出，不要只用自然语言回答。",
].join("\n");
