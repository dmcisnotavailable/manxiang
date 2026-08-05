from manxiang.schema import CaptureItem
from manxiang.topics import TopicDiscoverer


def make_capture(index: int, topic: str, note: str) -> CaptureItem:
    return CaptureItem(
        id=f"cap_{index:03d}",
        type="text",
        source=f"source {index}",
        user_note=note,
        captured_at="2026-08-02T20:00:00+08:00",
        tags=["AI 陪伴"],
        emotion_keywords=["困惑"],
        candidate_topics=[topic],
        status="light_tagged",
    )


def test_topic_discoverer_marks_five_related_captures_ready():
    captures = [
        make_capture(i, "AI 陪伴与亲密关系", f"为什么 AI 陪伴让人觉得真实？第 {i} 条")
        for i in range(5)
    ]
    discoverer = TopicDiscoverer()

    topics = discoverer.discover(captures)

    assert len(topics) == 1
    assert topics[0].name == "AI 陪伴与亲密关系"
    assert topics[0].status == "ready"
    assert topics[0].maturity_score >= 0.8
    assert topics[0].suggested_action == "升级为知识地图"


def test_topic_discoverer_keeps_small_topic_as_fragment():
    captures = [make_capture(1, "AI 味写作", "这个表达很像 AI。")]
    discoverer = TopicDiscoverer()

    topics = discoverer.discover(captures)

    assert topics[0].status == "fragment"
    assert topics[0].suggested_action == "继续收集"


def test_topic_discoverer_counts_duplicate_topics_in_one_capture_once():
    capture = CaptureItem(
        id="cap_duplicate",
        type="text",
        source="source duplicate",
        user_note="为什么这个陪伴感会变强？",
        captured_at="2026-08-02T20:00:00+08:00",
        tags=["AI 陪伴"],
        emotion_keywords=["困惑"],
        candidate_topics=["AI 陪伴"] * 5,
        status="light_tagged",
    )
    discoverer = TopicDiscoverer()

    topics = discoverer.discover([capture])

    assert topics[0].status == "fragment"
    assert topics[0].capture_ids == ["cap_duplicate"]
