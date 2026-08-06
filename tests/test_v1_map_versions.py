import pytest

from manxiang.map_versions import KnowledgeMapVersioner
from manxiang.schema import KnowledgeMap, SourceRef, TextView, TreeNode


def make_map(version: int, child: TreeNode) -> KnowledgeMap:
    return make_map_with_children(version, [child])


def make_map_with_children(version: int, children: list[TreeNode]) -> KnowledgeMap:
    return KnowledgeMap(
        task_id="task_1",
        version=version,
        text_view=TextView(
            core_question="西班牙王室叙事如何形成？",
            mainline_summary="亲缘 -> 艺术 -> 航海",
            recommendation_reason="问题线最稳。",
            next_action="继续补证据",
        ),
        tree=TreeNode(id="root", label="西班牙王室叙事", kind="root", children=children),
    )


def source_ref(artifact_id: str, chunk_id: str) -> SourceRef:
    return SourceRef(
        artifact_id=artifact_id,
        chunk_id=chunk_id,
        quote="伊莎贝拉一世资助了哥伦布航行",
        anchor="text:0-18",
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


def test_next_version_uses_text_view_override():
    versioner = KnowledgeMapVersioner()
    old_map = make_map(1, TreeNode(id="node_1", label="用户认为欧洲王室亲缘密集", kind="concept"))
    text_view = TextView(
        core_question="伊莎贝拉一世如何影响航海叙事？",
        mainline_summary="资助 -> 航行 -> 王权叙事",
        recommendation_reason="证据线更清楚。",
        next_action="补王室财政材料",
    )

    new_map = versioner.next_version(
        previous=old_map,
        tree=old_map.tree,
        input_capture_ids=[],
        input_chunk_ids=[],
        evidence_ids=[],
        text_view=text_view,
    )

    assert new_map.text_view == text_view


def test_next_version_copies_input_lists():
    versioner = KnowledgeMapVersioner()
    old_map = make_map(1, TreeNode(id="node_1", label="用户认为欧洲王室亲缘密集", kind="concept"))
    input_capture_ids = ["cap_1"]
    input_chunk_ids = ["chunk_1"]
    evidence_ids = ["ev_1"]

    new_map = versioner.next_version(
        previous=old_map,
        tree=old_map.tree,
        input_capture_ids=input_capture_ids,
        input_chunk_ids=input_chunk_ids,
        evidence_ids=evidence_ids,
    )
    input_capture_ids.append("cap_2")
    input_chunk_ids.append("chunk_2")
    evidence_ids.append("ev_2")

    assert new_map.input_capture_ids == ["cap_1"]
    assert new_map.input_chunk_ids == ["chunk_1"]
    assert new_map.evidence_ids == ["ev_1"]


def test_diff_reports_added_and_removed_nodes():
    versioner = KnowledgeMapVersioner()
    before = make_map_with_children(
        1,
        [
            TreeNode(id="node_keep", label="保留节点", kind="concept"),
            TreeNode(id="node_removed", label="删除节点", kind="concept"),
        ],
    )
    after = make_map_with_children(
        2,
        [
            TreeNode(id="node_keep", label="保留节点", kind="concept"),
            TreeNode(id="node_added", label="新增节点", kind="concept"),
        ],
    )

    diff = versioner.diff(before, after)

    assert diff["added_nodes"] == ["node_added"]
    assert diff["removed_nodes"] == ["node_removed"]


def test_diff_reports_nested_node_changes():
    versioner = KnowledgeMapVersioner()
    before = make_map(
        1,
        TreeNode(
            id="node_parent",
            label="航海叙事",
            kind="concept",
            children=[TreeNode(id="node_child", label="哥伦布获得王室支持", kind="concept", confidence="hypothesis")],
        ),
    )
    after = make_map(
        2,
        TreeNode(
            id="node_parent",
            label="航海叙事",
            kind="concept",
            children=[TreeNode(id="node_child", label="哥伦布获得王室支持", kind="concept", confidence="fact")],
        ),
    )

    diff = versioner.diff(before, after)

    assert diff["changed_nodes"][0]["id"] == "node_child"
    assert diff["changed_nodes"][0]["before_confidence"] == "hypothesis"
    assert diff["changed_nodes"][0]["after_confidence"] == "fact"


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
            source_refs=[source_ref("artifact_1", "chunk_1")],
        ),
    )

    diff = versioner.diff(before, after)

    assert diff["changed_nodes"][0]["id"] == "node_1"
    assert diff["changed_nodes"][0]["before_confidence"] == "hypothesis"
    assert diff["changed_nodes"][0]["after_confidence"] == "fact"
    assert diff["changed_nodes"][0]["before_source_ref_count"] == 0
    assert diff["changed_nodes"][0]["after_source_ref_count"] == 1


def test_diff_replaced_source_ref_with_same_count_is_changed():
    versioner = KnowledgeMapVersioner()
    before = make_map(
        1,
        TreeNode(
            id="node_1",
            label="伊莎贝拉一世资助了哥伦布航行",
            kind="concept",
            confidence="fact",
            source_refs=[source_ref("artifact_1", "chunk_1")],
        ),
    )
    after = make_map(
        2,
        TreeNode(
            id="node_1",
            label="伊莎贝拉一世资助了哥伦布航行",
            kind="concept",
            confidence="fact",
            source_refs=[source_ref("artifact_2", "chunk_2")],
        ),
    )

    diff = versioner.diff(before, after)

    assert diff["changed_nodes"][0]["id"] == "node_1"
    assert diff["changed_nodes"][0]["before_source_ref_count"] == 1
    assert diff["changed_nodes"][0]["after_source_ref_count"] == 1


def test_diff_rejects_duplicate_tree_node_ids():
    versioner = KnowledgeMapVersioner()
    before = make_map(
        1,
        TreeNode(
            id="node_1",
            label="王室叙事",
            kind="concept",
            children=[TreeNode(id="node_1", label="重复节点", kind="concept")],
        ),
    )
    after = make_map(2, TreeNode(id="node_1", label="王室叙事", kind="concept"))

    with pytest.raises(ValueError, match="Duplicate tree node id: node_1"):
        versioner.diff(before, after)
