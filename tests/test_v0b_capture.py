from pathlib import Path

from manxiang.capture import CaptureProcessor
from manxiang.fixtures import v0b_capture_fixtures


def test_text_capture_accepts_missing_user_note():
    processor = CaptureProcessor(clock=lambda: "2026-08-05T20:00:00+08:00")

    item = processor.capture(
        type="text",
        source="manual",
        user_note="",
        raw_text="普拉多博物馆有很多西班牙王室故事为背景的画作。",
    )

    assert item.user_note == ""
    assert item.original_text == "普拉多博物馆有很多西班牙王室故事为背景的画作。"
    assert item.summary_status == "summary_pending"
    assert item.parse_status == "not_parsed"
    assert "普拉多博物馆" in item.candidate_topics


def test_mixed_image_capture_keeps_attachment_reference():
    fixture = v0b_capture_fixtures()[4]
    processor = CaptureProcessor(clock=lambda: "2026-08-05T20:00:00+08:00")

    item = processor.capture(
        type="screenshot_note",
        source=fixture["source_uri"],
        user_note=fixture["user_note"],
    )

    assert item.source_type == "mixed"
    assert item.source_uri.endswith("2026-08-05-spanish-royal-family.png")
    assert Path(item.source_uri).exists()
    assert item.attachment_ids
    assert item.summary_status == "summary_pending"
    assert "西班牙王室" in item.candidate_topics


def test_url_capture_parse_failure_does_not_block_collection():
    processor = CaptureProcessor(clock=lambda: "2026-08-05T20:00:00+08:00")

    item = processor.capture(
        type="url",
        source="https://zhuanlan.zhihu.com/p/300938362",
        user_note="伊莎贝拉女王和哥伦布相关，感觉能串起来了",
    )

    assert item.source_type == "url"
    assert item.source_uri == "https://zhuanlan.zhihu.com/p/300938362"
    assert item.parse_status in {"metadata_parsed", "parse_failed"}
    assert "哥伦布" in item.candidate_topics
