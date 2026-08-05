from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from manxiang.schema import (
    CaptureItem,
    EvidenceItem,
    KnowledgeMap,
    ParkingLotItem,
    ResearchTask,
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
        )

    def _tree_from_row(self, row: dict[str, Any]) -> TreeNode:
        return TreeNode(
            id=row["id"],
            label=row["label"],
            kind=row["kind"],
            children=[self._tree_from_row(child) for child in row.get("children", [])],
        )
