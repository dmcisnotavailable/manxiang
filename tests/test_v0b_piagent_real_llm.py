import os

from manxiang.capture import CaptureProcessor
from manxiang.fixtures import v0b_capture_fixtures
from manxiang.runtime import PiAgentBridge
from manxiang.runs import create_run, run_surprise_with_bridge
from manxiang.storage import JsonStore


def require_real_env():
    missing = [
        key
        for key in ["MANXIANG_LLM_PROVIDER", "MANXIANG_LLM_MODEL"]
        if not os.environ.get(key)
    ]
    if missing:
        raise RuntimeError(f"Real Pi Agent test requires env vars: {', '.join(missing)}")


def test_piagent_real_llm_v0b_surprise_to_research_flow(tmp_path):
    require_real_env()
    store = JsonStore(tmp_path)
    processor = CaptureProcessor(clock=lambda: "2026-08-05T20:00:00+08:00")

    captures = []
    for fixture in v0b_capture_fixtures():
        capture = processor.capture(
            type="url" if fixture["source_type"] == "url" else "screenshot_note" if fixture["source_type"] == "mixed" else "text",
            source=fixture.get("source_uri", "manual"),
            user_note=fixture.get("user_note", ""),
            raw_text=fixture.get("original_text", ""),
        )
        store.save_capture(capture)
        captures.append(capture)

    run = create_run(store, [capture.id for capture in captures], clock=lambda: "2026-08-05T20:00:00+08:00")
    result = run_surprise_with_bridge(store, run, captures, bridge=PiAgentBridge())

    assert result["model_name"] == os.environ["MANXIANG_LLM_MODEL"]
    assert "record_collection_reading" in result["tool_calls"]
    assert "create_knowledge_map" in result["tool_calls"]
    assert any(event["type"] == "tool.completed" for event in result["events"])

    maps = [event.payload for event in store.replay_events(run.id) if event.type == "map.created"]
    assert maps
    agent_map = maps[-1]
    text = str(agent_map)
    assert "我已知道什么" not in text
    assert "核心问题还不清楚" not in text
    assert len(agent_map["non_obvious_insights"]) >= 3
    assert all(item["source_capture_ids"] for item in agent_map["non_obvious_insights"])
    assert len(agent_map["evidence_gaps"]) >= 2
    assert all(gap["search_query"] for gap in agent_map["evidence_gaps"])
