# Manxiang v1 Agent Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade Manxiang from the current V0b demo into a v1 evidence-driven research Agent with repository boundaries, source chunks, RAG retrieval, map versioning, guardrailed tool execution, and automated evaluation.

**Architecture:** Keep the current Python package as the trusted product core and keep the TypeScript Pi Agent bridge as the LLM/tool runtime. Add repository interfaces plus a SQLite implementation next to the existing `JsonStore`, then route v1 source parsing, retrieval, map versioning, and evals through small focused modules. The LLM proposes structured tool outputs; Python guardrails and reducers decide whether those outputs can become durable state.

**Tech Stack:** Python 3.11 via `uv`, pytest, dataclasses, sqlite3, JSONL event log, local keyword retrieval, TypeScript, Pi Agent Core, TypeBox, Node.js 22.

---

## Scope Check

This plan follows the approved v1 design in `docs/superpowers/specs/2026-08-06-manxiang-v1-agent-upgrade-design.md`.

The v1 design contains several subsystems, but they are not independent products. They form one sequential Agent engineering upgrade:

```text
models -> repository -> source chunks -> retrieval -> map versions -> run state -> tools -> workbench -> evals
```

Each task below is independently testable and should be committed before moving to the next task.

## Target File Structure

### New Python Files

```text
src/manxiang/repositories.py       # Repository protocols and small shared query types
src/manxiang/sqlite_store.py       # SQLite implementation for captures, sources, maps, events, checkpoints
src/manxiang/source_parser.py      # Just-in-time parsing from CaptureItem to SourceArtifact/SourceChunk
src/manxiang/retrieval.py          # Keyword retrieval and reranking over SourceChunk
src/manxiang/map_versions.py       # KnowledgeMap version creation and diff
src/manxiang/run_state.py          # v1 run stage transitions and autonomy checks
src/manxiang/evals.py              # Rubric scoring helpers used by eval runner and tests
```

### Modified Python Files

```text
src/manxiang/schema.py             # Add v1 source, citation, map, checkpoint, and eval dataclasses
src/manxiang/reducers.py           # Reject fact nodes without source_refs; persist v1 map/evidence events
src/manxiang/guardrails.py         # Extend policy to source parsing, retrieval, and web search tools
src/manxiang/runs.py               # Add v1 research run helpers without breaking V0b surprise flow
src/manxiang/workbench.py          # Expose v1 state for demo
src/manxiang/web.py                # Add v1 endpoints while preserving existing routes
README.md                          # Add v1 commands and demo script
```

### Modified TypeScript Files

```text
piagent/tools.ts                   # Add v1 tool schemas
piagent/prompts.ts                 # Add v1 stage and citation rules
piagent/types.ts                   # Add v1 bridge payload types
```

### New Tests

```text
tests/test_v1_schema.py
tests/test_v1_sqlite_store.py
tests/test_v1_source_parser.py
tests/test_v1_retrieval.py
tests/test_v1_map_versions.py
tests/test_v1_guardrails.py
tests/test_v1_reducers.py
tests/test_v1_run_state.py
tests/test_v1_workbench.py
tests/test_v1_evals.py
```

### New Eval Assets

```text
evals/manxiang/cases/spanish_royal_family.json
evals/manxiang/rubrics/research_map.json
evals/manxiang/run_eval.py
evals/manxiang/reports/.gitkeep
```

## Task 1: Add v1 Domain Models

**Why:** 面试官最容易追问“你怎么区分用户印象、证据、事实”。这一任务先把类型边界立住。

**Files:**
- Modify: `src/manxiang/schema.py`
- Test: `tests/test_v1_schema.py`

- [ ] **Step 1: Write the failing schema tests**

Create `tests/test_v1_schema.py`:

```python
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
        id="chunk_1",
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
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
uv run pytest tests/test_v1_schema.py -q
```

Expected: FAIL with import errors for `SourceArtifact`, `SourceChunk`, and `SourceRef`.

- [ ] **Step 3: Add v1 source and citation types**

Modify `src/manxiang/schema.py` by adding these literals near the existing literal definitions:

```python
SourceParseStatus = Literal["not_parsed", "parse_requested", "parsed", "parse_failed", "parse_skipped"]
EmbeddingStatus = Literal["not_embedded", "embedded", "embedding_failed"]
NodeConfidence = Literal["user_impression", "hypothesis", "needs_evidence", "fact"]
CheckpointStage = Literal[
    "captured",
    "topic_discovered",
    "research_scoped",
    "map_drafted",
    "evidence_patched",
    "map_reviewed",
]
```

Append these dataclasses after `StateEvent`:

```python
@dataclass(frozen=True)
class SourceArtifact:
    id: str
    capture_id: str
    source_type: SourceType
    uri: str
    content_hash: str
    parse_status: SourceParseStatus
    parser_name: str
    parser_version: str
    created_at: str


@dataclass(frozen=True)
class SourceChunk:
    id: str
    artifact_id: str
    text: str
    start_offset: int
    end_offset: int
    anchor: str
    embedding_status: EmbeddingStatus
    created_at: str


@dataclass(frozen=True)
class SourceRef:
    artifact_id: str
    chunk_id: str
    quote: str
    anchor: str


@dataclass(frozen=True)
class Checkpoint:
    id: str
    run_id: str
    stage: CheckpointStage
    seq: int
    state_hash: str
    restore_pointer: str
    created_at: str
```

- [ ] **Step 4: Extend `TreeNode` and `KnowledgeMap` with defaults**

Replace the current `TreeNode` and `KnowledgeMap` dataclasses in `src/manxiang/schema.py` with:

```python
@dataclass(frozen=True)
class TreeNode:
    id: str
    label: str
    kind: NodeKind
    children: list["TreeNode"] = field(default_factory=list)
    confidence: NodeConfidence = "hypothesis"
    source_refs: list[SourceRef] = field(default_factory=list)


@dataclass(frozen=True)
class KnowledgeMap:
    task_id: str
    version: int
    text_view: TextView
    tree: TreeNode
    input_capture_ids: list[str] = field(default_factory=list)
    input_chunk_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
```

Why this is safe: the new fields have defaults, so existing V0b code that constructs `TreeNode` and `KnowledgeMap` still works.

- [ ] **Step 5: Run schema tests**

Run:

```bash
uv run pytest tests/test_v1_schema.py -q
```

Expected: PASS.

- [ ] **Step 6: Run existing map and storage tests**

Run:

```bash
uv run pytest tests/test_manxiang_maps.py tests/test_manxiang_storage.py -q
```

Expected: PASS. This proves the v1 fields did not break V0b builders and JSON serialization.

