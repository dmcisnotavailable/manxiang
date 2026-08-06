from manxiang.schema import (
    KnowledgeMap,
    SourceArtifact,
    SourceChunk,
    SourceRef,
    TextView,
    TreeNode,
)


def test_source_chunk_keeps_traceable_anchor():
    artifact = SourceArtifact(
        id="artifact_1",
        capture_id="cap_1",
        source_type="text",
        uri="manual://cap_1",
        content_hash="hash_abc",
        parse_status="parsed",
        parser_name="plain_text",
        parser_version="v1",
        created_at="2026-08-06T10:00:00+08:00",
    )
    chunk = SourceChunk(
        id=artifact.id.replace("artifact", "chunk"),
        artifact_id=artifact.id,
        text="伊莎贝拉一世资助了哥伦布的航行。",
        start_offset=0,
        end_offset=18,
        anchor="text:0-18",
        embedding_status="not_embedded",
        created_at="2026-08-06T10:00:00+08:00",
    )

    assert chunk.artifact_id == "artifact_1"
    assert chunk.anchor == "text:0-18"
    assert chunk.embedding_status == "not_embedded"


def test_tree_node_can_carry_confidence_and_source_refs():
    ref = SourceRef(
        artifact_id="artifact_1",
        chunk_id="chunk_1",
        quote="伊莎贝拉一世资助了哥伦布的航行。",
        anchor="text:0-18",
    )
    node = TreeNode(
        id="node_1",
        label="伊莎贝拉和哥伦布的关系需要证据确认",
        kind="evidence",
        confidence="fact",
        source_refs=[ref],
    )

    assert node.confidence == "fact"
    assert node.source_refs[0].chunk_id == "chunk_1"


def test_knowledge_map_records_generation_inputs():
    knowledge_map = KnowledgeMap(
        task_id="task_1",
        version=2,
        text_view=TextView(
            core_question="西班牙王室叙事如何连接亲缘、艺术和航海？",
            mainline_summary="亲缘误读 -> 王室图像 -> 航海扩张",
            recommendation_reason="当前材料最适合用问题线组织。",
            next_action="核验证据缺口 gap_genealogy",
        ),
        tree=TreeNode(id="root", label="西班牙王权叙事", kind="root"),
        input_capture_ids=["cap_1", "cap_2"],
        input_chunk_ids=["chunk_1"],
        evidence_ids=["ev_1"],
    )

    assert knowledge_map.version == 2
    assert knowledge_map.input_chunk_ids == ["chunk_1"]
    assert knowledge_map.evidence_ids == ["ev_1"]
