import type { AgentTool, AgentToolResult } from "@earendil-works/pi-agent-core";
import { Type } from "typebox";

type Details = Record<string, unknown>;

function result(details: Details): AgentToolResult<Details> {
  return {
    content: [{ type: "text", text: JSON.stringify(details) }],
    details,
  };
}

function tool(name: string, label: string, description: string, parameters: ReturnType<typeof Type.Object>, details: Details): AgentTool {
  return {
    name,
    label,
    description,
    parameters,
    execute: async () => result(details),
  };
}

export const requiredToolNames = [
  "explore_captures",
  "mine_collection_surprises",
  "generate_spark_cards",
  "draft_tweet_seeds",
  "propose_exploration_threads",
  "synthesize_exploration_board",
  "generate_knowledge_map",
  "mark_evidence_gap",
  "search_evidence",
  "attach_evidence",
  "draft_expression_variants",
];

export function manxiangTools(): AgentTool[] {
  return [
    tool(
      "explore_captures",
      "Explore captures",
      "Extract themes, tensions, and questions from capture ids.",
      Type.Object({
        captureIds: Type.Array(Type.String()),
        includePending: Type.Boolean(),
        maxQuestions: Type.Number(),
      }),
      {
        themes: ["西班牙王室", "普拉多博物馆", "哥伦布", "王室译名"],
        tensions: ["用户印象不能直接当事实", "译名相似不等于血缘关系"],
        questions: [
          "伊莎贝拉和伊丽莎白是否有血缘关系？",
          "伊莎贝拉女王和哥伦布的具体关系是什么？",
          "费利佩和菲利普是什么语言或译名关系？",
        ],
      },
    ),
    tool(
      "mine_collection_surprises",
      "Mine collection surprises",
      "Find unexpected connections across captures.",
      Type.Object({ captureIds: Type.Array(Type.String()) }),
      {
        connection_insights: [
          {
            id: "insight_royal_columbus",
            relation_type: "cross_capture_connection",
            claim: "王室世系、普拉多绘画和哥伦布线索可以汇成一条西班牙王权叙事线。",
            explanation: "这些收藏都指向王权如何通过婚姻、赞助、艺术和航海扩张被看见。",
            source_capture_ids: ["cap_1", "cap_2", "cap_5", "cap_6"],
            confidence: "weak",
          },
        ],
      },
    ),
    tool(
      "generate_spark_cards",
      "Generate spark cards",
      "Create surprise cards grounded in capture ids.",
      Type.Object({ captureIds: Type.Array(Type.String()), count: Type.Number() }),
      {
        spark_cards: [
          {
            id: "spark_royal_tree",
            title: "一张王室世系图，把线索串起来了",
            angle: "从女王、译名和亲缘关系进入欧洲王室网络。",
            why_interesting: "它把看似零散的名字变成可追踪的关系问题。",
            source_capture_ids: ["cap_1", "cap_3", "cap_5"],
            surprise_score: 0.86,
            confidence: "weak",
            status: "draft",
          },
          {
            id: "spark_prado_power",
            title: "普拉多不是画库，也是一部王室八卦索引",
            angle: "用画作背后的委托、婚姻和继承故事解释王权。",
            why_interesting: "它让博物馆参观从看画变成读权力关系。",
            source_capture_ids: ["cap_2", "cap_5"],
            surprise_score: 0.8,
            confidence: "weak",
            status: "draft",
          },
          {
            id: "spark_columbus_isabella",
            title: "哥伦布线索让王室故事突然出海了",
            angle: "从伊莎贝拉女王赞助航海引出西班牙国家叙事。",
            why_interesting: "它把人物亲缘问题扩展成欧洲和美洲历史交汇点。",
            source_capture_ids: ["cap_4", "cap_6"],
            surprise_score: 0.83,
            confidence: "weak",
            status: "draft",
          },
        ],
      },
    ),
    tool(
      "draft_tweet_seeds",
      "Draft tweet seeds",
      "Draft short social writing seeds from spark cards.",
      Type.Object({ sparkCardIds: Type.Array(Type.String()), count: Type.Number() }),
      {
        tweet_seeds: [
          {
            id: "tweet_seed_1",
            spark_card_id: "spark_royal_tree",
            text: "欧洲王室的名字像一张线团：伊莎贝拉、伊丽莎白、费利佩、菲利普，看起来是翻译问题，往下挖却是婚姻、继承和权力网络。",
            style: "curious",
            source_capture_ids: ["cap_1", "cap_3", "cap_5"],
            publish_status: "draft",
          },
          {
            id: "tweet_seed_2",
            spark_card_id: "spark_prado_power",
            text: "普拉多博物馆里的很多画，不只是艺术史，也是西班牙王室把自己讲成历史主角的方式。",
            style: "plain",
            source_capture_ids: ["cap_2"],
            publish_status: "draft",
          },
          {
            id: "tweet_seed_3",
            spark_card_id: "spark_columbus_isabella",
            text: "伊莎贝拉女王和哥伦布这条线，把王室八卦突然接到了大航海时代。",
            style: "surprise",
            source_capture_ids: ["cap_6"],
            publish_status: "draft",
          },
        ],
      },
    ),
    tool(
      "propose_exploration_threads",
      "Propose exploration threads",
      "Offer research lines without treating notes as facts.",
      Type.Object({ maxThreads: Type.Number() }),
      {
        threads: [
          {
            id: "thread_genealogy",
            title: "欧洲王室亲缘和译名线",
            question: "这些相似名字背后到底是血缘、婚姻还是翻译？",
            source_capture_ids: ["cap_1", "cap_3", "cap_5"],
          },
          {
            id: "thread_isabella_columbus",
            title: "伊莎贝拉女王和哥伦布线",
            question: "伊莎贝拉赞助哥伦布这件事如何改变西班牙王权叙事？",
            source_capture_ids: ["cap_4", "cap_6"],
          },
        ],
        recommended_thread_id: "thread_isabella_columbus",
      },
    ),
    tool(
      "synthesize_exploration_board",
      "Synthesize exploration board",
      "Create a lightweight board for the recommended exploration thread.",
      Type.Object({ threadId: Type.String() }),
      {
        exploration_board: {
          id: "board_isabella_columbus",
          recommended_thread_id: "thread_isabella_columbus",
          columns: [
            { title: "已有线索", items: ["伊莎贝拉女王", "哥伦布", "西班牙王室"] },
            { title: "需要确认", items: ["具体赞助关系", "与普拉多画作的关联"] },
          ],
        },
      },
    ),
    tool(
      "generate_knowledge_map",
      "Generate knowledge map",
      "Create KnowledgeMap v1 using weak/medium confidence only.",
      Type.Object({ threadId: Type.String(), version: Type.Number() }),
      {
        map: {
          id: "map_isabella_columbus_v1",
          version: 1,
          nodes: [
            { id: "root", label: "伊莎贝拉女王和哥伦布为什么能串起这些收藏？", confidence: "weak" },
            { id: "node_royal_power", label: "王室赞助与权力叙事", confidence: "weak" },
            { id: "node_art", label: "普拉多画作作为王室故事入口", confidence: "weak" },
          ],
        },
      },
    ),
    tool(
      "mark_evidence_gap",
      "Mark evidence gap",
      "Mark gaps that need external evidence before becoming claims.",
      Type.Object({ mapId: Type.String() }),
      {
        gaps: [
          {
            id: "gap_isabella_columbus",
            description: "需要确认伊莎贝拉女王与哥伦布航行资助之间的可靠史料。",
            search_goal: "找到权威来源说明伊莎贝拉女王和哥伦布的关系。",
            stop_condition: "至少一个博物馆、百科或学术机构来源。",
          },
        ],
      },
    ),
    tool(
      "search_evidence",
      "Search evidence",
      "Request external evidence for one EvidenceGap. Python guardrail may block this tool.",
      Type.Object({
        gap_id: Type.String(),
        query: Type.String(),
        max_results: Type.Number(),
      }),
      {
        evidence: [
          {
            id: "ev_real_search_requested",
            gap_id: "gap_isabella_columbus",
            source_title: "Real search requested",
            source_uri: "about:real-search-adapter-required",
            summary: "Python side must replace this with real search adapter results after confirmation.",
            strength: "weak",
            status: "candidate",
          },
        ],
      },
    ),
    tool(
      "attach_evidence",
      "Attach evidence",
      "Attach confirmed evidence to a map node.",
      Type.Object({ evidenceId: Type.String(), mapId: Type.String() }),
      {
        evidence: {
          id: "ev_real_search_requested",
          source_type: "web",
          source_url: "about:real-search-adapter-required",
          title: "Real search requested",
          summary: "等待用户确认搜索后替换为真实证据。",
          supports_node_id: "node_royal_power",
          evidence_type: "candidate",
          strength: "weak",
          status: "weak_related",
        },
        map: {
          id: "map_isabella_columbus_v1",
          version: 1,
          nodes: [{ id: "node_royal_power", confidence: "weak" }],
        },
      },
    ),
    tool(
      "draft_expression_variants",
      "Draft expression variants",
      "Draft optional expression variants for the user.",
      Type.Object({ seedIds: Type.Array(Type.String()) }),
      {
        drafts: [
          {
            id: "draft_1",
            text: "我以为只是两个女王名字像，结果越看越像一张欧洲王室和大航海时代的关系网。",
            source_capture_ids: ["cap_1", "cap_5", "cap_6"],
          },
        ],
      },
    ),
  ];
}
