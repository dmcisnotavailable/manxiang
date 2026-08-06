from manxiang.schema import CaptureItem
from manxiang.source_parser import SourceParser


def test_parse_text_capture_to_artifact_and_chunks():
    parser = SourceParser(clock=lambda: "2026-08-06T10:00:00+08:00", chunk_size=12, overlap=4)
    capture = CaptureItem(
        id="cap_1",
        type="text",
        source="manual",
        user_note="感觉伊莎贝拉和哥伦布能串起来",
        captured_at="2026-08-06T10:00:00+08:00",
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
    parser = SourceParser(clock=lambda: "2026-08-06T10:00:00+08:00", chunk_size=24, overlap=6)
    capture = CaptureItem(
        id="cap_url",
        type="url",
        source="https://example.com/article",
        user_note="这条新闻可能和王室叙事有关",
        captured_at="2026-08-06T10:00:00+08:00",
        source_type="url",
        source_uri="https://example.com/article",
        ai_summary_draft="网页标题提到西班牙王室和艺术收藏。",
        parse_status="metadata_parsed",
    )

    artifact, chunks = parser.parse_capture(capture)

    assert artifact.uri == "https://example.com/article"
    assert chunks[0].text == "网页标题提到西班牙王室和艺术收藏。"
