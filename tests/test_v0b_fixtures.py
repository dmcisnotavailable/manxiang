from pathlib import Path

from manxiang.fixtures import v0b_capture_fixtures
from manxiang.schema import AgentRun, CaptureItem, default_run_budget


def test_v0b_fixtures_use_real_user_inputs():
    fixtures = v0b_capture_fixtures()

    assert len(fixtures) == 6
    assert fixtures[0]["original_text"] == "伊莎贝拉和伊丽莎白两个著名的女王有血缘关系。"
    assert fixtures[3]["source_uri"] == "https://www.bjnews.com.cn/detail/173352872819482.html"
    assert fixtures[4]["source_type"] == "mixed"
    assert Path(fixtures[4]["source_uri"]).name == "2026-08-05-spanish-royal-family.png"
    assert "哥伦布" in fixtures[5]["user_note"]


def test_capture_item_supports_v0b_fields_while_user_note_is_optional():
    item = CaptureItem(
        id="cap_test",
        type="text",
        source="manual",
        user_note="",
        captured_at="2026-08-05T20:00:00+08:00",
        source_type="text",
        original_text="普拉多博物馆有很多西班牙王室故事为背景的画作。",
    )

    assert item.user_note == ""
    assert item.summary_status == "summary_pending"
    assert item.parse_status == "not_parsed"
    assert item.attachment_ids == []


def test_agent_run_defaults_to_inbox_only():
    run = AgentRun(
        id="run_test",
        input_capture_ids=["cap_1"],
        created_at="2026-08-05T20:00:00+08:00",
        updated_at="2026-08-05T20:00:00+08:00",
    )

    assert run.autonomy_level == "inbox_only"
    assert run.budget == default_run_budget()
