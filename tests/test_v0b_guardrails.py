from manxiang.guardrails import before_tool_call
from manxiang.schema import AgentRun


def make_run(autonomy_level: str = "inbox_only") -> AgentRun:
    return AgentRun(
        id="run_1",
        input_capture_ids=["cap_1"],
        autonomy_level=autonomy_level,
        created_at="2026-08-05T20:00:00+08:00",
        updated_at="2026-08-05T20:00:00+08:00",
    )


def test_blocks_search_evidence_in_inbox_only():
    decision = before_tool_call(make_run(), "search_evidence", {"gap_id": "gap_1"})

    assert decision == {"block": True, "reason": "search_evidence requires web_search_allowed"}


def test_blocks_search_without_gap_id():
    decision = before_tool_call(make_run("web_search_allowed"), "search_evidence", {})

    assert decision == {"block": True, "reason": "search_evidence requires gap_id"}


def test_allows_search_after_confirmation_with_gap_id():
    assert before_tool_call(make_run("web_search_allowed"), "search_evidence", {"gap_id": "gap_1"}) is None
