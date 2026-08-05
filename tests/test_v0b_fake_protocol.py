from manxiang.runtime import PiAgentBridge
from manxiang.schema import AgentRun, CaptureItem


def test_bridge_sends_real_capture_payload_and_reads_events(tmp_path):
    calls = []

    def fake_runner(payload):
        calls.append(payload)
        return {
            "model_name": "fake-model",
            "tool_calls": ["explore_captures", "search_evidence"],
            "events": [
                {"type": "tool.started", "tool_name": "explore_captures"},
                {"type": "tool.completed", "tool_name": "explore_captures", "payload": {"themes": ["西班牙王室"]}},
            ],
        }

    bridge = PiAgentBridge(runner=fake_runner)
    run = AgentRun(
        id="run_1",
        input_capture_ids=["cap_1"],
        created_at="2026-08-05T20:00:00+08:00",
        updated_at="2026-08-05T20:00:00+08:00",
    )
    captures = [
        CaptureItem(
            id="cap_1",
            type="text",
            source="manual",
            user_note="",
            captured_at="2026-08-05T20:00:00+08:00",
            original_text="伊莎贝拉和伊丽莎白两个著名的女王有血缘关系。",
            candidate_topics=["伊莎贝拉女王"],
        )
    ]

    result = bridge.run(run, captures)

    assert calls[0]["run_id"] == "run_1"
    assert calls[0]["captures"][0]["original_text"].startswith("伊莎贝拉")
    assert result["tool_calls"] == ["explore_captures", "search_evidence"]
