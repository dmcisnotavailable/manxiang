from manxiang.map_versions import KnowledgeMapVersioner
from manxiang.schema import KnowledgeMap, SourceRef, TextView, TreeNode


def make_map(version: int, child: TreeNode) -> KnowledgeMap:
    return KnowledgeMap(
        task_id="task_1",
        version=version,
        text_view=TextView(
            core_question="西班牙王室叙事如何形成？",
            mainline_summary="亲缘 -> 艺术 -> 航海",
            recommendation_reason="问题线最稳。",
            next_action="继续补证据",
        ),
        tree=TreeNode(id="root", label="西班牙王室叙事", kind="root", children=[child]),
    )


def test_next_version_increments_and_records_inputs():
    versioner = KnowledgeMapVersioner()
    old_map = make_map(1, TreeNode(id="node_1", label="用户认为欧洲王室亲缘密集", kind="concept"))

    new_map = versioner.next_version(
        previous=old_map,
        tree=old_map.tree,
        input_capture_ids=["cap_1"],
        input_chunk_ids=["chunk_1"],
        evidence_ids=["ev_1"],
    )

    assert new_map.version == 2
    assert new_map.input_capture_ids == ["cap_1"]
    assert new_map.input_chunk_ids == ["chunk_1"]
    assert new_map.evidence_ids == ["ev_1"]


def test_diff_reports_changed_confidence_and_added_source_ref():
    versioner = KnowledgeMapVersioner()
    before = make_map(1, TreeNode(id="node_1", label="伊莎贝拉和哥伦布有关", kind="concept", confidence="hypothesis"))
    after = make_map(
        2,
        TreeNode(
            id="node_1",
            label="伊莎贝拉一世资助了哥伦布航行",
            kind="concept",
            confidence="fact",
            source_refs=[
                SourceRef(
                    artifact_id="artifact_1",
                    chunk_id="chunk_1",
                    quote="伊莎贝拉一世资助了哥伦布航行",
                    anchor="text:0-18",
                )
            ],
        ),
    )

    diff = versioner.diff(before, after)

    assert diff["changed_nodes"][0]["id"] == "node_1"
    assert diff["changed_nodes"][0]["before_confidence"] == "hypothesis"
    assert diff["changed_nodes"][0]["after_confidence"] == "fact"