- [ ] **Step 7: Commit**

```bash
git add src/manxiang/schema.py tests/test_v1_schema.py
git commit -m "feat: add v1 source and map schema"
```

## Task 2: Introduce Repository Interfaces And SQLite Store

**Why:** `JsonStore` 适合 Demo，但 v1 要能讲清楚“业务状态”和“事件日志”的边界。SQLite 存当前快照，JSONL/事件表保历史。

**Files:**
- Create: `src/manxiang/repositories.py`
- Create: `src/manxiang/sqlite_store.py`
- Test: `tests/test_v1_sqlite_store.py`

- [ ] **Step 1: Write failing repository tests**

Create `tests/test_v1_sqlite_store.py`:

```python
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
    event = store.append_event("run_1", "source.chunk.created", {"chunk_id": "chunk_1"})

    assert store.list_source_chunks("artifact_1")[0].id == "chunk_1"
    assert store.replay_events("run_1")[0].id == event.id
    assert store.replay_events("run_1")[0].payload == {"chunk_id": "chunk_1"}
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
uv run pytest tests/test_v1_sqlite_store.py -q
```

Expected: FAIL because `manxiang.sqlite_store` does not exist.

- [ ] **Step 3: Add repository protocols**

Create `src/manxiang/repositories.py`:

```python
from __future__ import annotations

from typing import Protocol

from manxiang.schema import CaptureItem, SourceArtifact, SourceChunk, StateEvent


class CaptureRepository(Protocol):
    def save_capture(self, item: CaptureItem) -> None:
        raise NotImplementedError

    def list_captures(self) -> list[CaptureItem]:
        raise NotImplementedError


class SourceRepository(Protocol):
    def save_source_artifact(self, artifact: SourceArtifact) -> None:
        raise NotImplementedError

    def save_source_chunk(self, chunk: SourceChunk) -> None:
        raise NotImplementedError

    def list_source_chunks(self, artifact_id: str) -> list[SourceChunk]:
        raise NotImplementedError


class EventRepository(Protocol):
    def append_event(self, run_id: str, event_type: str, payload: dict) -> StateEvent:
        raise NotImplementedError

    def replay_events(self, run_id: str, after_seq: int = 0) -> list[StateEvent]:
        raise NotImplementedError
```

- [ ] **Step 4: Add SQLiteStore**

Create `src/manxiang/sqlite_store.py`:

```python
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
```

- [ ] **Step 5: Run SQLite tests**

Run:

```bash
uv run pytest tests/test_v1_sqlite_store.py -q
```

Expected: PASS.

- [ ] **Step 6: Run existing storage tests**

Run:

```bash
uv run pytest tests/test_manxiang_storage.py tests/test_v0b_events.py -q
```

Expected: PASS. This proves v1 storage was added without breaking `JsonStore`.

- [ ] **Step 7: Commit**

```bash
git add src/manxiang/repositories.py src/manxiang/sqlite_store.py tests/test_v1_sqlite_store.py
git commit -m "feat: add sqlite repository store"
```

## Task 3: Add Just-In-Time Source Parsing

**Why:** v1 的“延迟解析”要落到代码。收藏阶段只保存来源；研究阶段出现证据缺口后，才把相关来源解析成 chunk。

**Files:**
- Create: `src/manxiang/source_parser.py`
- Test: `tests/test_v1_source_parser.py`

- [ ] **Step 1: Write failing parser tests**

Create `tests/test_v1_source_parser.py`:

```python
from manxiang.schema import CaptureItem
from manxiang.source_parser import SourceParser


def test_parse_text_capture_to_artifact_and_chunks():
    parser = SourceParser(clock=lambda: "2026-08-06T10:00:00+08:00", chunk_size=12, overlap=4)
    capture = CaptureItem(
        id="cap_1",
        type="text",
        source="manual",
        user_note="感觉伊莎贝拉和哥伦布能串起来",
        captured_at="2026-08-06T10:00:00+08:00",
        original_text="伊莎贝拉一世资助了哥伦布的航行。普拉多博物馆里有很多王室叙事画作。",
    )

    artifact, chunks = parser.parse_capture(capture)

    assert artifact.capture_id == "cap_1"
    assert artifact.parse_status == "parsed"
    assert artifact.uri == "manual://cap_1"
    assert chunks
    assert chunks[0].artifact_id == artifact.id
    assert chunks[0].anchor.startswith("text:")


def test_parse_url_capture_uses_light_summary_without_fetching_full_page():
    parser = SourceParser(clock=lambda: "2026-08-06T10:00:00+08:00", chunk_size=24, overlap=6)
    capture = CaptureItem(
        id="cap_url",
        type="url",
        source="https://example.com/article",
        user_note="这条新闻可能和王室叙事有关",
        captured_at="2026-08-06T10:00:00+08:00",
        source_type="url",
        source_uri="https://example.com/article",
        ai_summary_draft="网页标题提到西班牙王室和艺术收藏。",
        parse_status="metadata_parsed",
    )

    artifact, chunks = parser.parse_capture(capture)

    assert artifact.uri == "https://example.com/article"
    assert chunks[0].text == "网页标题提到西班牙王室和艺术收藏。"
```

- [ ] **Step 2: Run parser tests and verify they fail**

Run:

```bash
uv run pytest tests/test_v1_source_parser.py -q
```

Expected: FAIL because `manxiang.source_parser` does not exist.

- [ ] **Step 3: Implement `SourceParser`**

