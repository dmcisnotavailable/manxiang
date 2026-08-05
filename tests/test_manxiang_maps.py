from manxiang.maps import KnowledgeMapBuilder
from manxiang.schema import KnowledgeMap, LineNode, LinePlan, ResearchTask


def _make_task() -> ResearchTask:
    return ResearchTask(
        id="task_001",
        title="AI 陪伴为什么让人觉得像真的",
        topic_id="topic_001",
        stage="line_chosen",
        default_output="knowledge_map",
        mode="gentle_editor",
        goal="生成知识地图",
        core_question="为什么 AI 陪伴让人觉得真实？",
        completion_definition="形成文本 + 树状图知识地图",
        allowed_scope=["用户心理"],
        blocked_scope=["模型架构"],
        created_at="2026-08-02T20:00:00+08:00",
        updated_at="2026-08-02T20:00:00+08:00",
    )


def _make_line_plan(node_count: int) -> LinePlan:
    return LinePlan(
        task_id="task_001",
        recommended_line="causal",
        selected_line="causal",
        auxiliary_lines=["emotion"],
        recommendation_reason="适合解释为什么。",
        risk_notes=[],
        line_nodes=[
            LineNode(
                id=f"line_{index + 1}",
                title=f"主线节点 {index + 1}",
                kind="mainline",
                summary=f"第 {index + 1} 个主线节点。",
                depth_limit=2,
                status="expandable",
            )
            for index in range(node_count)
        ],
    )


def _child_by_id(node, child_id):
    return next(child for child in node.children if child.id == child_id)


def test_map_builder_creates_limited_text_and_tree_views():
    task = ResearchTask(
        id="task_001",
        title="AI 陪伴为什么让人觉得像真的",
        topic_id="topic_001",
        stage="line_chosen",
        default_output="knowledge_map",
        mode="gentle_editor",
        goal="生成知识地图",
        core_question="为什么 AI 陪伴让人觉得真实？",
        completion_definition="形成文本 + 树状图知识地图",
        allowed_scope=["用户心理"],
        blocked_scope=["模型架构"],
        created_at="2026-08-02T20:00:00+08:00",
        updated_at="2026-08-02T20:00:00+08:00",
    )
    line_plan = LinePlan(
        task_id=task.id,
        recommended_line="causal",
        selected_line="causal",
        auxiliary_lines=["emotion"],
        recommendation_reason="适合解释为什么。",
        risk_notes=[],
        line_nodes=[
            LineNode(id="line_1", title="低风险表达", kind="mainline", summary="用户表达成本降低。", depth_limit=2, status="expandable"),
            LineNode(id="line_2", title="即时回应", kind="mainline", summary="随时得到回应。", depth_limit=2, status="expandable"),
        ],
    )
    builder = KnowledgeMapBuilder()

    knowledge_map = builder.build(task, line_plan, concepts=["情绪价值", "长期记忆"], evidence_titles=["用户访谈"], gaps=["长期使用动机"])

    assert isinstance(knowledge_map, KnowledgeMap)
    assert knowledge_map.text_view.core_question == task.core_question
    assert "低风险表达 -> 即时回应" in knowledge_map.text_view.mainline_summary
    root_labels = [child.label for child in knowledge_map.tree.children]
    assert "核心问题" in root_labels
    assert "推荐主线" in root_labels
    assert "分支停车场" in root_labels


def test_map_builder_namespaces_mainline_tree_node_ids():
    task = _make_task()
    line_plan = _make_line_plan(1)
    knowledge_map = KnowledgeMapBuilder().build(task, line_plan, concepts=[], evidence_titles=[], gaps=[])

    mainline = _child_by_id(knowledge_map.tree, "mainline")
    mainline_node = mainline.children[0]
    original_node = line_plan.line_nodes[0]

    assert mainline_node.id != original_node.id
    assert mainline_node.id.startswith("map_mainline_")
    assert mainline_node.label == original_node.title
    assert mainline_node.kind == "mainline"


def test_map_builder_truncates_tree_sections_to_mvp_limits():
    task = _make_task()
    line_plan = _make_line_plan(6)
    knowledge_map = KnowledgeMapBuilder().build(
        task,
        line_plan,
        concepts=[f"概念 {index + 1}" for index in range(8)],
        evidence_titles=[f"证据 {index + 1}" for index in range(11)],
        gaps=[f"缺口 {index + 1}" for index in range(6)],
    )

    assert len(_child_by_id(knowledge_map.tree, "mainline").children) == 5
    assert len(_child_by_id(knowledge_map.tree, "concepts").children) == 7
    assert len(_child_by_id(knowledge_map.tree, "evidence").children) == 10
    assert len(_child_by_id(knowledge_map.tree, "evidence_gaps").children) == 5


def test_map_builder_uses_confirmation_next_action_when_gaps_are_empty():
    task = _make_task()
    line_plan = _make_line_plan(1)
    knowledge_map = KnowledgeMapBuilder().build(task, line_plan, concepts=[], evidence_titles=[], gaps=[])

    assert knowledge_map.text_view.next_action == "确认知识地图，决定是否升级为短札记或主题报告"
