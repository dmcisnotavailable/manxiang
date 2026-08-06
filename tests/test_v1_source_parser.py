import pytest

from manxiang.schema import CaptureItem
from manxiang.source_parser import SourceParser


NOW = "2026-08-06T10:00:00+08:00"


def test_parse_text_capture_to_artifact_and_chunks():
    parser = SourceParser(clock=lambda: NOW, chunk_size=12, overlap=4)
    capture = CaptureItem(
        id="cap_1",
        type="text",
        source="manual",
        user_note="感觉伊莎贝拉和哥伦布能串起来",
        captured_at=NOW,
        original_text="伊莎贝拉一世资助了哥伦布的航行。普拉多博物馆里有很多王室叙事画作。",
    )

    artifact, chunks = parser.parse_capture(capture)

    assert artifact.capture_id == "cap_1"
    assert artifact.parse_status == "parsed"
    assert artifact.uri == "manual://cap_1"
    assert chunks
    assert chunks[0].artifact_id == artifact.id
    assert chunks[0].anchor.startswith("text:")


def test_parse_url_capture_uses_light_summary_without_fetching_full_page():
    parser = SourceParser(clock=lambda: NOW, chunk_size=24, overlap=6)
    capture = CaptureItem(
        id="cap_url",
        type="url",
        source="https://example.com/article",
        user_note="这条新闻可能和王室叙事有关",
        captured_at=NOW,
        source_type="url",
        source_uri="https://example.com/article",
        ai_summary_draft="网页标题提到西班牙王室和艺术收藏。",
        parse_status="metadata_parsed",
    )

    artifact, chunks = parser.parse_capture(capture)

    assert artifact.uri == "https://example.com/article"
    assert chunks[0].text == "网页标题提到西班牙王室和艺术收藏。"


def test_parse_empty_capture_marks_parse_failed_without_chunks():
    parser = SourceParser(clock=lambda: NOW)
    capture = CaptureItem(
        id="cap_empty",
        type="text",
        source="manual",
        user_note="",
        captured_at=NOW,
    )

    artifact, chunks = parser.parse_capture(capture)

    assert artifact.parse_status == "parse_failed"
    assert chunks == []


def test_parse_capture_uses_first_available_text_field():
    parser = SourceParser(clock=lambda: NOW)
    capture = CaptureItem(
        id="cap_priority",
        type="text",
        source="manual",
        user_note="from user_note",
        captured_at=NOW,
        original_text="from original_text",
        raw_text="from raw_text",
        user_summary="from user_summary",
        ai_summary_draft="from ai_summary_draft",
    )

    _, chunks = parser.parse_capture(capture)

    assert chunks[0].text == "from original_text"


def test_parse_capture_falls_back_to_user_summary_before_ai_summary_and_note():
    parser = SourceParser(clock=lambda: NOW)
    capture = CaptureItem(
        id="cap_summary",
        type="text",
        source="manual",
        user_note="from user_note",
        captured_at=NOW,
        user_summary="from user_summary",
        ai_summary_draft="from ai_summary_draft",
    )

    _, chunks = parser.parse_capture(capture)

    assert chunks[0].text == "from user_summary"


def test_reject_invalid_chunk_settings():
    with pytest.raises(ValueError):
        SourceParser(clock=lambda: NOW, chunk_size=0)

    with pytest.raises(ValueError):
        SourceParser(clock=lambda: NOW, overlap=-1)

    with pytest.raises(ValueError):
        SourceParser(clock=lambda: NOW, chunk_size=10, overlap=10)


def test_chunks_include_exact_offsets_and_anchors():
    parser = SourceParser(clock=lambda: NOW, chunk_size=5, overlap=2)
    capture = CaptureItem(
        id="cap_chunks",
        type="text",
        source="manual",
        user_note="",
        captured_at=NOW,
        original_text="abcdefghij",
    )

    _, chunks = parser.parse_capture(capture)

    assert [(chunk.anchor, chunk.text) for chunk in chunks] == [
        ("text:0-5", "abcde"),
        ("text:3-8", "defgh"),
        ("text:6-10", "ghij"),
    ]


def test_parse_ids_and_hashes_are_stable():
    parser = SourceParser(clock=lambda: NOW, chunk_size=6, overlap=2)
    capture = CaptureItem(
        id="cap_stable",
        type="text",
        source="manual",
        user_note="",
        captured_at=NOW,
        original_text="stable source text",
    )

    artifact_1, chunks_1 = parser.parse_capture(capture)
    artifact_2, chunks_2 = parser.parse_capture(capture)

    assert artifact_1.id == artifact_2.id
    assert artifact_1.content_hash == artifact_2.content_hash
    assert [chunk.id for chunk in chunks_1] == [chunk.id for chunk in chunks_2]


def test_parse_legacy_url_capture_uses_source_as_uri():
    parser = SourceParser(clock=lambda: NOW)
    capture = CaptureItem(
        id="cap_legacy_url",
        type="url",
        source="https://example.com/a",
        user_note="legacy url",
        captured_at=NOW,
    )

    artifact, _ = parser.parse_capture(capture)

    assert artifact.uri == "https://example.com/a"