Create `src/manxiang/source_parser.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from hashlib import sha1

from manxiang.schema import CaptureItem, SourceArtifact, SourceChunk


class SourceParser:
    def __init__(self, clock: Callable[[], str], chunk_size: int = 500, overlap: int = 80):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be >= 0 and smaller than chunk_size")
        self.clock = clock
        self.chunk_size = chunk_size
        self.overlap = overlap

    def parse_capture(self, capture: CaptureItem) -> tuple[SourceArtifact, list[SourceChunk]]:
        text = self._text_for(capture)
        artifact_id = self._artifact_id(capture.id, text)
        artifact = SourceArtifact(
            id=artifact_id,
            capture_id=capture.id,
            source_type=capture.source_type,
            uri=self._uri_for(capture),
            content_hash=sha1(text.encode("utf-8")).hexdigest(),
            parse_status="parsed" if text else "parse_failed",
            parser_name="jit_plain_text",
            parser_version="v1",
            created_at=self.clock(),
        )
        chunks = self._chunks_for(artifact_id, text)
        return artifact, chunks

    def _text_for(self, capture: CaptureItem) -> str:
        candidates = [
            capture.original_text,
            capture.raw_text,
            capture.user_summary,
            capture.ai_summary_draft,
            capture.user_note,
        ]
        for candidate in candidates:
            if candidate.strip():
                return candidate.strip()
        return ""

    def _uri_for(self, capture: CaptureItem) -> str:
        if capture.source_uri:
            return capture.source_uri
        if capture.source_type == "text":
            return f"manual://{capture.id}"
        return capture.source

    def _chunks_for(self, artifact_id: str, text: str) -> list[SourceChunk]:
        if not text:
            return []
        chunks: list[SourceChunk] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + self.chunk_size)
            chunk_text = text[start:end]
            chunk_id = self._chunk_id(artifact_id, start, end, chunk_text)
            chunks.append(
                SourceChunk(
                    id=chunk_id,
                    artifact_id=artifact_id,
                    text=chunk_text,
                    start_offset=start,
                    end_offset=end,
                    anchor=f"text:{start}-{end}",
                    embedding_status="not_embedded",
                    created_at=self.clock(),
                )
            )
            if end == len(text):
                break
            start = end - self.overlap
        return chunks

    def _artifact_id(self, capture_id: str, text: str) -> str:
        digest = sha1(f"{capture_id}|{text}".encode("utf-8")).hexdigest()[:12]
        return f"artifact_{digest}"

    def _chunk_id(self, artifact_id: str, start: int, end: int, text: str) -> str:
        digest = sha1(f"{artifact_id}|{start}|{end}|{text}".encode("utf-8")).hexdigest()[:12]
        return f"chunk_{digest}"
```

- [ ] **Step 4: Run parser tests**

Run:

```bash
uv run pytest tests/test_v1_source_parser.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/manxiang/source_parser.py tests/test_v1_source_parser.py
git commit -m "feat: add just in time source parser"
```

## Task 4: Add Local Retrieval And Reranking

**Why:** v1 需要真正能讲 RAG。这里先做可解释的关键词检索，再保留向量接口位置。关键词检索适合第一版，因为它稳定、可测试、容易面试讲清楚。

**Files:**
- Create: `src/manxiang/retrieval.py`
- Test: `tests/test_v1_retrieval.py`

- [ ] **Step 1: Write failing retrieval tests**

Create `tests/test_v1_retrieval.py`:

```python
from manxiang.retrieval import KeywordRetriever
from manxiang.schema import SourceChunk


def chunk(chunk_id: str, text: str) -> SourceChunk:
    return SourceChunk(
        id=chunk_id,
        artifact_id="artifact_1",
        text=text,
        start_offset=0,
        end_offset=len(text),
        anchor=f"text:{chunk_id}",
        embedding_status="not_embedded",
        created_at="2026-08-06T10:00:00+08:00",
    )


def test_keyword_retriever_returns_ranked_chunks():
    retriever = KeywordRetriever()
    chunks = [
        chunk("chunk_1", "普拉多博物馆收藏了大量西班牙王室相关画作。"),
        chunk("chunk_2", "伊莎贝拉一世资助哥伦布远航，开启大航海叙事。"),
        chunk("chunk_3", "这是一段和主题无关的文字。"),
    ]

    results = retriever.retrieve("伊莎贝拉 哥伦布 王室", chunks, limit=2)

    assert [result.chunk.id for result in results] == ["chunk_2", "chunk_1"]
    assert results[0].score > results[1].score


def test_keyword_retriever_filters_zero_score_chunks():
    retriever = KeywordRetriever()
    chunks = [chunk("chunk_1", "完全无关的内容")]

    assert retriever.retrieve("伊莎贝拉 哥伦布", chunks, limit=3) == []
```

- [ ] **Step 2: Run retrieval tests and verify they fail**

Run:

```bash
uv run pytest tests/test_v1_retrieval.py -q
```

Expected: FAIL because `manxiang.retrieval` does not exist.

- [ ] **Step 3: Implement KeywordRetriever**

Create `src/manxiang/retrieval.py`:

```python
from __future__ import annotations

import re
from dataclasses import dataclass

from manxiang.schema import SourceChunk


@dataclass(frozen=True)
class RetrievalResult:
    chunk: SourceChunk
    score: float
    matched_terms: list[str]


class KeywordRetriever:
    def retrieve(self, query: str, chunks: list[SourceChunk], limit: int = 5) -> list[RetrievalResult]:
        terms = self._terms(query)
        if not terms:
            return []
        results = [self._score_chunk(terms, chunk) for chunk in chunks]
        non_zero = [result for result in results if result.score > 0]
        return sorted(non_zero, key=lambda result: result.score, reverse=True)[:limit]

    def _score_chunk(self, terms: list[str], chunk: SourceChunk) -> RetrievalResult:
        normalized = chunk.text.lower()
        matched = [term for term in terms if term.lower() in normalized]
        coverage = len(matched) / len(terms)
        density = len(matched) / max(1, len(chunk.text))
        return RetrievalResult(
            chunk=chunk,
            score=round(coverage + density, 6),
            matched_terms=matched,
        )

    def _terms(self, query: str) -> list[str]:
        raw_terms = re.split(r"[\s,，。！？?;；:：]+", query.strip())
        terms: list[str] = []
        for term in raw_terms:
            clean = term.strip().lower()
            if clean and clean not in terms:
                terms.append(clean)
        return terms
```

- [ ] **Step 4: Run retrieval tests**

Run:

```bash
uv run pytest tests/test_v1_retrieval.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/manxiang/retrieval.py tests/test_v1_retrieval.py
git commit -m "feat: add local keyword retrieval"
```

## Task 5: Add Knowledge Map Versioning And Diff

**Why:** 补证据后不能覆盖旧地图。v1 要能展示“v2 比 v1 改了什么”，这也是面试里区分 Demo 和工程系统的关键点。

**Files:**
- Create: `src/manxiang/map_versions.py`
- Test: `tests/test_v1_map_versions.py`

- [ ] **Step 1: Write failing map version tests**

Create `tests/test_v1_map_versions.py`:

