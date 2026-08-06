from manxiang.run_state import RunStateMachine
from manxiang.schema import AgentRun


def make_run(status: str = "exploring", autonomy_level: str = "inbox_only") -> AgentRun:
    return AgentRun(
        id="run_1",
        input_capture_ids=["cap_1"],
        status=status,
        autonomy_level=autonomy_level,
        created_at="2026-08-06T10:00:00+08:00",
        updated_at="2026-08-06T10:00:00+08:00",
    )


def test_blocked_search_moves_run_to_waiting_user():
    machine = RunStateMachine(clock=lambda: "2026-08-06T10:05:00+08:00")

    updated = machine.block_for_user(make_run(), reason="search requires confirmation")

    assert updated.status == "waiting_user"
    assert updated.updated_at == "2026-08-06T10:05:00+08:00"
    assert updated.blocked_tool_count == 1


def test_confirm_source_parse_allows_parsing_but_not_web_search():
    machine = RunStateMachine(clock=lambda: "2026-08-06T10:05:00+08:00")

    updated = machine.confirm_source_parse(make_run(status="waiting_user"))

    assert updated.status == "exploring"
    assert updated.autonomy_level == "source_parse_allowed"
    assert updated.budget["max_source_parses"] == 3
    assert updated.budget["max_search_queries"] == 0


def test_confirm_web_search_sets_search_budget():
    machine = RunStateMachine(clock=lambda: "2026-08-06T10:05:00+08:00")

    updated = machine.confirm_web_search(make_run(status="waiting_user"), max_search_queries=2)

    assert updated.status == "exploring"
    assert updated.autonomy_level == "web_search_allowed"
    assert updated.budget["max_search_queries"] == 2
