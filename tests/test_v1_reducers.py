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
