import json

import pytest

from manxiang.runs import confirm_search, run_surprise_with_bridge
from manxiang.run_state import RunStateMachine
from manxiang.schema import AgentRun
from manxiang.storage import JsonStore
from manxiang.workbench import WorkbenchService


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
    assert updated.updated_at == "2026-08-06T10:05:00+08:00"


def test_confirm_web_search_sets_search_budget():
    machine = RunStateMachine(clock=lambda: "2026-08-06T10:05:00+08:00")

    updated = machine.confirm_web_search(make_run(status="waiting_user"), max_search_queries=2)

    assert updated.status == "exploring"
    assert updated.autonomy_level == "web_search_allowed"
    assert updated.budget["max_search_queries"] == 2
    assert updated.updated_at == "2026-08-06T10:05:00+08:00"


def test_confirm_search_requires_waiting_user(tmp_path):
    store = JsonStore(tmp_path)

    with pytest.raises(ValueError, match="waiting_user"):
        confirm_search(
            store,
            make_run(status="exploring"),
            gap_id="gap_1",
            max_search_queries=2,
            clock=lambda: "2026-08-06T10:05:00+08:00",
        )


def test_confirm_search_persists_web_search_permission(tmp_path):
    store = JsonStore(tmp_path)

    updated = confirm_search(
        store,
        make_run(status="waiting_user"),
        gap_id="gap_1",
        max_search_queries=2,
        clock=lambda: "2026-08-06T10:05:00+08:00",
    )

    assert updated.status == "exploring"
    assert updated.autonomy_level == "web_search_allowed"
    assert updated.budget["max_search_queries"] == 2
    assert updated.updated_at == "2026-08-06T10:05:00+08:00"

    stored_run = json.loads((tmp_path / "runs.json").read_text(encoding="utf-8"))[0]
    assert stored_run["status"] == "exploring"
    assert stored_run["autonomy_level"] == "web_search_allowed"
    assert stored_run["budget"]["max_search_queries"] == 2


def test_confirm_search_rejects_negative_budget(tmp_path):
    store = JsonStore(tmp_path)

    with pytest.raises(ValueError, match="non-negative"):
        confirm_search(
            store,
            make_run(status="waiting_user"),
            gap_id="gap_1",
            max_search_queries=-1,
            clock=lambda: "2026-08-06T10:05:00+08:00",
        )


def test_blocked_tool_completed_is_ignored_and_run_waits_for_user(tmp_path):
    store = JsonStore(tmp_path)

    class FakeBridge:
        def run(self, _run, _captures):
            return {
                "events": [
                    {
                        "type": "tool.started",
                        "tool_name": "create_knowledge_map",
                        "payload": {"nodes": [{"id": "node_1", "confidence": "fact"}]},
                    },
                    {
                        "type": "tool.completed",
                        "tool_name": "create_knowledge_map",
                        "payload": {"map": _valid_agent_map()},
                    },
                ],
            }

    run_surprise_with_bridge(
        store,
        make_run(),
        [],
        bridge=FakeBridge(),
        clock=lambda: "2026-08-06T10:05:00+08:00",
    )

    events = store.replay_events("run_1")
    event_types = [event.type for event in events]
    assert event_types == ["tool.blocked", "user.input.required"]
    assert events[0].payload["tool_name"] == "create_knowledge_map"
    assert events[1].payload == {"tool_name": "create_knowledge_map", "reason": "fact nodes require valid source_refs"}

    stored_run = json.loads((tmp_path / "runs.json").read_text(encoding="utf-8"))[0]
    assert stored_run["status"] == "waiting_user"
    assert stored_run["blocked_tool_count"] == 1
    assert stored_run["updated_at"] == "2026-08-06T10:05:00+08:00"


def test_v1_request_tools_completed_append_replayable_events(tmp_path):
    store = JsonStore(tmp_path)

    class FakeBridge:
        def run(self, _run, _captures):
            events = []
            for tool_name, payload in [
                (
                    "create_research_contract",
                    {
                        "contract": {
                            "task_id": "task_1",
                            "title": "伊莎贝拉研究契约",
                            "goal": "厘清伊莎贝拉资助哥伦布的证据链",
                            "allowed_scope": ["收藏文本"],
                            "blocked_scope": ["无证据扩写"],
                            "completion_definition": "形成带证据引用的修订地图",
                        }
                    },
                ),
                (
                    "request_source_parse",
                    {"capture_id": "cap_1", "reason": "需要解析原文来补足 gap_1", "gap_id": "gap_1"},
                ),
                (
                    "retrieve_evidence_chunks",
                    {"gap_id": "gap_1", "query": "伊莎贝拉 哥伦布", "limit": 5},
                ),
                (
                    "request_web_search",
                    {
                        "gap_id": "gap_1",
                        "query": "Isabella Columbus patronage",
                        "search_goal": "找到伊莎贝拉资助哥伦布的可靠证据",
                        "stop_condition": "找到两个可靠来源后停止",
                        "max_results": 3,
                    },
                ),
            ]:
                events.append({"type": "tool.started", "tool_name": tool_name, "payload": payload})
                events.append({"type": "tool.completed", "tool_name": tool_name, "payload": payload})
            return {"events": events}

    run_surprise_with_bridge(
        store,
        make_run(autonomy_level="web_search_allowed"),
        [],
        bridge=FakeBridge(),
        clock=lambda: "2026-08-06T10:05:00+08:00",
    )

    event_types = [event.type for event in store.replay_events("run_1")]
    assert "research.contract.created" in event_types
    assert "source.parse.requested" in event_types
    assert "evidence.chunks.retrieve.requested" in event_types
    assert "web.search.requested" in event_types


