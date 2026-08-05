from manxiang.navigation import TaskNavigator
from manxiang.schema import CaptureItem, TopicCluster


def test_navigator_creates_task_and_recommends_causal_line():
    topic = TopicCluster(
        id="topic_001",
        name="AI 陪伴与亲密关系",
        status="ready",
        capture_ids=["cap_001", "cap_002"],
        repeated_questions=["为什么 AI 陪伴让人觉得真实？"],
        emotion_patterns=["困惑"],
        maturity_score=0.9,
        suggested_action="升级为知识地图",
    )
    captures = [
        CaptureItem(
            id="cap_001",
            type="text",
            source="source",
            user_note="为什么 AI 陪伴让人觉得真实？",
            captured_at="2026-08-02T20:00:00+08:00",
            tags=["AI 陪伴", "真实感"],
            candidate_topics=["AI 陪伴与亲密关系"],
        )
    ]
    navigator = TaskNavigator(clock=lambda: "2026-08-02T20:00:00+08:00")

    task = navigator.create_task(topic, mode="gentle_editor")
    line_plan = navigator.recommend_line(task, captures)

    assert task.stage == "scoping"
    assert task.default_output == "knowledge_map"
    assert line_plan.recommended_line == "causal"
    assert line_plan.selected_line == "causal"
    assert line_plan.line_nodes


def test_navigator_explains_risk_before_line_override():
    navigator = TaskNavigator(clock=lambda: "2026-08-02T20:00:00+08:00")

    notes = navigator.explain_line_override(current="causal", requested="emotion")

    assert "个人表达" in notes[0]
    assert "逻辑严谨度" in notes[1]


def test_navigator_uses_question_line_when_no_real_signal():
    topic = TopicCluster(
        id="topic_002",
        name="普通主题",
        status="gathering",
        capture_ids=[],
        repeated_questions=[],
        emotion_patterns=[],
        maturity_score=0.3,
        suggested_action="先做问题地图",
    )
    navigator = TaskNavigator(clock=lambda: "2026-08-02T20:00:00+08:00")

    task = navigator.create_task(topic, mode="gentle_editor")
    line_plan = navigator.recommend_line(task, captures=[])

    assert line_plan.recommended_line == "question"


def test_navigator_prefixes_custom_topic_id_with_task():
    topic = TopicCluster(
        id="custom_001",
        name="自定义主题",
        status="ready",
        capture_ids=[],
        repeated_questions=[],
        emotion_patterns=[],
        maturity_score=0.8,
        suggested_action="升级为知识地图",
    )
    navigator = TaskNavigator(clock=lambda: "2026-08-02T20:00:00+08:00")

    task = navigator.create_task(topic, mode="gentle_editor")

    assert task.id == "task_custom_001"