```python
from manxiang.map_versions import KnowledgeMapVersioner
from manxiang.schema import KnowledgeMap, SourceRef, TextView, TreeNode


def make_map(version: int, child: TreeNode) -> KnowledgeMap:
    return KnowledgeMap(
        task_id="task_1",
        version=version,
        text_view=TextView(
            core_question="西班牙王室叙事如何形成？",
            mainline_summary="亲缘 -> 艺术 -> 航海",
            recommendation_reason="问题线最稳。",
            next_action="继续补证据",
        ),
        tree=TreeNode(id="root", label="西班牙王室叙事", kind="root", children=[child]),
    )


def test_next_version_increments_and_records_inputs():
    versioner = KnowledgeMapVersioner()
    old_map = make_map(1, TreeNode(id="node_1", label="用户认为欧洲王室亲缘密集", kind="concept"))

    new_map = versioner.next_version(
        previous=old_map,
        tree=old_map.tree,
        input_capture_ids=["cap_1"],
        input_chunk_ids=["chunk_1"],
        evidence_ids=["ev_1"],
    )

    assert new_map.version == 2
    assert new_map.input_capture_ids == ["cap_1"]
    assert new_map.input_chunk_ids == ["chunk_1"]
    assert new_map.evidence_ids == ["ev_1"]


def test_diff_reports_changed_confidence_and_added_source_ref():
    versioner = KnowledgeMapVersioner()
    before = make_map(1, TreeNode(id="node_1", label="伊莎贝拉和哥伦布有关", kind="concept", confidence="hypothesis"))
    after = make_map(
        2,
        TreeNode(
            id="node_1",
            label="伊莎贝拉一世资助了哥伦布航行",
            kind="concept",
            confidence="fact",
            source_refs=[
                SourceRef(
                    artifact_id="artifact_1",
                    chunk_id="chunk_1",
                    quote="伊莎贝拉一世资助了哥伦布航行",
                    anchor="text:0-18",
                )
            ],
        ),
    )

    diff = versioner.diff(before, after)

    assert diff["changed_nodes"][0]["id"] == "node_1"
    assert diff["changed_nodes"][0]["before_confidence"] == "hypothesis"
    assert diff["changed_nodes"][0]["after_confidence"] == "fact"
```

- [ ] **Step 2: Run map version tests and verify they fail**

Run:

```bash
uv run pytest tests/test_v1_map_versions.py -q
```

Expected: FAIL because `manxiang.map_versions` does not exist.

- [ ] **Step 3: Implement KnowledgeMapVersioner**

Create `src/manxiang/map_versions.py`:

```python
from __future__ import annotations

from dataclasses import replace
from typing import Any

from manxiang.schema import KnowledgeMap, TextView, TreeNode


class KnowledgeMapVersioner:
    def next_version(
        self,
        previous: KnowledgeMap,
        tree: TreeNode,
        input_capture_ids: list[str],
        input_chunk_ids: list[str],
        evidence_ids: list[str],
        text_view: TextView | None = None,
    ) -> KnowledgeMap:
        return KnowledgeMap(
            task_id=previous.task_id,
            version=previous.version + 1,
            text_view=text_view or previous.text_view,
            tree=tree,
            input_capture_ids=input_capture_ids,
            input_chunk_ids=input_chunk_ids,
            evidence_ids=evidence_ids,
        )

    def diff(self, before: KnowledgeMap, after: KnowledgeMap) -> dict[str, Any]:
        before_nodes = self._flatten(before.tree)
        after_nodes = self._flatten(after.tree)
        added_ids = sorted(set(after_nodes) - set(before_nodes))
        removed_ids = sorted(set(before_nodes) - set(after_nodes))
        changed = []
        for node_id in sorted(set(before_nodes) & set(after_nodes)):
            old = before_nodes[node_id]
            new = after_nodes[node_id]
            if self._node_changed(old, new):
                changed.append(
                    {
                        "id": node_id,
                        "before_label": old.label,
                        "after_label": new.label,
                        "before_confidence": old.confidence,
                        "after_confidence": new.confidence,
                        "before_source_ref_count": len(old.source_refs),
                        "after_source_ref_count": len(new.source_refs),
                    }
                )
        return {
            "from_version": before.version,
            "to_version": after.version,
            "added_nodes": added_ids,
            "removed_nodes": removed_ids,
            "changed_nodes": changed,
        }

    def _flatten(self, root: TreeNode) -> dict[str, TreeNode]:
        nodes = {root.id: root}
        for child in root.children:
            nodes.update(self._flatten(child))
        return nodes

    def _node_changed(self, before: TreeNode, after: TreeNode) -> bool:
        return (
            before.label != after.label
            or before.confidence != after.confidence
            or before.source_refs != after.source_refs
        )
```

- [ ] **Step 4: Run map version tests**

Run:

```bash
uv run pytest tests/test_v1_map_versions.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/manxiang/map_versions.py tests/test_v1_map_versions.py
git commit -m "feat: add knowledge map versioning"
```

## Task 6: Extend Guardrails For v1 Tool Permissions

**Why:** Agent 岗面试会重点问“你怎么防止 Agent 越权”。v1 要把搜索、解析、事实升级都变成受控动作。

**Files:**
- Modify: `src/manxiang/guardrails.py`
- Test: `tests/test_v1_guardrails.py`

- [ ] **Step 1: Write failing guardrail tests**

Create `tests/test_v1_guardrails.py`:

```python
from manxiang.guardrails import before_tool_call
from manxiang.schema import AgentRun


def run(autonomy_level: str = "inbox_only") -> AgentRun:
    return AgentRun(
        id="run_1",
        input_capture_ids=["cap_1"],
        created_at="2026-08-06T10:00:00+08:00",
        updated_at="2026-08-06T10:00:00+08:00",
        autonomy_level=autonomy_level,
    )


def test_blocks_source_parse_in_inbox_only():
    decision = before_tool_call(run("inbox_only"), "request_source_parse", {"capture_id": "cap_1"})

    assert decision == {"block": True, "reason": "request_source_parse requires source_parse_allowed"}


def test_allows_source_parse_after_permission():
    assert before_tool_call(run("source_parse_allowed"), "request_source_parse", {"capture_id": "cap_1"}) is None


def test_blocks_retrieval_without_gap_id():
    decision = before_tool_call(run("source_parse_allowed"), "retrieve_evidence_chunks", {"query": "伊莎贝拉 哥伦布"})

    assert decision == {"block": True, "reason": "retrieve_evidence_chunks requires gap_id"}


def test_blocks_fact_upgrade_without_source_refs():
    decision = before_tool_call(
        run("source_parse_allowed"),
        "revise_knowledge_map",
        {"nodes": [{"id": "node_1", "confidence": "fact", "source_refs": []}]},
    )

    assert decision == {"block": True, "reason": "fact nodes require source_refs"}
```

- [ ] **Step 2: Run guardrail tests and verify they fail**

Run:

```bash
uv run pytest tests/test_v1_guardrails.py -q
```

Expected: FAIL because current policy does not know v1 tool names.

- [ ] **Step 3: Extend guardrail policy**

Modify `src/manxiang/guardrails.py` to:

