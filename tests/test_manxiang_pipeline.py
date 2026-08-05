import pytest

from manxiang.pipeline import ManxiangPipeline


def test_pipeline_turns_captures_into_ready_topic_and_map(tmp_path):
    pipeline = ManxiangPipeline(storage_root=tmp_path, clock=lambda: "2026-08-02T20:00:00+08:00")

    for index in range(5):
        pipeline.capture(
            type="text",
            source=f"note {index}",
            user_note=f"为什么 AI 陪伴让人觉得真实和被理解？第 {index} 条",
        )

    topics = pipeline.discover_topics()
    task, line_plan, knowledge_map = pipeline.create_knowledge_map(topics[0].id, mode="gentle_editor")

    assert topics[0].status == "ready"
    assert task.stage == "scoping"
    assert line_plan.recommended_line == "causal"
    assert knowledge_map.tree.label == task.title


def test_pipeline_explains_discover_topics_requirement(tmp_path):
    pipeline = ManxiangPipeline(storage_root=tmp_path, clock=lambda: "2026-08-02T20:00:00+08:00")
    pipeline.capture(
        type="text",
        source="note 1",
        user_note="为什么 AI 陪伴让人觉得真实？",
    )

    with pytest.raises(ValueError, match="Run discover_topics\\(\\)"):
        pipeline.create_knowledge_map("topic_missing", mode="gentle_editor")


def test_pipeline_persists_created_task_and_map(tmp_path):
    pipeline = ManxiangPipeline(storage_root=tmp_path, clock=lambda: "2026-08-02T20:00:00+08:00")

    for index in range(5):
        pipeline.capture(
            type="text",
            source=f"note {index}",
            user_note=f"为什么 AI 陪伴让人觉得真实和被理解？第 {index} 条",
        )

    topics = pipeline.discover_topics()
    task, _, knowledge_map = pipeline.create_knowledge_map(topics[0].id, mode="gentle_editor")

    assert pipeline.store.list_tasks() == [task]
    assert pipeline.store.list_maps() == [knowledge_map]
