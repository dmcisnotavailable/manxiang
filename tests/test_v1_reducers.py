import pytest

from manxiang.reducers import reduce_tool_result
from manxiang.storage import JsonStore


@pytest.mark.parametrize(
    ("tool_name", "payload", "event_type", "expected_payload"),
    [
        (
            "create_research_contract",
            {
                "contract": {
                    "task_id": "task_1",
                    "title": "伊莎贝拉研究契约",
                    "goal": "厘清伊莎贝拉资助哥伦布的证据链",
                    "allowed_scope": ["收藏文本", "本地证据块"],
                    "blocked_scope": ["无证据扩写"],
                    "completion_definition": "形成带证据引用的修订地图",
                }
            },
            "research.contract.created",
            {
                "task_id": "task_1",
                "title": "伊莎贝拉研究契约",
                "goal": "厘清伊莎贝拉资助哥伦布的证据链",
                "allowed_scope": ["收藏文本", "本地证据块"],
                "blocked_scope": ["无证据扩写"],
                "completion_definition": "形成带证据引用的修订地图",
            },
        ),
        (
            "request_source_parse",
            {"capture_id": "cap_1", "reason": "需要解析原文来补足 gap_1", "gap_id": "gap_1"},
            "source.parse.requested",
            {"capture_id": "cap_1", "reason": "需要解析原文来补足 gap_1", "gap_id": "gap_1"},
        ),
        (
            "retrieve_evidence_chunks",
            {"gap_id": "gap_1", "query": "伊莎贝拉 哥伦布", "limit": 5},
            "evidence.chunks.retrieve.requested",
            {"gap_id": "gap_1", "query": "伊莎贝拉 哥伦布", "limit": 5},
        ),
        (
            "request_web_search",
            {
                "gap_id": "gap_1",
                "query": "Isabella Columbus patronage",
                "search_goal": "找到伊莎贝拉资助哥伦布的可靠证据",
                "stop_condition": "找到两个可靠来源后停止",
                "max_results": 3,
            },
            "web.search.requested",
            {
                "gap_id": "gap_1",
                "query": "Isabella Columbus patronage",
                "search_goal": "找到伊莎贝拉资助哥伦布的可靠证据",
                "stop_condition": "找到两个可靠来源后停止",
                "max_results": 3,
            },
        ),
    ],
)
def test_reducer_records_v1_request_tool_events(tmp_path, tool_name, payload, event_type, expected_payload):
    store = JsonStore(tmp_path)

    reduce_tool_result(store, run_id="run_1", tool_name=tool_name, payload=payload)

    events = store.replay_events("run_1")
    assert events[-1].type == event_type
    assert events[-1].payload == expected_payload


def test_reducer_rejects_fact_node_without_source_refs(tmp_path):
    store = JsonStore(tmp_path)

    with pytest.raises(ValueError, match="fact nodes require valid source_refs"):
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


@pytest.mark.parametrize(
    "source_refs",
    [
        "artifact_1",
        {"artifact_id": "artifact_1"},
        ["src_1"],
        [{"artifact_id": "artifact_1", "chunk_id": "chunk_1", "quote": "引用文本", "anchor": ""}],
        [{"artifact_id": "artifact_1", "chunk_id": "chunk_1", "quote": "", "anchor": "text:0-4"}],
        [{"artifact_id": "artifact_1", "chunk_id": "chunk_1", "anchor": "text:0-4"}],
    ],
)
def test_reducer_rejects_fact_node_with_invalid_source_refs(tmp_path, source_refs):
    store = JsonStore(tmp_path)

    with pytest.raises(ValueError, match="fact nodes require valid source_refs"):
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

    with pytest.raises(ValueError, match="fact nodes require valid source_refs"):
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