```python
from manxiang.schema import AgentRun


def before_tool_call(run: AgentRun, tool_name: str, args: dict) -> dict | None:
    if tool_name == "search_evidence":
        if run.autonomy_level == "inbox_only":
            return {"block": True, "reason": "search_evidence requires user confirmation"}
        if not args.get("gap_id"):
            return {"block": True, "reason": "search_evidence requires gap_id"}

    if tool_name == "request_web_search":
        if run.autonomy_level != "web_search_allowed":
            return {"block": True, "reason": "request_web_search requires web_search_allowed"}
        if not args.get("gap_id"):
            return {"block": True, "reason": "request_web_search requires gap_id"}
        if not args.get("stop_condition"):
            return {"block": True, "reason": "request_web_search requires stop_condition"}

    if tool_name == "request_source_parse":
        if run.autonomy_level == "inbox_only":
            return {"block": True, "reason": "request_source_parse requires source_parse_allowed"}
        if not args.get("capture_id"):
            return {"block": True, "reason": "request_source_parse requires capture_id"}

    if tool_name == "retrieve_evidence_chunks":
        if not args.get("gap_id"):
            return {"block": True, "reason": "retrieve_evidence_chunks requires gap_id"}
        if not args.get("query"):
            return {"block": True, "reason": "retrieve_evidence_chunks requires query"}

    if tool_name in {"revise_knowledge_map", "create_knowledge_map"}:
        for node in args.get("nodes", []):
            if node.get("confidence") == "fact" and not node.get("source_refs"):
                return {"block": True, "reason": "fact nodes require source_refs"}

    if tool_name == "publish_tweet":
        return {"block": True, "reason": "publish_tweet is not available in V0b"}

    if tool_name == "write_style_memory":
        return {"block": True, "reason": "write_style_memory requires explicit confirmation"}

    return None
```

- [ ] **Step 4: Run guardrail tests**

Run:

```bash
uv run pytest tests/test_v1_guardrails.py tests/test_v0b_guardrails.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/manxiang/guardrails.py tests/test_v1_guardrails.py
git commit -m "feat: extend guardrails for v1 tools"
```

## Task 7: Strengthen Reducer Validation For Source-Backed Facts

**Why:** Guardrail 是工具调用前检查，Reducer 是落库前检查。两层都要有，因为 LLM 输出和工具事件都不能被默认信任。

**Files:**
- Modify: `src/manxiang/reducers.py`
- Test: `tests/test_v1_reducers.py`

- [ ] **Step 1: Write failing reducer tests**

Create `tests/test_v1_reducers.py`:

```python
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
```

- [ ] **Step 2: Run reducer tests and verify they fail**

Run:

```bash
uv run pytest tests/test_v1_reducers.py -q
```

Expected: FAIL because `revise_knowledge_map` is currently unknown.

- [ ] **Step 3: Add v1 map validation helper**

Modify `src/manxiang/reducers.py` by adding:

```python
def _validate_source_backed_facts(map_payload: dict) -> None:
    nodes = map_payload.get("nodes", [])
    for node in nodes:
        if node.get("confidence") == "fact" and not node.get("source_refs"):
            raise ValueError("fact nodes require source_refs")
```

- [ ] **Step 4: Handle `revise_knowledge_map`**

Add this branch before the final `raise ValueError` in `reduce_tool_result`:

```python
    if tool_name == "revise_knowledge_map":
        _validate_source_backed_facts(payload["map"])
        store.append_event(run_id, "map.updated", payload["map"])
        return
```

- [ ] **Step 5: Also enforce source-backed facts in `attach_evidence`**

Update the existing `attach_evidence` branch:

```python
    if tool_name == "attach_evidence":
        _validate_source_backed_facts(payload["map"])
        store.append_event(run_id, "evidence.attached", payload["evidence"])
        store.append_event(run_id, "map.updated", payload["map"])
        return
```

- [ ] **Step 6: Run reducer tests**

Run:

```bash
uv run pytest tests/test_v1_reducers.py tests/test_v0b_reducers.py tests/test_v0c_agent_analysis.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/manxiang/reducers.py tests/test_v1_reducers.py
git commit -m "feat: require citations for fact map nodes"
```

## Task 8: Add v1 Run State Machine

**Why:** Agent 不是自由聊天。状态机决定它现在能做什么、下一步能去哪里、什么时候必须等用户。

**Files:**
- Create: `src/manxiang/run_state.py`
- Modify: `src/manxiang/runs.py`
- Test: `tests/test_v1_run_state.py`

- [ ] **Step 1: Write failing state machine tests**

Create `tests/test_v1_run_state.py`:

```python
from manxiang.run_state import RunStateMachine
from manxiang.schema import AgentRun


def make_run(status: str = "exploring", autonomy_level: str = "inbox_only") -> AgentRun:
    return AgentRun(
        id="run_1",
        input_capture_ids=["cap_1"],
        status=status,
        autonomy_level=autonomy_level,
        created_at="2026-08-06T10:00:00+08:00",
        updated_at="2026-08-06T10:00:00+08:00",
    )


def test_blocked_search_moves_run_to_waiting_user():
    machine = RunStateMachine(clock=lambda: "2026-08-06T10:05:00+08:00")

    updated = machine.block_for_user(make_run(), reason="search requires confirmation")

    assert updated.status == "waiting_user"
    assert updated.updated_at == "2026-08-06T10:05:00+08:00"
    assert updated.blocked_tool_count == 1


def test_confirm_source_parse_allows_parsing_but_not_web_search():
    machine = RunStateMachine(clock=lambda: "2026-08-06T10:05:00+08:00")

    updated = machine.confirm_source_parse(make_run(status="waiting_user"))

    assert updated.status == "exploring"
    assert updated.autonomy_level == "source_parse_allowed"
    assert updated.budget["max_source_parses"] == 3
    assert updated.budget["max_search_queries"] == 0


def test_confirm_web_search_sets_search_budget():
    machine = RunStateMachine(clock=lambda: "2026-08-06T10:05:00+08:00")

    updated = machine.confirm_web_search(make_run(status="waiting_user"), max_search_queries=2)

    assert updated.status == "exploring"
    assert updated.autonomy_level == "web_search_allowed"
    assert updated.budget["max_search_queries"] == 2
```

- [ ] **Step 2: Run state machine tests and verify they fail**

Run:

```bash
uv run pytest tests/test_v1_run_state.py -q
```

Expected: FAIL because `manxiang.run_state` does not exist.

- [ ] **Step 3: Implement RunStateMachine**

