from manxiang.capture import CaptureProcessor


def test_capture_processor_tags_ai_companion_without_network():
    processor = CaptureProcessor(clock=lambda: "2026-08-02T20:00:00+08:00")

    item = processor.capture(
        type="url",
        source="https://example.com/ai-companion",
        user_note="明知道是 AI，为什么还是会觉得被理解和陪伴？",
    )

    assert item.id.startswith("cap_")
    assert item.status == "light_tagged"
    assert "AI 陪伴" in item.tags
    assert "真实感" in item.tags
    assert "AI 陪伴与亲密关系" in item.candidate_topics
    assert item.summary == "用户收藏了一个链接，并记录了关于 AI 陪伴、真实感 的即时感想。"
