from manxiang.schema import CaptureItem, KnowledgeMap, ResearchTask, TextView, TreeNode


def test_capture_item_has_default_captured_state():
    item = CaptureItem(
        id="cap_001",
        type="url",
        source="https://example.com",
        user_note="为什么这个 AI 陪伴产品让人觉得被理解？",
        captured_at="2026-08-02T20:00:00+08:00",
    )

    assert item.status == "captured"
    assert item.tags == []
    assert item.candidate_topics == []


def test_knowledge_map_has_text_and_tree_views():
    task = ResearchTask(
        id="task_001",
        title="AI 陪伴为什么让人觉得像真的",
        topic_id="topic_001",
        stage="map_drafted",
        default_output="knowledge_map",
        mode="gentle_editor",
        goal="生成知识地图",
        core_question="为什么人会把情感需求交给 AI？",
        completion_definition="形成文本 + 树状图知识地图",
        allowed_scope=["用户心理"],
        blocked_scope=["底层模型架构"],
        created_at="2026-08-02T20:00:00+08:00",
        updated_at="2026-08-02T20:00:00+08:00",
    )
    tree = TreeNode(id="root", label=task.title, kind="root")
    text = TextView(
        core_question=task.core_question,
        mainline_summary="孤独感增加 -> 低风险表达 -> 即时回应",
        recommendation_reason="用户感想多次出现为什么和真实感。",
        next_action="确认主线节点",
    )
    knowledge_map = KnowledgeMap(task_id=task.id, version=1, text_view=text, tree=tree)

    assert knowledge_map.text_view.core_question == task.core_question
    assert knowledge_map.tree.label == task.title
