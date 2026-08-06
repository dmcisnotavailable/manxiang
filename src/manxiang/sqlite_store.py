from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable

from manxiang.events import make_event_id
from manxiang.schema import CaptureItem, SourceArtifact, SourceChunk, StateEvent


class SQLiteStore:
    def __init__(self, db_path: str | Path, clock: Callable[[], str]):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self._init_schema()

    def save_capture(self, item: CaptureItem) -> None:
        self._upsert_json("captures", item.id, item)

    def list_captures(self) -> list[CaptureItem]:
        return [CaptureItem(**row) for row in self._list_json("captures")]

    def save_source_artifact(self, artifact: SourceArtifact) -> None:
        self._upsert_json("source_artifacts", artifact.id, artifact)

    def get_source_artifact(self, artifact_id: str) -> SourceArtifact | None:
        row = self._get_json("source_artifacts", artifact_id)
        return SourceArtifact(**row) if row else None

    def save_source_chunk(self, chunk: SourceChunk) -> None:
        self._upsert_json("source_chunks", chunk.id, chunk)

    def list_source_chunks(self, artifact_id: str) -> list[SourceChunk]:
        rows = self._list_json("source_chunks")
        return [SourceChunk(**row) for row in rows if row["artifact_id"] == artifact_id]

    def append_event(self, run_id: str, event_type: str, payload: dict) -> StateEvent:
        with self._connect() as conn:
            seq = self._next_seq(conn)
            event = StateEvent(
                id=make_event_id(run_id, seq, event_type),
                seq=seq,
                run_id=run_id,
                type=event_type,
                payload=payload,
                created_at=self.clock(),
            )
            conn.execute(
                "insert into events(id, seq, run_id, type, payload, created_at) values (?, ?, ?, ?, ?, ?)",
                (event.id, event.seq, event.run_id, event.type, json.dumps(payload, ensure_ascii=False), event.created_at),
            )
            return event

    def replay_events(self, run_id: str, after_seq: int = 0) -> list[StateEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                "select id, seq, run_id, type, payload, created_at from events where run_id = ? and seq > ? order by seq",
                (run_id, after_seq),
            ).fetchall()
        return [
            StateEvent(
                id=row["id"],
                seq=int(row["seq"]),
                run_id=row["run_id"],
                type=row["type"],
                payload=json.loads(row["payload"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("create table if not exists kv(table_name text not null, id text not null, payload text not null, primary key(table_name, id))")
            conn.execute("create table if not exists event_seq(id integer primary key check (id = 1), seq integer not null)")
            conn.execute("insert or ignore into event_seq(id, seq) values (1, 0)")
            conn.execute("create table if not exists events(id text primary key, seq integer not null, run_id text not null, type text not null, payload text not null, created_at text not null)")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _upsert_json(self, table_name: str, item_id: str, item: Any) -> None:
        payload = json.dumps(self._to_jsonable(item), ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                "insert into kv(table_name, id, payload) values (?, ?, ?) on conflict(table_name, id) do update set payload = excluded.payload",
                (table_name, item_id, payload),
            )

    def _get_json(self, table_name: str, item_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "select payload from kv where table_name = ? and id = ?",
                (table_name, item_id),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def _list_json(self, table_name: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "select payload from kv where table_name = ? order by id",
                (table_name,),
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def _next_seq(self, conn: sqlite3.Connection) -> int:
        row = conn.execute("select seq from event_seq where id = 1").fetchone()
        seq = int(row["seq"]) + 1
        conn.execute("update event_seq set seq = ? where id = 1", (seq,))
        return seq

    def _to_jsonable(self, value: Any) -> Any:
        if is_dataclass(value):
            return {key: self._to_jsonable(item) for key, item in asdict(value).items()}
        if isinstance(value, list):
            return [self._to_jsonable(item) for item in value]
        if isinstance(value, dict):
            return {key: self._to_jsonable(item) for key, item in value.items()}
        return value
