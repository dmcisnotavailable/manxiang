from manxiang.schema import CaptureItem, KnowledgeMap, SourceRef, TextView, TreeNode
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


def test_json_store_round_trips_v1_knowledge_map_fields(tmp_path):
    store = JsonStore(tmp_path)
    ref = SourceRef(
        artifact_id="artifact_1",
        chunk_id="chunk_1",
        quote="伊莎贝拉一世资助了哥伦布的航行。",
        anchor="text:0-18",
    )
    knowledge_map = KnowledgeMap(
        task_id="task_v1",
        version=2,
        text_view=TextView(
            core_question="西班牙王室叙事如何连接亲缘、艺术和航海？",
            mainline_summary="亲缘误读 -> 王室图像 -> 航海扩张",
            recommendation_reason="当前材料最适合用问题线组织。",
            next_action="核验证据缺口 gap_genealogy",
        ),
        tree=TreeNode(
            id="root",
            label="西班牙王权叙事",
            kind="root",
            confidence="fact",
            source_refs=[ref],
            children=[
                TreeNode(
                    id="gap_genealogy",
                    label="亲缘关系需要补证据",
                    kind="evidence_gap",
                    confidence="needs_evidence",
                )
            ],
        ),
        input_capture_ids=["cap_1", "cap_2"],
        input_chunk_ids=["chunk_1"],
        evidence_ids=["ev_1"],
    )

    store.save_map(knowledge_map)

    [loaded] = store.list_maps()
    assert loaded == knowledge_map
    assert loaded.tree.source_refs == [ref]
    assert loaded.tree.children[0].confidence == "needs_evidence"
    assert loaded.input_capture_ids == ["cap_1", "cap_2"]
    assert loaded.input_chunk_ids == ["chunk_1"]
    assert loaded.evidence_ids == ["ev_1"]
