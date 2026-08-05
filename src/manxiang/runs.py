from dataclasses import replace
from hashlib import sha1

from manxiang.schema import AgentRun
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
