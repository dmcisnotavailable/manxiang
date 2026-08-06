from manxiang.schema import CaptureItem, SourceArtifact, SourceChunk
from manxiang.sqlite_store import SQLiteStore


def test_sqlite_store_saves_and_lists_captures(tmp_path):
    store = SQLiteStore(tmp_path / "manxiang.sqlite3", clock=lambda: "2026-08-06T10:00:00+08:00")
    capture = CaptureItem(
        id="cap_1",
        type="text",
        source="manual",
        user_note="王室亲缘这件事感觉能串起来",
        captured_at="2026-08-06T10:00:00+08:00",
        original_text="伊莎贝拉和伊丽莎白两个著名的女王有血缘关系。",
    )

    store.save_capture(capture)

    captures = store.list_captures()
    assert len(captures) == 1
    assert captures[0].id == "cap_1"
    assert captures[0].original_text.startswith("伊莎贝拉")


def test_sqlite_store_saves_sources_chunks_and_events(tmp_path):
    store = SQLiteStore(tmp_path / "manxiang.sqlite3", clock=lambda: "2026-08-06T10:00:00+08:00")
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
        id="chunk_1",
        artifact_id="artifact_1",
        text="伊莎贝拉一世资助了哥伦布。",
        start_offset=0,
        end_offset=13,
        anchor="text:0-13",
        embedding_status="not_embedded",
        created_at="2026-08-06T10:00:00+08:00",
    )

    store.save_source_artifact(artifact)
    store.save_source_chunk(chunk)
    event_1 = store.append_event("run_1", "source.artifact.created", {"artifact_id": "artifact_1"})
    event_2 = store.append_event("run_1", "source.chunk.created", {"chunk": chunk})
    other_run_event = store.append_event("run_2", "source.chunk.created", {"chunk_id": "chunk_1"})

    saved_artifact = store.get_source_artifact("artifact_1")
    assert saved_artifact is not None
    assert saved_artifact.id == "artifact_1"
    assert saved_artifact.capture_id == "cap_1"
    assert saved_artifact.uri == "manual://cap_1"
    assert saved_artifact.parse_status == "parsed"
    assert store.list_source_chunks("artifact_1")[0].id == "chunk_1"

    run_1_events = store.replay_events("run_1")
    assert [event.seq for event in run_1_events] == [1, 2]
    assert store.replay_events("run_1", after_seq=1) == [run_1_events[1]]
    assert store.replay_events("run_2") == [other_run_event]
    assert run_1_events[0].id == event_1.id
    assert run_1_events[1].id == event_2.id
    assert run_1_events[1].payload["chunk"]["id"] == "chunk_1"
    assert run_1_events[1].payload["chunk"]["artifact_id"] == "artifact_1"
