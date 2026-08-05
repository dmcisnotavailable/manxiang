import pytest

from manxiang.evidence import EvidencePatcher, FakeSearchProvider
from manxiang.schema import EvidenceGap, ResearchTask


def make_task(stage: str) -> ResearchTask:
    return ResearchTask(
        id="task_001",
        title="AI 陪伴为什么让人觉得像真的",
        topic_id="topic_001",
        stage=stage,
        default_output="knowledge_map",
        mode="gentle_editor",
        goal="生成知识地图",
        core_question="为什么 AI 陪伴让人觉得真实？",
        completion_definition="形成知识地图",
        allowed_scope=["用户心理"],
        blocked_scope=["模型架构"],
        created_at="2026-08-02T20:00:00+08:00",
        updated_at="2026-08-02T20:00:00+08:00",
    )


def make_gap(**overrides: str) -> EvidenceGap:
    values = {
        "id": "gap_001",
        "task_id": "task_001",
        "node_id": "line_1",
        "description": "缺少长期使用动机证据",
        "search_goal": "找用户研究",
        "stop_condition": "找到 2 条可用证据后停止",
    }
    values.update(overrides)
    return EvidenceGap(**values)


def test_evidence_patcher_rejects_search_outside_evidence_stage():
    patcher = EvidencePatcher(search_provider=FakeSearchProvider([]), clock=lambda: "2026-08-02T20:00:00+08:00")
    gap = EvidenceGap(
        id="gap_001",
        task_id="task_001",
        node_id="line_1",
        description="缺少长期使用动机证据",
        search_goal="找用户研究",
        stop_condition="找到 2 条可用证据后停止",
    )

    with pytest.raises(ValueError, match="只允许在补证据阶段搜索"):
        patcher.patch(make_task("map_drafted"), gap, query="AI companion user motivation")


def test_evidence_patcher_rejects_search_when_gap_only_found():
    patcher = EvidencePatcher(search_provider=FakeSearchProvider([]), clock=lambda: "2026-08-02T20:00:00+08:00")

    with pytest.raises(ValueError, match="只允许在补证据阶段搜索"):
        patcher.patch(make_task("evidence_gap_found"), make_gap(), query="AI companion user motivation")


def test_evidence_patcher_rejects_gap_from_another_task():
    patcher = EvidencePatcher(search_provider=FakeSearchProvider([]), clock=lambda: "2026-08-02T20:00:00+08:00")

    with pytest.raises(ValueError, match="证据缺口必须属于当前研究任务"):
        patcher.patch(make_task("evidence_patching"), make_gap(task_id="task_other"), query="AI companion user motivation")


@pytest.mark.parametrize("search_goal", ["", "   "])
def test_evidence_patcher_rejects_empty_search_goal(search_goal: str):
    patcher = EvidencePatcher(search_provider=FakeSearchProvider([]), clock=lambda: "2026-08-02T20:00:00+08:00")

    with pytest.raises(ValueError, match="搜索前必须有搜索目标和停止条件"):
        patcher.patch(make_task("evidence_patching"), make_gap(search_goal=search_goal), query="AI companion user motivation")


@pytest.mark.parametrize("stop_condition", ["", "   "])
def test_evidence_patcher_rejects_empty_stop_condition(stop_condition: str):
    patcher = EvidencePatcher(search_provider=FakeSearchProvider([]), clock=lambda: "2026-08-02T20:00:00+08:00")

    with pytest.raises(ValueError, match="搜索前必须有搜索目标和停止条件"):
        patcher.patch(
            make_task("evidence_patching"),
            make_gap(stop_condition=stop_condition),
            query="AI companion user motivation",
        )


@pytest.mark.parametrize("query", ["", "   "])
def test_evidence_patcher_rejects_empty_query(query: str):
    patcher = EvidencePatcher(search_provider=FakeSearchProvider([]), clock=lambda: "2026-08-02T20:00:00+08:00")

    with pytest.raises(ValueError, match="搜索前必须有明确查询词"):
        patcher.patch(make_task("evidence_patching"), make_gap(), query=query)


def test_evidence_patcher_limits_search_results_to_three_evidence_items():
    provider = FakeSearchProvider(
        [
            {
                "title": f"AI companion user report {index}",
                "url": f"https://example.com/report-{index}",
                "snippet": "Users mention immediate response and low-pressure expression.",
            }
            for index in range(5)
        ]
    )
    patcher = EvidencePatcher(search_provider=provider, clock=lambda: "2026-08-02T20:00:00+08:00")

    evidence = patcher.patch(make_task("evidence_patching"), make_gap(), query="AI companion user motivation")

    assert len(evidence) == 3


def test_evidence_patcher_converts_search_results_to_evidence():
    provider = FakeSearchProvider(
        [
            {
                "title": "AI companion user report",
                "url": "https://example.com/report",
                "snippet": "Users mention immediate response and low-pressure expression.",
            }
        ]
    )
    patcher = EvidencePatcher(search_provider=provider, clock=lambda: "2026-08-02T20:00:00+08:00")
    gap = EvidenceGap(
        id="gap_001",
        task_id="task_001",
        node_id="line_1",
        description="缺少长期使用动机证据",
        search_goal="找用户研究",
        stop_condition="找到 2 条可用证据后停止",
    )

    evidence = patcher.patch(make_task("evidence_patching"), gap, query="AI companion user motivation")

    assert len(evidence) == 1
    assert evidence[0].supports_node_id == "line_1"
    assert evidence[0].strength == "medium"