@pytest.mark.parametrize("status", ["exploring", "completed", "failed"])
@pytest.mark.parametrize("method_name", ["confirm_source_parse", "confirm_web_search"])
def test_confirming_permissions_requires_waiting_user(status, method_name):
    machine = RunStateMachine(clock=lambda: "2026-08-06T10:05:00+08:00")

    with pytest.raises(ValueError, match="waiting_user"):
        getattr(machine, method_name)(make_run(status=status))


def test_confirm_source_parse_rejects_negative_budget():
    machine = RunStateMachine(clock=lambda: "2026-08-06T10:05:00+08:00")

    with pytest.raises(ValueError, match="non-negative"):
        machine.confirm_source_parse(make_run(status="waiting_user"), max_source_parses=-1)


def test_confirm_web_search_rejects_negative_budget():
    machine = RunStateMachine(clock=lambda: "2026-08-06T10:05:00+08:00")

    with pytest.raises(ValueError, match="non-negative"):
        machine.confirm_web_search(make_run(status="waiting_user"), max_search_queries=-1)


def test_blocked_tool_without_reason_uses_generic_prompt(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)

    def block_without_reason(_run, _tool_name, _payload):
        return {"block": True}

    class FakeBridge:
        def run(self, _run, _captures):
            return {"events": [{"type": "tool.started", "tool_name": "write_style_memory", "payload": {}}]}

    monkeypatch.setattr("manxiang.runs.before_tool_call", block_without_reason)

    run_surprise_with_bridge(
        store,
        make_run(),
        [],
        bridge=FakeBridge(),
        clock=lambda: "2026-08-06T10:05:00+08:00",
    )

    events = store.replay_events("run_1")
    assert events[-1].type == "user.input.required"
    assert events[-1].payload["reason"] == "tool call requires user confirmation"


def test_workbench_syncs_blocked_bridge_run_state(tmp_path):
    times = iter([
        "2026-08-06T09:55:00+08:00",
        "2026-08-06T10:00:00+08:00",
        "2026-08-06T10:05:00+08:00",
    ])
    service = WorkbenchService(storage_root=tmp_path, clock=lambda: next(times))
    service.capture(type="text", source="manual", raw_text="A note that can start a surprise run.")

    class BlockedBridge:
        def run(self, _run, _captures):
            return {"events": [{"type": "tool.started", "tool_name": "write_style_memory", "payload": {}}]}

    state = service.create_surprise_run(run_bridge=True, bridge=BlockedBridge())

    assert state["surpriseRun"]["status"] == "waiting_user"
    assert state["surpriseRun"]["blocked_tool_count"] == 1
    assert state["surpriseRun"]["updated_at"] == "2026-08-06T10:05:00+08:00"
    assert state["surpriseResult"]["run"]["status"] == "waiting_user"


def _valid_agent_map() -> dict:
    return {
        "id": "map_1",
        "version": 1,
        "title": "Map after confirmation point",
        "core_question": "Why should a blocked tool result never enter the knowledge map?",
        "thesis": "The confirmation gate must block persisted results, not only show a UI warning.",
        "mainline": ["Block tool start", "Ignore the matching tool result", "Wait for user confirmation"],
        "non_obvious_insights": [
            {
                "claim": "A blocked tool start makes the matching later result untrusted.",
                "why_interesting": "Otherwise the reducer can persist output that bypassed confirmation.",
                "source_capture_ids": ["cap_1"],
            },
            {
                "claim": "The waiting_user status is the shared pause point for UI and runtime.",
                "why_interesting": "It tells the interface that the next step needs user approval.",
                "source_capture_ids": ["cap_1"],
            },
            {
                "claim": "The event stream needs user.input.required for replay.",
                "why_interesting": "The UI can still show the confirmation point if the model keeps emitting events.",
                "source_capture_ids": ["cap_1"],
            },
        ],
        "known_unknowns": ["Whether the user grants more autonomy is still unknown."],
        "evidence_gaps": [
            {
                "id": "gap_1",
                "description": "Confirm the waiting state is persisted.",
                "search_query": "run state machine waiting user persistence",
                "source_capture_ids": ["cap_1"],
            },
            {
                "id": "gap_2",
                "description": "Confirm blocked completed results are ignored.",
                "search_query": "blocked tool completed ignored reducer",
                "source_capture_ids": ["cap_1"],
            },
        ],
    }
