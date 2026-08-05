from manxiang.schema import CaptureItem, TextView, TreeNode, KnowledgeMap
from manxiang.storage import JsonStore


def test_json_store_round_trips_capture_items(tmp_path):
    store = JsonStore(tmp_path)
    item = CaptureItem(
        id="cap_001",
        type="url",
        source="https://example.com",
        user_note="这个观点让我想知道为什么。",
        captured_at="2026-08-02T20:00:00+08:00",
        tags=["AI 陪伴"],
        candidate_topics=["AI 陪伴与亲密关系"],
        status="light_tagged",
    )

    store.save_capture(item)

    assert store.list_captures() == [item]


def test_json_store_round_trips_knowledge_maps(tmp_path):
    store = JsonStore(tmp_path)
    knowledge_map = KnowledgeMap(
        task_id="task_001",
        version=1,
        text_view=TextView(
            core_question="为什么人会把情感需求交给 AI？",
            mainline_summary="孤独感增加 -> 低风险表达",
            recommendation_reason="资料集中在原因解释。",
            next_action="补长期使用动机的证据",
        ),
        tree=TreeNode(
            id="root",
            label="AI 陪伴为什么让人觉得像真的",
            kind="root",
            children=[TreeNode(id="mainline", label="推荐主线", kind="mainline")],
        ),
    )

    store.save_map(knowledge_map)

    assert store.list_maps() == [knowledge_map]