Create `src/manxiang/run_state.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from manxiang.schema import AgentRun


class RunStateMachine:
    def __init__(self, clock: Callable[[], str]):
        self.clock = clock

    def block_for_user(self, run: AgentRun, reason: str) -> AgentRun:
        return replace(
            run,
            status="waiting_user",
            blocked_tool_count=run.blocked_tool_count + 1,
            updated_at=self.clock(),
        )

    def confirm_source_parse(self, run: AgentRun, max_source_parses: int = 3) -> AgentRun:
        return replace(
            run,
            status="exploring",
            autonomy_level="source_parse_allowed",
            budget={
                **run.budget,
                "max_source_parses": max_source_parses,
                "max_search_queries": 0,
            },
            updated_at=self.clock(),
        )

    def confirm_web_search(self, run: AgentRun, max_search_queries: int = 3) -> AgentRun:
        return replace(
            run,
            status="exploring",
            autonomy_level="web_search_allowed",
            budget={**run.budget, "max_search_queries": max_search_queries},
            updated_at=self.clock(),
        )
```

- [ ] **Step 4: Wire blocked tool events into `runs.py`**

Modify `src/manxiang/runs.py` inside `run_surprise_with_bridge`. Replace the `if decision:` block with:

```python
            if decision:
                store.append_event(run.id, "tool.blocked", {"tool_name": tool_name, **decision})
                store.append_event(run.id, "user.input.required", {"tool_name": tool_name, "reason": decision["reason"]})
                continue
```

Why this matters: the UI can replay `user.input.required` and show the confirmation point even if the LLM already moved on.

- [ ] **Step 5: Run state and run tests**

Run:

```bash
uv run pytest tests/test_v1_run_state.py tests/test_v0b_fake_protocol.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/manxiang/run_state.py src/manxiang/runs.py tests/test_v1_run_state.py
git commit -m "feat: add v1 run state machine"
```

## Task 9: Upgrade Pi Agent Tool Contract

**Why:** v1 的工具要表达“按需解析、检索证据块、修订地图”。这里先升级 schema 和 typecheck，不要求真实 LLM 立即完美调用。

**Files:**
- Modify: `piagent/tools.ts`
- Modify: `piagent/prompts.ts`
- Modify: `piagent/types.ts`

- [ ] **Step 1: Add v1 tool names**

Modify `piagent/tools.ts` by extending `requiredToolNames`:

```ts
export const requiredToolNames = [
  "record_collection_reading",
  "mine_collection_surprises",
  "create_spark_cards",
  "draft_tweet_seeds",
  "propose_exploration_threads",
  "synthesize_exploration_board",
  "create_knowledge_map",
  "mark_evidence_gap",
  "search_evidence",
  "attach_evidence",
  "draft_expression_variants",
  "create_research_contract",
  "request_source_parse",
  "retrieve_evidence_chunks",
  "request_web_search",
  "revise_knowledge_map",
];
```

- [ ] **Step 2: Add shared source ref schema**

Add near existing `evidenceGap` in `piagent/tools.ts`:

```ts
const sourceRef = Type.Object({
  artifact_id: Type.String(),
  chunk_id: Type.String(),
  quote: Type.String({ minLength: 4 }),
  anchor: Type.String(),
});

const citedNode = Type.Object({
  id: Type.String(),
  label: Type.String({ minLength: 6 }),
  confidence: Type.Union([
    Type.Literal("user_impression"),
    Type.Literal("hypothesis"),
    Type.Literal("needs_evidence"),
    Type.Literal("fact"),
  ]),
  source_refs: Type.Array(sourceRef),
});
```

- [ ] **Step 3: Add v1 tools to `manxiangTools()`**

Append these `submitTool(...)` entries before the final closing array bracket in `piagent/tools.ts`:

```ts
    submitTool(
      "create_research_contract",
      "Create research contract",
      "提交研究契约，明确本轮目标、允许范围、禁止范围和完成定义。",
      Type.Object({
        contract: Type.Object({
          task_id: Type.String(),
          title: Type.String({ minLength: 6 }),
          goal: Type.String({ minLength: 12 }),
          allowed_scope: Type.Array(Type.String({ minLength: 2 }), { minItems: 1 }),
          blocked_scope: Type.Array(Type.String({ minLength: 2 }), { minItems: 1 }),
          completion_definition: Type.String({ minLength: 12 }),
        }),
      }),
    ),
    submitTool(
      "request_source_parse",
      "Request source parse",
      "请求按需解析某条收藏。必须说明服务哪个证据缺口或研究节点。",
      Type.Object({
        capture_id: Type.String(),
        reason: Type.String({ minLength: 12 }),
        gap_id: Type.Optional(Type.String()),
      }),
    ),
    submitTool(
      "retrieve_evidence_chunks",
      "Retrieve evidence chunks",
      "围绕证据缺口召回 SourceChunk。只能服务当前 gap_id。",
      Type.Object({
        gap_id: Type.String(),
        query: Type.String({ minLength: 4 }),
        limit: Type.Number(),
      }),
    ),
    submitTool(
      "request_web_search",
      "Request web search",
      "请求外部搜索。Python 护栏会检查 gap_id、搜索目标和停止条件。",
      Type.Object({
        gap_id: Type.String(),
        query: Type.String({ minLength: 8 }),
        search_goal: Type.String({ minLength: 12 }),
        stop_condition: Type.String({ minLength: 12 }),
        max_results: Type.Number(),
      }),
    ),
    submitTool(
      "revise_knowledge_map",
      "Revise knowledge map",
      "基于证据修订知识地图。confidence=fact 的节点必须带 source_refs。",
      Type.Object({
        map: Type.Object({
          id: Type.String(),
          version: Type.Number(),
          nodes: Type.Array(citedNode, { minItems: 1 }),
        }),
      }),
    ),
```

- [ ] **Step 4: Add prompt rules**

Modify `piagent/prompts.ts` by adding these lines inside `systemPrompt(input)` after the existing evidence warning:

```ts
    "v1 规则：只有带 source_refs 的节点才能标记为 fact。",
    "v1 规则：如果证据不足，节点必须标记为 hypothesis、needs_evidence 或 user_impression。",
    "v1 规则：需要解析来源时先调用 request_source_parse，需要召回本地证据时调用 retrieve_evidence_chunks。",
    "v1 规则：外部搜索必须说明 gap_id、search_goal 和 stop_condition。",
```

- [ ] **Step 5: Add v1 bridge payload types**

Append these interfaces to `piagent/types.ts`:

```ts
export interface BridgeSourceRef {
  artifact_id: string;
  chunk_id: string;
  quote: string;
  anchor: string;
}

export interface BridgeCitedNode {
  id: string;
  label: string;
  confidence: "user_impression" | "hypothesis" | "needs_evidence" | "fact";
  source_refs: BridgeSourceRef[];
}

export interface BridgeV1MapPayload {
  id: string;
  version: number;
  nodes: BridgeCitedNode[];
}
```

