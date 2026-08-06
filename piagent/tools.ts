import type { AgentTool, AgentToolResult } from "@earendil-works/pi-agent-core";
import { Type, type TSchema } from "typebox";

type Details = Record<string, unknown>;

function result(details: Details): AgentToolResult<Details> {
  return {
    content: [{ type: "text", text: JSON.stringify(details) }],
    details,
  };
}

function submitTool(name: string, label: string, description: string, parameters: TSchema): AgentTool {
  return {
    name,
    label,
    description,
    parameters,
    execute: async (_toolCallId, params) => result(params as Details),
  };
}

const sourceIds = Type.Array(Type.String(), {
  minItems: 1,
  description: "必须引用真实 capture id，不能编造。",
});

const evidenceGap = Type.Object({
  id: Type.String(),
  description: Type.String({ minLength: 12 }),
  search_query: Type.String({ minLength: 8 }),
  source_capture_ids: sourceIds,
});

export const requiredToolNames = [
  "record_collection_reading",
  "mine_collection_surprises",
  "create_spark_cards",
  "draft_tweet_seeds",
  "propose_exploration_threads",
  "synthesize_exploration_board",
  "create_knowledge_map",
  "mark_evidence_gap",
  "search_evidence",
  "attach_evidence",
  "draft_expression_variants",
];

