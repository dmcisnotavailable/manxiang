from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from manxiang.events import StateEvent, make_event_id
from manxiang.schema import (
    CaptureItem,
    EvidenceItem,
    KnowledgeMap,
    ParkingLotItem,
    ResearchTask,
    SourceRef,
    TextView,
    TopicCluster,
    TreeNode,
)


class JsonStore:
    """Small local JSON store for the MVP.

    This is intentionally simple. It gives us persistence without introducing a
    database before the core workflow is proven.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_capture(self, item: CaptureItem) -> None:
        self._upsert("captures.json", item.id, item)

    def list_captures(self) -> list[CaptureItem]:
        return [CaptureItem(**row) for row in self._read_many("captures.json")]

    def save_topic(self, item: TopicCluster) -> None:
        self._upsert("topics.json", item.id, item)

    def list_topics(self) -> list[TopicCluster]:
        return [TopicCluster(**row) for row in self._read_many("topics.json")]

    def save_task(self, item: ResearchTask) -> None:
        self._upsert("tasks.json", item.id, item)

    def list_tasks(self) -> list[ResearchTask]:
        return [ResearchTask(**row) for row in self._read_many("tasks.json")]

    def save_map(self, item: KnowledgeMap) -> None:
        key = f"{item.task_id}:{item.version}"
        self._upsert("maps.json", key, item, key_field="_key")

    def list_maps(self) -> list[KnowledgeMap]:
        rows = self._read_many("maps.json")
        return [self._map_from_row(row) for row in rows]

    def save_evidence(self, item: EvidenceItem) -> None:
        self._upsert("evidence.json", item.id, item)

    def list_evidence(self) -> list[EvidenceItem]:
        return [EvidenceItem(**row) for row in self._read_many("evidence.json")]

    def save_parking_item(self, item: ParkingLotItem) -> None:
        self._upsert("parking.json", item.id, item)

    def list_parking_items(self) -> list[ParkingLotItem]:
        return [ParkingLotItem(**row) for row in self._read_many("parking.json")]

    def append_event(self, run_id: str, event_type: str, payload: dict) -> StateEvent:
        seq = self._next_event_seq()
        event = StateEvent(
            id=make_event_id(run_id, seq, event_type),
            seq=seq,
            run_id=run_id,
            type=event_type,
            payload=payload,
            created_at=self._event_time(),
        )
        with self._path("events.jsonl").open("a", encoding="utf-8") as file:
            file.write(json.dumps(self._to_jsonable(event), ensure_ascii=False) + "\n")
        self._append_checkpoint(run_id=run_id, seq=seq, pointer="events.jsonl")
        return event

    def replay_events(self, run_id: str, after_seq: int = 0) -> list[StateEvent]:
        path = self._path("events.jsonl")
        if not path.exists():
            return []

        events: list[StateEvent] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row["run_id"] == run_id and row["seq"] > after_seq:
                events.append(StateEvent(**row))
        return sorted(events, key=lambda event: event.seq)

    def list_checkpoints(self, run_id: str) -> list[dict]:
        return [row for row in self._read_many("checkpoints.json") if row["run_id"] == run_id]

    def _path(self, filename: str) -> Path:
        return self.root / filename

    def _read_many(self, filename: str) -> list[dict[str, Any]]:
        path = self._path(filename)
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_many(self, filename: str, rows: list[dict[str, Any]]) -> None:
        self._path(filename).write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _upsert(self, filename: str, item_id: str, item: Any, key_field: str = "id") -> None:
        rows = self._read_many(filename)
        payload = self._to_jsonable(item)
        payload[key_field] = item_id
        kept = [row for row in rows if row.get(key_field) != item_id]
        kept.append(payload)
        self._write_many(filename, kept)

    def _next_event_seq(self) -> int:
        path = self._path("event_seq.json")
        if not path.exists():
            path.write_text(json.dumps({"seq": 0}), encoding="utf-8")
        row = json.loads(path.read_text(encoding="utf-8"))
        row["seq"] += 1
        path.write_text(json.dumps(row), encoding="utf-8")
        return int(row["seq"])

    def _append_checkpoint(self, run_id: str, seq: int, pointer: str) -> None:
        rows = self._read_many("checkpoints.json")
        rows.append(
            {
                "checkpoint_id": f"ckpt_{run_id}_{seq}",
                "run_id": run_id,
                "seq": seq,
                "pointer": pointer,
                "created_at": self._event_time(),
            }
        )
        self._write_many("checkpoints.json", rows)

    def _event_time(self) -> str:
        return "2026-08-05T20:00:00+08:00"

    def _to_jsonable(self, value: Any) -> Any:
        if is_dataclass(value):
            return {key: self._to_jsonable(item) for key, item in asdict(value).items()}
        if isinstance(value, list):
            return [self._to_jsonable(item) for item in value]
        if isinstance(value, dict):
            return {key: self._to_jsonable(item) for key, item in value.items()}
        return value

    def _map_from_row(self, row: dict[str, Any]) -> KnowledgeMap:
        clean = {key: value for key, value in row.items() if key != "_key"}
        return KnowledgeMap(
            task_id=clean["task_id"],
            version=int(clean["version"]),
            text_view=TextView(**clean["text_view"]),
            tree=self._tree_from_row(clean["tree"]),
            input_capture_ids=list(clean.get("input_capture_ids", [])),
            input_chunk_ids=list(clean.get("input_chunk_ids", [])),
            evidence_ids=list(clean.get("evidence_ids", [])),
        )

    def _tree_from_row(self, row: dict[str, Any]) -> TreeNode:
        return TreeNode(
            id=row["id"],
            label=row["label"],
            kind=row["kind"],
            children=[self._tree_from_row(child) for child in row.get("children", [])],
            confidence=row.get("confidence", "hypothesis"),
            source_refs=[
                ref if isinstance(ref, SourceRef) else SourceRef(**ref)
                for ref in row.get("source_refs", [])
            ],
        )
