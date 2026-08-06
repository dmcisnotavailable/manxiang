from dataclasses import replace
from hashlib import sha1

from manxiang.guardrails import before_tool_call
from manxiang.reducers import reduce_tool_result
from manxiang.runtime import PiAgentBridge
from manxiang.schema import AgentRun, CaptureItem
from manxiang.storage import JsonStore


def create_run(store: JsonStore, capture_ids: list[str], clock) -> AgentRun:
    now = clock()
    digest = sha1("|".join(capture_ids).encode("utf-8")).hexdigest()[:10]
    run = AgentRun(
        id=f"run_{digest}",
        input_capture_ids=capture_ids,
        status="exploring",
        created_at=now,
        updated_at=now,
    )
    store._upsert("runs.json", run.id, run)
    store.append_event(run.id, "run.started", {"capture_ids": capture_ids})
    return run


def confirm_search(store: JsonStore, run: AgentRun, gap_id: str, max_search_queries: int, clock) -> AgentRun:
    updated = replace(
        run,
        autonomy_level="web_search_allowed",
        status="exploring",
        budget={**run.budget, "max_search_queries": max_search_queries},
        updated_at=clock(),
    )
    store._upsert("runs.json", updated.id, updated)
    store.append_event(updated.id, "user.input.required", {"resolved": True, "gap_id": gap_id})
    return updated


def run_surprise_with_bridge(
    store: JsonStore,
    run: AgentRun,
    captures: list[CaptureItem],
    bridge: PiAgentBridge | None = None,
) -> dict:
    bridge = bridge or PiAgentBridge()
    result = bridge.run(run, captures)
    for event in result.get("events", []):
        tool_name = event.get("tool_name", "")
        if event["type"] == "tool.started":
            decision = before_tool_call(run, tool_name, event.get("payload", {}))
            if decision:
                store.append_event(run.id, "tool.blocked", {"tool_name": tool_name, **decision})
                store.append_event(run.id, "user.input.required", {"tool_name": tool_name, "reason": decision["reason"]})
                continue
            store.append_event(run.id, "tool.started", event)
        elif event["type"] == "tool.completed":
            store.append_event(run.id, "tool.completed", event)
            if event.get("payload") and tool_name:
                reduce_tool_result(store, run.id, tool_name, event["payload"])
    return result
