from manxiang.guardrails import before_tool_call
from manxiang.schema import AgentRun


def run(autonomy_level: str = "inbox_only") -> AgentRun:
    return AgentRun(
        id="run_1",
        input_capture_ids=["cap_1"],
        created_at="2026-08-06T10:00:00+08:00",
        updated_at="2026-08-06T10:00:00+08:00",
        autonomy_level=autonomy_level,
    )


def test_blocks_source_parse_in_inbox_only():
    decision = before_tool_call(run("inbox_only"), "request_source_parse", {"capture_id": "cap_1"})

    assert decision == {"block": True, "reason": "request_source_parse requires source_parse_allowed"}


def test_allows_source_parse_after_permission():
    assert before_tool_call(run("source_parse_allowed"), "request_source_parse", {"capture_id": "cap_1"}) is None


def test_allows_source_parse_with_web_search_permission():
    assert before_tool_call(run("web_search_allowed"), "request_source_parse", {"capture_id": "cap_1"}) is None


def test_blocks_web_search_without_search_goal():
    decision = before_tool_call(
        run("web_search_allowed"),
        "request_web_search",
        {"gap_id": "gap_1", "stop_condition": "找到两个可靠来源"},
    )

    assert decision == {"block": True, "reason": "request_web_search requires search_goal"}


def test_blocks_retrieval_without_gap_id():
    decision = before_tool_call(
        run("source_parse_allowed"),
        "retrieve_evidence_chunks",
        {"query": "伊莎贝拉 哥伦布"},
    )

    assert decision == {"block": True, "reason": "retrieve_evidence_chunks requires gap_id"}


def test_blocks_retrieval_with_blank_query():
    decision = before_tool_call(
        run("source_parse_allowed"),
        "retrieve_evidence_chunks",
        {"gap_id": "gap_1", "query": "   "},
    )

    assert decision == {"block": True, "reason": "retrieve_evidence_chunks requires query"}


def test_blocks_retrieval_with_non_string_query():
    decision = before_tool_call(
        run("source_parse_allowed"),
        "retrieve_evidence_chunks",
        {"gap_id": "gap_1", "query": 123},
    )

    assert decision == {"block": True, "reason": "retrieve_evidence_chunks requires query"}


def test_blocks_fact_upgrade_without_source_refs():
    decision = before_tool_call(
        run("source_parse_allowed"),
        "revise_knowledge_map",
        {"nodes": [{"id": "node_1", "confidence": "fact", "source_refs": []}]},
    )

    assert decision == {"block": True, "reason": "fact nodes require source_refs"}


def test_blocks_malformed_nodes_that_are_not_a_list():
    decision = before_tool_call(
        run("source_parse_allowed"),
        "revise_knowledge_map",
        {"nodes": {"id": "node_1", "confidence": "fact", "source_refs": []}},
    )

    assert decision == {"block": True, "reason": "map nodes must be a list"}


def test_blocks_map_nodes_that_are_not_objects():
    decision = before_tool_call(
        run("source_parse_allowed"),
        "revise_knowledge_map",
        {"nodes": ["node_1"]},
    )

    assert decision == {"block": True, "reason": "map nodes must be objects"}


def test_blocks_fact_upgrade_when_map_nodes_follow_empty_top_level_nodes():
    decision = before_tool_call(
        run("source_parse_allowed"),
        "revise_knowledge_map",
        {
            "nodes": [],
            "map": {"nodes": [{"id": "node_1", "confidence": "fact", "source_refs": []}]},
        },
    )

    assert decision == {"block": True, "reason": "fact nodes require source_refs"}


def test_blocks_fact_upgrade_inside_map_without_source_refs():
    decision = before_tool_call(
        run("source_parse_allowed"),
        "revise_knowledge_map",
        {"map": {"nodes": [{"id": "node_1", "confidence": "fact", "source_refs": []}]}},
    )

    assert decision == {"block": True, "reason": "fact nodes require source_refs"}


def test_allows_fact_upgrade_inside_map_with_source_refs():
    decision = before_tool_call(
        run("source_parse_allowed"),
        "revise_knowledge_map",
        {"map": {"nodes": [{"id": "node_1", "confidence": "fact", "source_refs": ["src_1"]}]}},
    )

    assert decision is None


def test_allows_create_knowledge_map_without_nodes_payload():
    decision = before_tool_call(
        run("source_parse_allowed"),
        "create_knowledge_map",
        {"version": 1},
    )

    assert decision is None
