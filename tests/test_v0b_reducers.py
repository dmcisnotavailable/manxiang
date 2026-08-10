import pytest

from manxiang.reducers import reduce_tool_result
from manxiang.storage import JsonStore


def test_reducer_persists_spark_card_event(tmp_path):
    store = JsonStore(tmp_path)

    reduce_tool_result(
        store,
        run_id="run_1",
        tool_name="generate_spark_cards",
        payload={
            "spark_cards": [
                {
                    "id": "spark_1",
                    "title": "一张王室世系图，把线索串起来了",
                    "source_capture_ids": ["cap_1", "cap_5"],
                }
            ]
        },
    )

    assert store.replay_events("run_1")[0].type == "spark.card.created"


def test_reducer_rejects_fact_in_map_v1(tmp_path):
    store = JsonStore(tmp_path)

    with pytest.raises(ValueError, match="KnowledgeMap v1 cannot create fact nodes"):
        reduce_tool_result(
            store,
            run_id="run_1",
            tool_name="generate_knowledge_map",
            payload={
                "map": {
                    "version": 1,
                    "nodes": [{"id": "node_1", "confidence": "fact"}],
                }
            },
        )
