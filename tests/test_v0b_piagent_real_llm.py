import os

from manxiang.capture import CaptureProcessor
from manxiang.fixtures import v0b_capture_fixtures
from manxiang.runtime import PiAgentBridge
from manxiang.runs import create_run
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
    result = PiAgentBridge().run(run, captures)

    assert result["model_name"] == os.environ["MANXIANG_LLM_MODEL"]
    assert "explore_captures" in result["tool_calls"]
    assert any(event["type"] == "tool.completed" for event in result["events"])