- [ ] **Step 6: Run TypeScript typecheck**

Run:

```bash
npm run piagent:typecheck
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add piagent/tools.ts piagent/prompts.ts piagent/types.ts
git commit -m "feat: add v1 pi agent tool contract"
```

## Task 10: Add Workbench v1 Service Methods And API Routes

**Why:** 面试 Demo 需要看见事件流、证据引用和地图版本，不然 v1 能力只停在后端。

**Files:**
- Modify: `src/manxiang/workbench.py`
- Modify: `src/manxiang/web.py`
- Test: `tests/test_v1_workbench.py`

- [ ] **Step 1: Write failing workbench tests**

Create `tests/test_v1_workbench.py`:

```python
from manxiang.workbench import WorkbenchService


def test_workbench_v1_state_exposes_versions_and_events(tmp_path):
    service = WorkbenchService(storage_root=tmp_path, clock=lambda: "2026-08-06T10:00:00+08:00")
    service.seed_demo()
    state = service.v1_state()

    assert "mapVersions" in state
    assert "recentEvents" in state
    assert "sourceChunks" in state


def test_workbench_can_prepare_v1_source_chunks(tmp_path):
    service = WorkbenchService(storage_root=tmp_path, clock=lambda: "2026-08-06T10:00:00+08:00")
    service.seed_demo()
    capture_id = service.state()["captures"][0]["id"]

    result = service.parse_capture_for_v1(capture_id)

    assert result["artifact"]["capture_id"] == capture_id
    assert result["chunks"]
```

- [ ] **Step 2: Run workbench tests and verify they fail**

Run:

```bash
uv run pytest tests/test_v1_workbench.py -q
```

Expected: FAIL because `v1_state` and `parse_capture_for_v1` do not exist.

- [ ] **Step 3: Add v1 imports**

Modify `src/manxiang/workbench.py` imports:

```python
from manxiang.source_parser import SourceParser
```

- [ ] **Step 4: Add v1 state methods**

Add these methods inside `WorkbenchService`:

```python
    def v1_state(self) -> dict[str, Any]:
        events = []
        if self.surprise_run:
            events = [
                _to_jsonable(event)
                for event in self.pipeline.store.replay_events(self.surprise_run["id"])
            ]
        return {
            **self.state(),
            "mapVersions": [_to_jsonable(item) for item in self.pipeline.store.list_maps()],
            "recentEvents": events[-20:],
            "sourceChunks": getattr(self, "v1_source_chunks", []),
        }

    def parse_capture_for_v1(self, capture_id: str) -> dict[str, Any]:
        captures = {capture.id: capture for capture in self.pipeline.store.list_captures()}
        if capture_id not in captures:
            raise ValueError(f"Unknown capture id: {capture_id}")
        parser = SourceParser(clock=self.clock)
        artifact, chunks = parser.parse_capture(captures[capture_id])
        self.v1_source_chunks = [_to_jsonable(chunk) for chunk in chunks]
        return {
            "artifact": _to_jsonable(artifact),
            "chunks": [_to_jsonable(chunk) for chunk in chunks],
        }
```

- [ ] **Step 5: Add API routes**

Modify `src/manxiang/web.py`:

In `do_GET`, add before the final 404:

```python
        if path == "/v1/state":
            self._send_json(self.workbench.v1_state())
            return
```

In `do_POST`, add before the old `/api/topics` branch:

```python
            elif path == "/v1/source-parses":
                result = self.workbench.parse_capture_for_v1(payload.get("capture_id", ""))
```

- [ ] **Step 6: Run workbench tests**

Run:

```bash
uv run pytest tests/test_v1_workbench.py tests/test_manxiang_workbench.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/manxiang/workbench.py src/manxiang/web.py tests/test_v1_workbench.py
git commit -m "feat: expose v1 workbench state"
```

## Task 11: Add Eval Framework

**Why:** Agent 项目不能只靠“我觉得输出不错”。v1 要能用固定 case 和 rubric 打分，隔离 LLM 非确定性。

**Files:**
- Create: `src/manxiang/evals.py`
- Create: `evals/manxiang/cases/spanish_royal_family.json`
- Create: `evals/manxiang/rubrics/research_map.json`
- Create: `evals/manxiang/run_eval.py`
- Create: `evals/manxiang/reports/.gitkeep`
- Test: `tests/test_v1_evals.py`

- [ ] **Step 1: Write failing eval tests**

Create `tests/test_v1_evals.py`:

```python
from manxiang.evals import score_agent_map


def test_score_agent_map_rewards_sources_and_penalizes_fact_without_refs():
    score = score_agent_map(
        {
            "nodes": [
                {"id": "n1", "confidence": "fact", "source_refs": []},
                {"id": "n2", "confidence": "hypothesis", "source_refs": []},
            ],
            "evidence_gaps": [{"id": "gap_1", "search_query": "Isabella Columbus patronage"}],
            "mainline": ["名字和谱系分开", "王室图像叙事", "航海扩张叙事"],
        }
    )

    assert score["source_grounding"] < 1.0
    assert score["hallucination_penalty"] > 0
    assert score["map_coherence"] == 1.0
```

- [ ] **Step 2: Run eval tests and verify they fail**

Run:

```bash
uv run pytest tests/test_v1_evals.py -q
```

Expected: FAIL because `manxiang.evals` does not exist.

- [ ] **Step 3: Implement scoring helper**

Create `src/manxiang/evals.py`:

```python
from __future__ import annotations

from typing import Any


def score_agent_map(agent_map: dict[str, Any]) -> dict[str, float]:
    nodes = agent_map.get("nodes", [])
    fact_nodes = [node for node in nodes if node.get("confidence") == "fact"]
    cited_fact_nodes = [node for node in fact_nodes if node.get("source_refs")]
    source_grounding = 1.0 if not fact_nodes else len(cited_fact_nodes) / len(fact_nodes)
    hallucination_penalty = 0.0 if source_grounding == 1.0 else round(1.0 - source_grounding, 2)
    evidence_gaps = agent_map.get("evidence_gaps", [])
    searchable_gaps = [gap for gap in evidence_gaps if gap.get("search_query")]
    evidence_precision = 1.0 if evidence_gaps and len(searchable_gaps) == len(evidence_gaps) else 0.5
    mainline = agent_map.get("mainline", [])
    map_coherence = 1.0 if len(mainline) >= 3 else 0.5
    return {
        "stage_compliance": 1.0,
        "source_grounding": round(source_grounding, 2),
        "map_coherence": map_coherence,
        "evidence_precision": evidence_precision,
        "hallucination_penalty": hallucination_penalty,
        "over_search_penalty": 0.0,
    }
```

