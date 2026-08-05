from manxiang.events import StateEvent
from manxiang.storage import JsonStore


def test_store_appends_events_and_replays_by_seq(tmp_path):
    store = JsonStore(tmp_path)

    first = store.append_event(run_id="run_1", event_type="run.started", payload={})
    second = store.append_event(run_id="run_1", event_type="spark.card.created", payload={"id": "spark_1"})

    assert first.seq == 1
    assert second.seq == 2
    assert [event.type for event in store.replay_events("run_1", after_seq=0)] == [
        "run.started",
        "spark.card.created",
    ]
    assert [event.type for event in store.replay_events("run_1", after_seq=1)] == ["spark.card.created"]


def test_checkpoint_is_written_for_event(tmp_path):
    store = JsonStore(tmp_path)

    event = store.append_event(run_id="run_1", event_type="map.created", payload={"map_id": "map_1"})
    checkpoints = store.list_checkpoints("run_1")

    assert isinstance(event, StateEvent)
    assert checkpoints[-1]["seq"] == event.seq
    assert checkpoints[-1]["run_id"] == "run_1"