export function manxiangTools(): AgentTool[] {
  return [
    submitTool(
      "record_collection_reading",
      "Record collection reading",
      "提交你对全部收藏的整体阅读。必须区分用户猜想、待验证事实和可用线索。",
      Type.Object({
        reading: Type.Object({
          user_intent: Type.String({ minLength: 12 }),
          promising_question: Type.String({ minLength: 12 }),
          shallow_interpretations_to_avoid: Type.Array(Type.String({ minLength: 8 }), { minItems: 2 }),
          hypotheses: Type.Array(
            Type.Object({
              claim: Type.String({ minLength: 12 }),
              status: Type.Union([Type.Literal("user_hunch"), Type.Literal("needs_evidence"), Type.Literal("usable_lead")]),
              source_capture_ids: sourceIds,
            }),
            { minItems: 3 },
          ),
        }),
      }),
    ),
    submitTool(
      "mine_collection_surprises",
      "Mine collection surprises",
      "提交跨收藏的意外连接。不要泛泛说“王室、艺术史、哥伦布能串起来”，要说清楚为什么这个连接不明显。",
      Type.Object({
        connection_insights: Type.Array(
          Type.Object({
            id: Type.String(),
            relation_type: Type.String(),
            claim: Type.String({ minLength: 18 }),
            explanation: Type.String({ minLength: 30 }),
            source_capture_ids: sourceIds,
            confidence: Type.Union([Type.Literal("weak"), Type.Literal("medium"), Type.Literal("strong")]),
          }),
          { minItems: 1 },
        ),
      }),
    ),
    submitTool(
      "create_spark_cards",
      "Create spark cards",
      "提交能让用户感到“原来还能这样看”的灵感卡。每张卡必须绑定真实 capture。",
      Type.Object({
        spark_cards: Type.Array(
          Type.Object({
            id: Type.String(),
            title: Type.String({ minLength: 8 }),
            angle: Type.String({ minLength: 18 }),
            why_interesting: Type.String({ minLength: 24 }),
            source_capture_ids: sourceIds,
            surprise_score: Type.Number(),
            confidence: Type.Union([Type.Literal("weak"), Type.Literal("medium"), Type.Literal("strong")]),
            status: Type.String(),
          }),
          { minItems: 3 },
        ),
      }),
    ),
    submitTool(
      "draft_tweet_seeds",
      "Draft tweet seeds",
      "提交短表达种子。不能直接下事实结论，要保留探索感。",
      Type.Object({
        tweet_seeds: Type.Array(
          Type.Object({
            id: Type.String(),
            spark_card_id: Type.String(),
            text: Type.String({ minLength: 20 }),
            style: Type.String(),
            source_capture_ids: sourceIds,
            publish_status: Type.String(),
          }),
          { minItems: 3 },
        ),
      }),
    ),
    submitTool(
      "propose_exploration_threads",
      "Propose exploration threads",
      "提交 2-3 条探索主线，并说明推荐哪条先走。",
      Type.Object({
        threads: Type.Array(
          Type.Object({
            id: Type.String(),
            title: Type.String({ minLength: 6 }),
            question: Type.String({ minLength: 12 }),
            reason: Type.String({ minLength: 16 }),
            source_capture_ids: sourceIds,
          }),
          { minItems: 2 },
        ),
        recommended_thread_id: Type.String(),
      }),
    ),
    submitTool(
      "synthesize_exploration_board",
      "Synthesize exploration board",
      "提交探索面板，用来解释当前主线有哪些线索、假设和风险。",
      Type.Object({
        exploration_board: Type.Object({
          id: Type.String(),
          recommended_thread_id: Type.String(),
          columns: Type.Array(
            Type.Object({
              title: Type.String(),
              items: Type.Array(Type.String({ minLength: 6 }), { minItems: 1 }),
            }),
            { minItems: 3 },
          ),
        }),
      }),
    ),
    submitTool(
      "create_knowledge_map",
      "Create knowledge map",
      "提交最终知识图。禁止模板话术；必须体现你基于收藏做出的非显而易见分析。",
      Type.Object({
        map: Type.Object({
          id: Type.String(),
          version: Type.Literal(1),
          title: Type.String({ minLength: 8 }),
          core_question: Type.String({ minLength: 20 }),
          thesis: Type.String({ minLength: 30 }),
          mainline: Type.Array(Type.String({ minLength: 18 }), { minItems: 3 }),
          non_obvious_insights: Type.Array(
            Type.Object({
              claim: Type.String({ minLength: 18 }),
              why_interesting: Type.String({ minLength: 24 }),
              source_capture_ids: sourceIds,
            }),
            { minItems: 3 },
          ),
          known_unknowns: Type.Array(Type.String({ minLength: 8 }), { minItems: 2 }),
          evidence_gaps: Type.Array(evidenceGap, { minItems: 2 }),
        }),
      }),
    ),
    submitTool(
      "mark_evidence_gap",
      "Mark evidence gap",
      "提交需要补证据的缺口。每个缺口必须有可直接搜索的 query。",
      Type.Object({
        gaps: Type.Array(evidenceGap, { minItems: 1 }),
      }),
    ),
    submitTool(
      "search_evidence",
      "Search evidence",
      "请求外部搜索。Python 护栏会在未确认时阻止该工具。",
      Type.Object({
        gap_id: Type.String(),
        query: Type.String({ minLength: 8 }),
        max_results: Type.Number(),
      }),
    ),
    submitTool(
      "attach_evidence",
      "Attach evidence",
      "提交要附加到地图上的候选证据。没有真实搜索前只能标 weak_related。",
      Type.Object({
        evidence: Type.Object({
          id: Type.String(),
          source_type: Type.String(),
          source_url: Type.String(),
          title: Type.String(),
          summary: Type.String({ minLength: 12 }),
          supports_node_id: Type.String(),
          evidence_type: Type.String(),
          strength: Type.Union([Type.Literal("weak"), Type.Literal("medium"), Type.Literal("strong")]),
          status: Type.String(),
        }),
        map: Type.Object({
          id: Type.String(),
          version: Type.Literal(1),
          nodes: Type.Array(Type.Object({ id: Type.String(), confidence: Type.String() })),
        }),
      }),
    ),
    submitTool(
      "draft_expression_variants",
      "Draft expression variants",
      "提交可选表达草稿，帮助用户把探索结果变成可发内容。",
      Type.Object({
        drafts: Type.Array(
          Type.Object({
            id: Type.String(),
            text: Type.String({ minLength: 20 }),
            source_capture_ids: sourceIds,
          }),
          { minItems: 1 },
        ),
      }),
    ),
  ];
}
