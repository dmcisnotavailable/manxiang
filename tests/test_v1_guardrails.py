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


def test_blocks_retrieval_without_gap_id():
    decision = before_tool_call(run("source_parse_allowed"), "retrieve_evidence_chunks", {"query": "伊莎贝拉 哥伦布"})

    assert decision == {"block": True, "reason": "retrieve_evidence_chunks requires gap_id"}


def test_blocks_fact_upgrade_without_source_refs():
    decision = before_tool_call(
        run("source_parse_allowed"),
        "revise_knowledge_map",
        {"nodes": [{"id": "node_1", "confidence": "fact", "source_refs": []}]},
    )

    assert decision == {"block": True, "reason": "fact nodes require source_refs"}
