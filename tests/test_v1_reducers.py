import pytest

from manxiang.reducers import reduce_tool_result
from manxiang.storage import JsonStore


def test_reducer_rejects_fact_node_without_source_refs(tmp_path):
    store = JsonStore(tmp_path)

    with pytest.raises(ValueError, match="fact nodes require source_refs"):
        reduce_tool_result(
            store,
            run_id="run_1",
            tool_name="revise_knowledge_map",
            payload={
                "map": {
                    "id": "map_1",
                    "version": 2,
                    "nodes": [
                        {"id": "node_1", "confidence": "fact", "source_refs": []},
                    ],
                }
            },
        )


def test_reducer_accepts_fact_node_with_source_refs(tmp_path):
    store = JsonStore(tmp_path)

    reduce_tool_result(
        store,
        run_id="run_1",
        tool_name="revise_knowledge_map",
        payload={
            "map": {
                "id": "map_1",
                "version": 2,
                "nodes": [
                    {
                        "id": "node_1",
                        "confidence": "fact",
                        "source_refs": [
                            {
                                "artifact_id": "artifact_1",
                                "chunk_id": "chunk_1",
                                "quote": "伊莎贝拉一世资助哥伦布。",
                                "anchor": "text:0-13",
                            }
                        ],
                    },
                ],
            }
        },
    )

    events = store.replay_events("run_1")
    assert events[-1].type == "map.updated"


@pytest.mark.parametrize("source_refs", ["artifact_1", {"artifact_id": "artifact_1"}])
def test_reducer_rejects_fact_node_with_non_list_source_refs(tmp_path, source_refs):
    store = JsonStore(tmp_path)

    with pytest.raises(ValueError, match="fact nodes require source_refs"):
        reduce_tool_result(
            store,
            run_id="run_1",
            tool_name="revise_knowledge_map",
            payload={
                "map": {
                    "id": "map_1",
                    "version": 2,
                    "nodes": [
                        {
                            "id": "node_1",
                            "confidence": "fact",
                            "source_refs": source_refs,
                        }
                    ],
                }
            },
        )


def test_reducer_rejects_map_payload_that_is_not_an_object(tmp_path):
    store = JsonStore(tmp_path)

    with pytest.raises(ValueError, match="map payload must be an object"):
        reduce_tool_result(
            store,
            run_id="run_1",
            tool_name="revise_knowledge_map",
            payload={"map": "not a map"},
        )


def test_reducer_rejects_nodes_that_are_not_a_list(tmp_path):
    store = JsonStore(tmp_path)

    with pytest.raises(ValueError, match="map nodes must be a list"):
        reduce_tool_result(
            store,
            run_id="run_1",
            tool_name="revise_knowledge_map",
            payload={
                "map": {
                    "id": "map_1",
                    "version": 2,
                    "nodes": {"id": "node_1", "confidence": "fact", "source_refs": []},
                }
            },
        )


def test_reducer_rejects_nodes_that_are_not_objects(tmp_path):
    store = JsonStore(tmp_path)

    with pytest.raises(ValueError, match="map nodes must be objects"):
        reduce_tool_result(
            store,
            run_id="run_1",
            tool_name="revise_knowledge_map",
            payload={
                "map": {
                    "id": "map_1",
                    "version": 2,
                    "nodes": ["node_1"],
                }
            },
        )


def test_reducer_accepts_top_level_nodes_payload_with_source_refs(tmp_path):
    store = JsonStore(tmp_path)

    reduce_tool_result(
        store,
        run_id="run_1",
        tool_name="revise_knowledge_map",
        payload={
            "id": "map_1",
            "version": 2,
            "nodes": [
                {
                    "id": "node_1",
                    "confidence": "fact",
                    "source_refs": [
                        {
                            "artifact_id": "artifact_1",
                            "chunk_id": "chunk_1",
                            "quote": "伊莎贝拉一世资助哥伦布。",
                            "anchor": "text:0-13",
                        }
                    ],
                }
            ],
        },
    )

    events = store.replay_events("run_1")
    assert events[-1].type == "map.updated"
    assert events[-1].payload["nodes"][0]["id"] == "node_1"


def test_attach_evidence_rejects_fact_node_without_source_refs_and_writes_no_events(tmp_path):
    store = JsonStore(tmp_path)

    with pytest.raises(ValueError, match="fact nodes require source_refs"):
        reduce_tool_result(
            store,
            run_id="run_1",
            tool_name="attach_evidence",
            payload={
                "evidence": {"id": "evidence_1"},
                "map": {
                    "id": "map_1",
                    "version": 2,
                    "nodes": [
                        {"id": "node_1", "confidence": "fact", "source_refs": []},
                    ],
                },
            },
        )

    assert store.replay_events("run_1") == []