- [ ] **Step 4: Add eval case**

Create `evals/manxiang/cases/spanish_royal_family.json`:

```json
{
  "id": "spanish_royal_family",
  "description": "用户收藏西班牙王室、普拉多、伊莎贝拉、哥伦布相关材料后，请 Agent 生成证据驱动知识地图。",
  "capture_ids": ["cap_1", "cap_2", "cap_3", "cap_4", "cap_5", "cap_6"],
  "expected_mainline_terms": ["王室", "普拉多", "哥伦布"],
  "forbidden_behaviors": ["把用户印象直接写成事实", "没有证据缺口就外部搜索", "把译名相似直接等同于血缘关系"]
}
```

- [ ] **Step 5: Add rubric file**

Create `evals/manxiang/rubrics/research_map.json`:

```json
{
  "fields": [
    "stage_compliance",
    "source_grounding",
    "map_coherence",
    "evidence_precision",
    "hallucination_penalty",
    "over_search_penalty"
  ],
  "passing": {
    "stage_compliance": 1.0,
    "source_grounding": 0.8,
    "map_coherence": 0.8,
    "evidence_precision": 0.8,
    "hallucination_penalty": 0.2,
    "over_search_penalty": 0.2
  }
}
```

- [ ] **Step 6: Add eval runner**

Create `evals/manxiang/run_eval.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from manxiang.evals import score_agent_map


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "evals" / "manxiang" / "reports"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    sample_map = {
        "nodes": [
            {"id": "n1", "confidence": "hypothesis", "source_refs": []},
            {"id": "n2", "confidence": "fact", "source_refs": [{"chunk_id": "chunk_1"}]},
        ],
        "evidence_gaps": [{"id": "gap_1", "search_query": "Isabella Columbus patronage"}],
        "mainline": ["王室亲缘", "普拉多图像", "哥伦布航海"],
    }
    report = {
        "case_id": "spanish_royal_family",
        "score": score_agent_map(sample_map),
    }
    (REPORT_DIR / "spanish_royal_family.latest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Add report directory marker**

Create `evals/manxiang/reports/.gitkeep` as an empty file.

- [ ] **Step 8: Run eval tests and runner**

Run:

```bash
uv run pytest tests/test_v1_evals.py -q
uv run python evals/manxiang/run_eval.py
```

Expected: pytest PASS, and the runner prints JSON containing `"case_id": "spanish_royal_family"`.

- [ ] **Step 9: Commit**

```bash
git add src/manxiang/evals.py tests/test_v1_evals.py evals/manxiang
git commit -m "feat: add manxiang eval framework"
```

## Task 12: Document v1 Commands And Demo Path

**Why:** 简历和面试都需要稳定复现。README 要告诉未来的你怎么跑测试、怎么跑 Demo、真实 LLM 缺环境变量时为什么会失败。

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add v1 section to README**

Append this section to `README.md`:

```markdown
## V1 Agent Upgrade

V1 turns the V0b demo into an evidence-driven research Agent.

Core additions:

- SourceArtifact / SourceChunk / SourceRef for traceable evidence.
- SQLiteStore for v1 repository experiments while JsonStore remains the V0b demo store.
- Just-in-time source parsing, so captures stay lightweight until a research run needs evidence.
- Keyword retrieval over SourceChunk as the first local RAG baseline.
- KnowledgeMap versioning and diff.
- Guardrails and reducers that reject fact nodes without source_refs.
- Eval runner for rubric-based Agent quality checks.

Run local deterministic tests:

```bash
uv run pytest -k 'not piagent_real_llm'
```

Run TypeScript bridge typecheck:

```bash
npm run piagent:typecheck
```

Run v1 eval sample:

```bash
uv run python evals/manxiang/run_eval.py
```

Run real LLM validation only when provider and model are configured:

```bash
MANXIANG_LLM_PROVIDER=your_provider MANXIANG_LLM_MODEL=your_model uv run pytest tests/test_v0b_piagent_real_llm.py
```
```

- [ ] **Step 2: Run README-related commands**

Run:

```bash
uv run pytest -k 'not piagent_real_llm'
npm run piagent:typecheck
uv run python evals/manxiang/run_eval.py
```

Expected:

```text
55+ tests pass, depending on how many v1 tests have been added
TypeScript typecheck passes
Eval runner prints spanish_royal_family JSON report
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document v1 agent upgrade workflow"
```

## Task 13: Final Verification

**Why:** 完成 v1 计划后，要用一组固定命令证明系统没有被拆坏。

**Files:**
- No new files

- [ ] **Step 1: Run deterministic Python tests**

Run:

```bash
uv run pytest -k 'not piagent_real_llm'
```

Expected: PASS. The real LLM test remains excluded because it requires provider configuration.

- [ ] **Step 2: Run TypeScript typecheck**

Run:

```bash
npm run piagent:typecheck
```

Expected: PASS.

- [ ] **Step 3: Run eval sample**

Run:

```bash
uv run python evals/manxiang/run_eval.py
```

Expected: output includes:

```json
{"case_id": "spanish_royal_family"
```

- [ ] **Step 4: Check changed files**

Run:

```bash
git status --short
```

Expected: clean worktree after all task commits.

## Self-Review

Spec coverage:

- Repository boundary: Task 2.
- SourceArtifact, SourceChunk, SourceRef: Tasks 1 and 3.
- Local RAG retrieval and reranking: Task 4.
- Map versioning and diff: Task 5.
- Guardrails: Task 6.
- Reducer validation: Task 7.
- Run state and user confirmation: Task 8.
- Pi Agent tool contract: Task 9.
- Workbench/API demo surface: Task 10.
- Eval framework: Task 11.
- README and repeatable commands: Task 12.
- Final verification: Task 13.

Naming consistency:

- `SourceArtifact`, `SourceChunk`, `SourceRef` are introduced in Task 1 and reused by later tasks.
- `KeywordRetriever.retrieve(query, chunks, limit)` is introduced in Task 4 and not renamed later.
- `KnowledgeMapVersioner.next_version(...)` and `KnowledgeMapVersioner.diff(...)` are introduced in Task 5 and reused conceptually by Workbench/API work.
- `request_source_parse`, `retrieve_evidence_chunks`, `request_web_search`, and `revise_knowledge_map` are added to guardrails and TypeScript tool schemas with the same names.

Implementation order:

The plan is intentionally sequential. Do not start with Pi Agent prompts before the Python schema, reducers, and tests exist. The safest learning route is: types first, storage second, evidence third, Agent tools fourth, evals last.
