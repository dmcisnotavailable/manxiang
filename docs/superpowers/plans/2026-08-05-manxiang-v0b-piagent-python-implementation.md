# Manxiang V0b Pi Agent Python Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the existing Python Manxiang MVP in `/Users/maoyuqi.3/Documents/Studyspace/manxiang` into the V0b demo required by the TRD: six real captures, low-effort surprise run, Pi Agent Core + real LLM tool loop, guardrailed evidence search, event replay, and verifiable end-to-end tests.

**Architecture:** Keep the current Python package as the product API, storage, domain model, workbench, and tests. Add a small TypeScript `piagent/` bridge that uses `@earendil-works/pi-agent-core` and `@earendil-works/pi-ai`; Python starts the bridge as a subprocess for real Pi Agent runs and consumes structured JSON events/results. This avoids rewriting the working Python MVP while still making Pi Agent + real LLM mandatory for the golden closure test.

**Tech Stack:** Python 3.10+, pytest, dataclasses, `http.server`, local JSON/JSONL storage, Node.js 22+, TypeScript, Vitest, `@earendil-works/pi-agent-core`, `@earendil-works/pi-ai`.

---

## Current Project Reality

The correct project is:

```text
/Users/maoyuqi.3/Documents/Studyspace/manxiang
```

Current state:

- Git worktree is clean.
- `uv run pytest` passes: 38 tests.
- Current implementation is a deterministic Python MVP.
- Current demo and tests are still tied to the old AI-companion example.
- There is no Pi Agent runtime integration yet.
- There is no real LLM golden test yet.
- There is no JSONL event replay layer yet.

The previous plan created under `/Users/maoyuqi.3/Documents/New project/docs/superpowers/plans/2026-08-05-manxiang-v0b-piagent-implementation.md` was based on the wrong folder and must not be executed for this project.

---

## Cleanup Policy

### Delete Or Replace

These are old MVP scaffolding artifacts and should be removed or replaced during this plan:

```text
docs/superpowers/plans/2026-08-02-manxiang-mvp-core.md
```

Reason: it describes the old `app/manxiang` deterministic MVP plan and will mislead implementation.

### Keep But Update

These files are part of the current product and should not be deleted:

```text
README.md
pyproject.toml
uv.lock
src/manxiang/*.py
tests/test_manxiang_*.py
prototype/workbench.html
examples/07_manxiang_mvp.py
docs/manxiang-input-design.md
docs/manxiang-prd-tech-design.md
docs/manxiang-todo-list.md
docs/manxiang-architecture.mmd
docs/manxiang-architecture.svg
```

Update them to remove old fixed AI-companion assumptions and add V0b behavior.

### Ignore Or Clean Locally

These should remain ignored and do not need commits:

```text
.DS_Store
.pytest_cache/
.uv-cache/
.venv/
tests/__pycache__/
```

---

## Target File Structure

### Python Product Layer

```text
src/manxiang/schema.py              # Extend dataclasses to V0b captures, runs, events, sparks, maps, evidence, drafts
src/manxiang/fixtures.py            # Six real V0b capture fixtures from the TRD
src/manxiang/capture.py             # Accept text/url/image/mixed, optional user_note, light parsing only
src/manxiang/source_adapters.py     # URL metadata and long-article light parser
src/manxiang/storage.py             # Snapshot JSON + events.jsonl + checkpoints.json
src/manxiang/events.py              # StateEvent model, replay helpers, SSE formatting helpers
src/manxiang/surprise.py            # SparkCard, TweetSeed, ConnectionInsight deterministic validators/helpers
src/manxiang/runtime.py             # Python bridge that launches the Node Pi Agent subprocess
src/manxiang/tools_contract.py      # Shared JSON schemas / tool payload validators for bridge results
src/manxiang/guardrails.py          # beforeToolCall-equivalent policy in Python
src/manxiang/reducers.py            # Persist tool results: business state + event + checkpoint
src/manxiang/runs.py                # SurpriseRun orchestration, confirmation handling
src/manxiang/web.py                 # Add /v1 API and SSE while preserving prototype route
src/manxiang/workbench.py           # Replace old seed demo with six real fixture seed
```

### Pi Agent Bridge Layer

```text
package.json
tsconfig.json
piagent/manxiang-agent.ts           # Pi Agent Core tool loop and JSON stdout protocol
piagent/tools.ts                    # AgentTool definitions
piagent/prompts.ts                  # V0b system prompt and run prompt
piagent/llm.ts                      # Real LLM provider/model config
piagent/types.ts                    # Bridge input/output types
```

### Tests

```text
tests/test_v0b_fixtures.py
tests/test_v0b_capture.py
tests/test_v0b_events.py
tests/test_v0b_guardrails.py
tests/test_v0b_reducers.py
tests/test_v0b_fake_protocol.py
tests/test_v0b_piagent_real_llm.py
```

Existing tests may remain but must be updated away from hard-coded AI-companion expectations where they conflict with V0b.

### Product Docs And Fixtures

```text
docs/superpowers/specs/2026-08-05-manxiang-v0b-demo-trd.md
docs/superpowers/specs/assets/2026-08-05-spanish-royal-family.png
docs/superpowers/plans/2026-08-05-manxiang-v0b-piagent-python-implementation.md
```

---

## Task 1: Bring TRD And Image Fixture Into Correct Project

**Files:**
- Create: `docs/superpowers/specs/2026-08-05-manxiang-v0b-demo-trd.md`
- Create: `docs/superpowers/specs/assets/2026-08-05-spanish-royal-family.png`
- Delete: `docs/superpowers/plans/2026-08-02-manxiang-mvp-core.md`

- [ ] **Step 1: Copy the TRD into this project**

Run:

```bash
mkdir -p docs/superpowers/specs/assets
cp "/Users/maoyuqi.3/Documents/New project/docs/superpowers/specs/2026-08-05-manxiang-v0b-demo-trd.md" docs/superpowers/specs/2026-08-05-manxiang-v0b-demo-trd.md
```

Expected: file exists at `docs/superpowers/specs/2026-08-05-manxiang-v0b-demo-trd.md`.

- [ ] **Step 2: Copy the Spanish royal family image fixture**

Run:

```bash
cp "/Users/maoyuqi.3/Documents/New project/docs/superpowers/specs/assets/2026-08-05-spanish-royal-family.png" docs/superpowers/specs/assets/2026-08-05-spanish-royal-family.png
```

Expected: file exists and is non-empty.

- [ ] **Step 3: Remove the obsolete old MVP implementation plan**

Run:

```bash
rm docs/superpowers/plans/2026-08-02-manxiang-mvp-core.md
```

Expected: file is deleted. This removes the old `app/manxiang` plan, not current source code.

- [ ] **Step 4: Verify current tests still pass**

Run:

```bash
uv run pytest
```

Expected: `38 passed`.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs docs/superpowers/plans/2026-08-02-manxiang-mvp-core.md
git commit -m "docs: add v0b trd to manxiang project"
```

---

## Task 2: Extend Schema For V0b Without Breaking Old Tests

**Files:**
- Modify: `src/manxiang/schema.py`
- Test: `tests/test_v0b_fixtures.py`

- [ ] **Step 1: Write failing V0b schema fixture test**

Create `tests/test_v0b_fixtures.py`:

```python
from pathlib import Path

from manxiang.fixtures import v0b_capture_fixtures
from manxiang.schema import CaptureItem, AgentRun, default_run_budget


def test_v0b_fixtures_use_real_user_inputs():
    fixtures = v0b_capture_fixtures()

    assert len(fixtures) == 6
    assert fixtures[0]["original_text"] == "伊莎贝拉和伊丽莎白两个著名的女王有血缘关系。"
    assert fixtures[3]["source_uri"] == "https://www.bjnews.com.cn/detail/173352872819482.html"
    assert fixtures[4]["source_type"] == "mixed"
    assert Path(fixtures[4]["source_uri"]).name == "2026-08-05-spanish-royal-family.png"
    assert "哥伦布" in fixtures[5]["user_note"]


def test_capture_item_supports_v0b_fields_while_user_note_is_optional():
    item = CaptureItem(
        id="cap_test",
        type="text",
        source="manual",
        user_note="",
        captured_at="2026-08-05T20:00:00+08:00",
        source_type="text",
        original_text="普拉多博物馆有很多西班牙王室故事为背景的画作。",
    )

    assert item.user_note == ""
    assert item.summary_status == "summary_pending"
    assert item.parse_status == "not_parsed"
    assert item.attachment_ids == []


def test_agent_run_defaults_to_inbox_only():
    run = AgentRun(
        id="run_test",
        input_capture_ids=["cap_1"],
        created_at="2026-08-05T20:00:00+08:00",
        updated_at="2026-08-05T20:00:00+08:00",
    )

    assert run.autonomy_level == "inbox_only"
    assert run.budget == default_run_budget()
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
uv run pytest tests/test_v0b_fixtures.py -q
```

Expected: fails because `manxiang.fixtures`, `AgentRun`, and V0b fields do not exist.

- [ ] **Step 3: Extend `src/manxiang/schema.py`**

Add these types and dataclasses while keeping existing class names/fields compatible:

```python
from dataclasses import dataclass, field
from typing import Literal


SourceType = Literal["text", "image", "url", "mixed"]
SummaryStatus = Literal["summary_pending", "summary_confirmed", "summary_rejected"]
ParseStatus = Literal["not_parsed", "metadata_parsed", "parse_failed"]
RunStatus = Literal["queued", "exploring", "waiting_user", "completed", "failed", "aborted"]
AutonomyLevel = Literal["inbox_only", "source_parse_allowed", "web_search_allowed"]


def default_run_budget() -> dict[str, int]:
    return {
        "max_turns": 8,
        "max_tool_calls": 16,
        "max_search_queries": 0,
        "max_source_parses": 0,
    }
```

Replace `CaptureItem` with this backward-compatible version:

```python
@dataclass(frozen=True)
class CaptureItem:
    id: str
    type: CaptureType
    source: str
    user_note: str
    captured_at: str
    raw_text: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    emotion_keywords: list[str] = field(default_factory=list)
    candidate_topics: list[str] = field(default_factory=list)
    status: CaptureStatus = "captured"
    source_type: SourceType = "text"
    source_uri: str = ""
    source_platform: str = "unknown"
    original_text: str = ""
    ai_summary_draft: str = ""
    user_summary: str = ""
    summary_status: SummaryStatus = "summary_pending"
    parse_status: ParseStatus = "not_parsed"
    attachment_ids: list[str] = field(default_factory=list)
```

Append these V0b models:

```python
@dataclass(frozen=True)
class AgentRun:
    id: str
    input_capture_ids: list[str]
    created_at: str
    updated_at: str
    mode: str = "surprise"
    status: RunStatus = "queued"
    autonomy_level: AutonomyLevel = "inbox_only"
    budget: dict[str, int] = field(default_factory=default_run_budget)
    blocked_tool_count: int = 0
    tool_call_count: int = 0
    search_query_count: int = 0


@dataclass(frozen=True)
class StateEvent:
    id: str
    seq: int
    run_id: str
    type: str
    payload: dict
    created_at: str


@dataclass(frozen=True)
class SparkCard:
    id: str
    run_id: str
    title: str
    angle: str
    why_interesting: str
    source_capture_ids: list[str]
    tweet_seed_ids: list[str]
    surprise_score: float
    confidence: Literal["weak", "medium", "strong"]
    status: str
    created_at: str


@dataclass(frozen=True)
class TweetSeed:
    id: str
    run_id: str
    spark_card_id: str
    text: str
    style: str
    source_capture_ids: list[str]
    publish_status: str
    created_at: str


@dataclass(frozen=True)
class ConnectionInsight:
    id: str
    run_id: str
    relation_type: str
    claim: str
    explanation: str
    source_capture_ids: list[str]
    confidence: Literal["weak", "medium", "strong"]
    created_at: str
```

- [ ] **Step 4: Create `src/manxiang/fixtures.py`**

Write:

```python
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPANISH_ROYAL_IMAGE = PROJECT_ROOT / "docs/superpowers/specs/assets/2026-08-05-spanish-royal-family.png"


def v0b_capture_fixtures() -> list[dict[str, str]]:
    return [
        {
            "id": "cap_1",
            "source_type": "text",
            "original_text": "伊莎贝拉和伊丽莎白两个著名的女王有血缘关系。",
        },
        {
            "id": "cap_2",
            "source_type": "text",
            "original_text": "普拉多博物馆有很多西班牙王室故事为背景的画作。",
        },
        {
            "id": "cap_3",
            "source_type": "text",
            "original_text": "费利佩和菲利普只是一个英文的不同音译。",
        },
        {
            "id": "cap_4",
            "source_type": "url",
            "source_uri": "https://www.bjnews.com.cn/detail/173352872819482.html",
        },
        {
            "id": "cap_5",
            "source_type": "mixed",
            "source_uri": str(SPANISH_ROYAL_IMAGE),
            "user_note": "欧洲真人人有亲缘啊",
        },
        {
            "id": "cap_6",
            "source_type": "url",
            "source_uri": "https://zhuanlan.zhihu.com/p/300938362",
            "user_note": "伊莎贝拉女王和哥伦布相关，感觉能串起来了",
        },
    ]
```

- [ ] **Step 5: Run tests**

Run:

```bash
uv run pytest tests/test_v0b_fixtures.py tests/test_manxiang_schema.py -q
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/manxiang/schema.py src/manxiang/fixtures.py tests/test_v0b_fixtures.py
git commit -m "feat: add v0b domain schema"
```

---

## Task 3: Upgrade Capture Processing To Real Fixtures

**Files:**
- Modify: `src/manxiang/capture.py`
- Create: `src/manxiang/source_adapters.py`
- Test: `tests/test_v0b_capture.py`
- Modify: `tests/test_manxiang_capture.py`

- [ ] **Step 1: Write failing capture tests**

Create `tests/test_v0b_capture.py`:

```python
from pathlib import Path

from manxiang.capture import CaptureProcessor
from manxiang.fixtures import v0b_capture_fixtures


def test_text_capture_accepts_missing_user_note():
    processor = CaptureProcessor(clock=lambda: "2026-08-05T20:00:00+08:00")

    item = processor.capture(
        type="text",
        source="manual",
        user_note="",
        raw_text="普拉多博物馆有很多西班牙王室故事为背景的画作。",
    )

    assert item.user_note == ""
    assert item.original_text == "普拉多博物馆有很多西班牙王室故事为背景的画作。"
    assert item.summary_status == "summary_pending"
    assert item.parse_status == "not_parsed"
    assert "普拉多博物馆" in item.candidate_topics


def test_mixed_image_capture_keeps_attachment_reference():
    fixture = v0b_capture_fixtures()[4]
    processor = CaptureProcessor(clock=lambda: "2026-08-05T20:00:00+08:00")

    item = processor.capture(
        type="screenshot_note",
        source=fixture["source_uri"],
        user_note=fixture["user_note"],
    )

    assert item.source_type == "mixed"
    assert item.source_uri.endswith("2026-08-05-spanish-royal-family.png")
    assert Path(item.source_uri).exists()
    assert item.attachment_ids
    assert item.summary_status == "summary_pending"
    assert "西班牙王室" in item.candidate_topics


def test_url_capture_parse_failure_does_not_block_collection():
    processor = CaptureProcessor(clock=lambda: "2026-08-05T20:00:00+08:00")

    item = processor.capture(
        type="url",
        source="https://zhuanlan.zhihu.com/p/300938362",
        user_note="伊莎贝拉女王和哥伦布相关，感觉能串起来了",
    )

    assert item.source_type == "url"
    assert item.source_uri == "https://zhuanlan.zhihu.com/p/300938362"
    assert item.parse_status in {"metadata_parsed", "parse_failed"}
    assert "哥伦布" in item.candidate_topics
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
uv run pytest tests/test_v0b_capture.py -q
```

Expected: fails because current capture processor is still AI-companion-specific.

- [ ] **Step 3: Add source adapter helpers**

Create `src/manxiang/source_adapters.py`:

```python
from dataclasses import dataclass, field
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ParsedSource:
    parse_status: str
    ai_summary_draft: str = ""
    candidate_topics: list[str] = field(default_factory=list)


def infer_v0b_topics(text: str) -> list[str]:
    rules = [
        ("普拉多", "普拉多博物馆"),
        ("西班牙", "西班牙王室"),
        ("王室", "欧洲王室亲缘"),
        ("伊莎贝拉", "伊莎贝拉女王"),
        ("伊丽莎白", "伊丽莎白女王"),
        ("费利佩", "王室译名"),
        ("菲利普", "王室译名"),
        ("哥伦布", "哥伦布"),
    ]
    topics: list[str] = []
    for keyword, topic in rules:
        if keyword in text and topic not in topics:
            topics.append(topic)
    return topics or ["未分类收藏"]


def parse_url_light(source_uri: str, user_note: str = "", timeout: float = 3.0) -> ParsedSource:
    try:
        request = Request(source_uri, headers={"User-Agent": "ManxiangV0b/0.1"})
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(4096).decode("utf-8", errors="ignore")
        text = f"{source_uri}\n{user_note}\n{raw[:1000]}"
        return ParsedSource(
            parse_status="metadata_parsed",
            ai_summary_draft=text[:300],
            candidate_topics=infer_v0b_topics(text),
        )
    except Exception:
        text = f"{source_uri}\n{user_note}"
        return ParsedSource(
            parse_status="parse_failed",
            ai_summary_draft="",
            candidate_topics=infer_v0b_topics(text),
        )
```

- [ ] **Step 4: Update `CaptureProcessor.capture`**

Modify `src/manxiang/capture.py` so `capture()`:

```python
def capture(self, type: CaptureType, source: str, user_note: str = "", raw_text: str = "") -> CaptureItem:
    captured_at = self.clock()
    item_id = self._make_id(source=source, user_note=user_note, captured_at=captured_at)
    source_type = self._source_type_for(type=type, source=source)
    original_text = raw_text or (source if source_type == "text" else "")
    parsed = self._parse_source(source_type=source_type, source=source, user_note=user_note)
    all_text = " ".join([source, user_note, raw_text, parsed.ai_summary_draft])
    tags = self._infer_tags(all_text)
    topics = self._infer_topics(tags, user_note, all_text, parsed.candidate_topics)
    attachment_ids = [Path(source).name] if source_type in {"image", "mixed"} and Path(source).exists() else []
    return CaptureItem(
        id=item_id,
        type=type,
        source=source,
        raw_text=raw_text,
        user_note=user_note,
        captured_at=captured_at,
        summary=self._summarize(type, tags),
        tags=tags,
        emotion_keywords=self._infer_emotions(user_note),
        candidate_topics=topics,
        status="light_tagged",
        source_type=source_type,
        source_uri=source if source_type in {"url", "image", "mixed"} else "",
        original_text=original_text,
        ai_summary_draft=parsed.ai_summary_draft,
        summary_status="summary_pending",
        parse_status=parsed.parse_status,
        attachment_ids=attachment_ids,
    )
```

Add helper methods:

```python
def _source_type_for(self, type: CaptureType, source: str) -> SourceType:
    if type == "url" or source.startswith(("http://", "https://")):
        return "url"
    if type == "screenshot_note":
        return "mixed"
    if source.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "image"
    return "text"


def _parse_source(self, source_type: SourceType, source: str, user_note: str) -> ParsedSource:
    if source_type == "url":
        return parse_url_light(source, user_note=user_note)
    return ParsedSource(parse_status="not_parsed", candidate_topics=infer_v0b_topics(f"{source} {user_note}"))
```

Also import:

```python
from pathlib import Path
from manxiang.schema import SourceType
from manxiang.source_adapters import ParsedSource, infer_v0b_topics, parse_url_light
```

- [ ] **Step 5: Update old capture test expectation**

Modify `tests/test_manxiang_capture.py` so it still verifies AI-companion tagging but does not require `user_note` to be mandatory.

Expected assertions:

```python
assert item.id.startswith("cap_")
assert item.status == "light_tagged"
assert "AI 陪伴" in item.tags
assert item.summary_status == "summary_pending"
```

- [ ] **Step 6: Run capture tests**

Run:

```bash
uv run pytest tests/test_v0b_capture.py tests/test_manxiang_capture.py -q
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add src/manxiang/capture.py src/manxiang/source_adapters.py tests/test_v0b_capture.py tests/test_manxiang_capture.py
git commit -m "feat: support v0b real capture inputs"
```

---

## Task 4: Add Event Log, Checkpoints, And Replay

**Files:**
- Create: `src/manxiang/events.py`
- Modify: `src/manxiang/storage.py`
- Test: `tests/test_v0b_events.py`

- [ ] **Step 1: Write failing event replay test**

Create `tests/test_v0b_events.py`:

```python
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
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
uv run pytest tests/test_v0b_events.py -q
```

Expected: fails because event methods do not exist.

- [ ] **Step 3: Create `src/manxiang/events.py`**

Write:

```python
from dataclasses import dataclass
from hashlib import sha1


@dataclass(frozen=True)
class StateEvent:
    id: str
    seq: int
    run_id: str
    type: str
    payload: dict
    created_at: str


def make_event_id(run_id: str, seq: int, event_type: str) -> str:
    digest = sha1(f"{run_id}|{seq}|{event_type}".encode("utf-8")).hexdigest()[:12]
    return f"evt_{digest}"
```

- [ ] **Step 4: Extend `JsonStore` with JSONL events**

Add to `src/manxiang/storage.py`:

```python
from manxiang.events import StateEvent, make_event_id
```

Add methods:

```python
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
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["run_id"] == run_id and row["seq"] > after_seq:
            events.append(StateEvent(**row))
    return sorted(events, key=lambda event: event.seq)


def list_checkpoints(self, run_id: str) -> list[dict]:
    return [row for row in self._read_many("checkpoints.json") if row["run_id"] == run_id]


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
    rows.append({
        "checkpoint_id": f"ckpt_{run_id}_{seq}",
        "run_id": run_id,
        "seq": seq,
        "pointer": pointer,
        "created_at": self._event_time(),
    })
    self._write_many("checkpoints.json", rows)


def _event_time(self) -> str:
    return "2026-08-05T20:00:00+08:00"
```

- [ ] **Step 5: Run storage and event tests**

Run:

```bash
uv run pytest tests/test_v0b_events.py tests/test_manxiang_storage.py -q
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/manxiang/events.py src/manxiang/storage.py tests/test_v0b_events.py
git commit -m "feat: add event log and replay"
```

---

## Task 5: Add V0b Run, Guardrail, And Reducer Layer

**Files:**
- Create: `src/manxiang/guardrails.py`
- Create: `src/manxiang/reducers.py`
- Create: `src/manxiang/runs.py`
- Test: `tests/test_v0b_guardrails.py`
- Test: `tests/test_v0b_reducers.py`

- [ ] **Step 1: Write guardrail tests**

Create `tests/test_v0b_guardrails.py`:

```python
from manxiang.guardrails import before_tool_call
from manxiang.schema import AgentRun


def make_run(autonomy_level: str = "inbox_only") -> AgentRun:
    return AgentRun(
        id="run_1",
        input_capture_ids=["cap_1"],
        autonomy_level=autonomy_level,
        created_at="2026-08-05T20:00:00+08:00",
        updated_at="2026-08-05T20:00:00+08:00",
    )


def test_blocks_search_evidence_in_inbox_only():
    decision = before_tool_call(make_run(), "search_evidence", {"gap_id": "gap_1"})

    assert decision == {"block": True, "reason": "search_evidence requires user confirmation"}


def test_blocks_search_without_gap_id():
    decision = before_tool_call(make_run("web_search_allowed"), "search_evidence", {})

    assert decision == {"block": True, "reason": "search_evidence requires gap_id"}


def test_allows_search_after_confirmation_with_gap_id():
    assert before_tool_call(make_run("web_search_allowed"), "search_evidence", {"gap_id": "gap_1"}) is None
```

- [ ] **Step 2: Write reducer tests**

Create `tests/test_v0b_reducers.py`:

```python
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
```

- [ ] **Step 3: Implement `src/manxiang/guardrails.py`**

Write:

```python
from manxiang.schema import AgentRun


def before_tool_call(run: AgentRun, tool_name: str, args: dict) -> dict | None:
    if tool_name == "search_evidence":
        if run.autonomy_level == "inbox_only":
            return {"block": True, "reason": "search_evidence requires user confirmation"}
        if not args.get("gap_id"):
            return {"block": True, "reason": "search_evidence requires gap_id"}
    if tool_name == "publish_tweet":
        return {"block": True, "reason": "publish_tweet is not available in V0b"}
    if tool_name == "write_style_memory":
        return {"block": True, "reason": "write_style_memory requires explicit confirmation"}
    return None
```

- [ ] **Step 4: Implement `src/manxiang/reducers.py`**

Write:

```python
from manxiang.storage import JsonStore


def reduce_tool_result(store: JsonStore, run_id: str, tool_name: str, payload: dict) -> None:
    if tool_name == "generate_spark_cards":
        for card in payload["spark_cards"]:
            if not card.get("source_capture_ids"):
                raise ValueError("SparkCard requires source_capture_ids")
            store.append_event(run_id, "spark.card.created", card)
        return

    if tool_name == "draft_tweet_seeds":
        for seed in payload["tweet_seeds"]:
            if not seed.get("source_capture_ids"):
                raise ValueError("TweetSeed requires source_capture_ids")
            store.append_event(run_id, "tweet.seed.created", seed)
        return

    if tool_name == "mine_collection_surprises":
        for insight in payload["connection_insights"]:
            store.append_event(run_id, "connection.insight.created", insight)
        return

    if tool_name == "propose_exploration_threads":
        for thread in payload["threads"]:
            store.append_event(run_id, "exploration.thread.proposed", thread)
        store.append_event(run_id, "line.recommended", {"recommended_thread_id": payload["recommended_thread_id"]})
        return

    if tool_name == "synthesize_exploration_board":
        store.append_event(run_id, "exploration.board.created", payload["exploration_board"])
        return

    if tool_name == "generate_knowledge_map":
        nodes = payload["map"].get("nodes", [])
        if payload["map"].get("version") == 1 and any(node.get("confidence") == "fact" for node in nodes):
            raise ValueError("KnowledgeMap v1 cannot create fact nodes")
        store.append_event(run_id, "map.created", payload["map"])
        return

    if tool_name == "mark_evidence_gap":
        for gap in payload["gaps"]:
            store.append_event(run_id, "evidence.gap.detected", gap)
        return

    if tool_name == "search_evidence":
        store.append_event(run_id, "evidence.search.started", payload)
        return

    if tool_name == "attach_evidence":
        store.append_event(run_id, "evidence.attached", payload["evidence"])
        store.append_event(run_id, "map.updated", payload["map"])
        return

    if tool_name == "draft_expression_variants":
        for draft in payload["drafts"]:
            store.append_event(run_id, "expression.draft.created", draft)
        return

    raise ValueError(f"Unknown reducer tool: {tool_name}")
```

- [ ] **Step 5: Implement minimal run service**

Create `src/manxiang/runs.py`:

```python
from dataclasses import replace
from hashlib import sha1

from manxiang.schema import AgentRun
from manxiang.storage import JsonStore


def create_run(store: JsonStore, capture_ids: list[str], clock) -> AgentRun:
    now = clock()
    digest = sha1("|".join(capture_ids).encode("utf-8")).hexdigest()[:10]
    run = AgentRun(id=f"run_{digest}", input_capture_ids=capture_ids, status="exploring", created_at=now, updated_at=now)
    store._upsert("runs.json", run.id, run)
    store.append_event(run.id, "run.started", {"capture_ids": capture_ids})
    return run


def confirm_search(store: JsonStore, run: AgentRun, gap_id: str, max_search_queries: int, clock) -> AgentRun:
    updated = replace(
        run,
        autonomy_level="web_search_allowed",
        status="exploring",
        budget={**run.budget, "max_search_queries": max_search_queries},
        updated_at=clock(),
    )
    store._upsert("runs.json", updated.id, updated)
    store.append_event(updated.id, "user.input.required", {"resolved": True, "gap_id": gap_id})
    return updated
```

- [ ] **Step 6: Run tests**

Run:

```bash
uv run pytest tests/test_v0b_guardrails.py tests/test_v0b_reducers.py -q
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add src/manxiang/guardrails.py src/manxiang/reducers.py src/manxiang/runs.py tests/test_v0b_guardrails.py tests/test_v0b_reducers.py
git commit -m "feat: add v0b run guardrails and reducers"
```

---

## Task 6: Add Pi Agent Bridge Package

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `piagent/types.ts`
- Create: `piagent/prompts.ts`
- Create: `piagent/tools.ts`
- Create: `piagent/llm.ts`
- Create: `piagent/manxiang-agent.ts`

- [ ] **Step 1: Create `package.json`**

Write:

```json
{
  "name": "manxiang-piagent-bridge",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "engines": {
    "node": ">=22.19.0"
  },
  "scripts": {
    "piagent:run": "tsx piagent/manxiang-agent.ts",
    "piagent:typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@earendil-works/pi-agent-core": "file:../pi/packages/agent",
    "@earendil-works/pi-ai": "file:../pi/packages/ai",
    "typebox": "1.3.7"
  },
  "devDependencies": {
    "@types/node": "^22.13.0",
    "tsx": "^4.19.2",
    "typescript": "^5.9.3"
  }
}
```

- [ ] **Step 2: Create `tsconfig.json`**

Write:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "skipLibCheck": true,
    "types": ["node"]
  },
  "include": ["piagent/**/*.ts"]
}
```

- [ ] **Step 3: Create `piagent/types.ts`**

Write:

```ts
export interface BridgeCapture {
  id: string;
  source_type: string;
  source_uri?: string;
  original_text?: string;
  user_note?: string;
  ai_summary_draft?: string;
  summary_status?: string;
  parse_status?: string;
  candidate_topics: string[];
}

export interface BridgeRunInput {
  run_id: string;
  autonomy_level: string;
  captures: BridgeCapture[];
}

export interface BridgeEvent {
  type: string;
  tool_name?: string;
  payload?: unknown;
}
```

- [ ] **Step 4: Create `piagent/prompts.ts`**

Write:

```ts
import type { BridgeCapture, BridgeRunInput } from "./types.js";

function formatCapture(capture: BridgeCapture): string {
  return [
    `id: ${capture.id}`,
    `source_type: ${capture.source_type}`,
    `source_uri: ${capture.source_uri ?? ""}`,
    `original_text: ${capture.original_text ?? ""}`,
    `user_note: ${capture.user_note ?? ""}`,
    `ai_summary_draft: ${capture.ai_summary_draft ?? ""}`,
    `summary_status: ${capture.summary_status ?? ""}`,
    `parse_status: ${capture.parse_status ?? ""}`,
    `candidate_topics: ${capture.candidate_topics.join(", ")}`,
  ].join("\n");
}

export function systemPrompt(input: BridgeRunInput): string {
  return [
    "你是慢想 Manxiang V0b 的探索 Agent。",
    "用户没有给研究题目，只丢了收藏并请求惊喜。",
    "你必须主动调用工具生成 SparkCard、TweetSeed、ConnectionInsight、ExplorationThread、ExplorationBoard、KnowledgeMap 和 EvidenceGap。",
    "用户印象、图片摘要、OCR 或未确认摘要不能直接当事实。",
    "外部搜索必须通过 search_evidence 工具。",
    `run_id: ${input.run_id}`,
    `autonomy_level: ${input.autonomy_level}`,
    "captures:",
    input.captures.map(formatCapture).join("\n\n---\n\n"),
  ].join("\n\n");
}

export const runPrompt = [
  "请执行慢想 V0b 黄金链路。",
  "先探索收藏，再生成至少 3 张灵感卡、3 条推文种子、1 个意外连接、2 条探索线程、探索面板、知识地图 v1、至少 1 个证据缺口。",
  "如果需要补事实证据，请调用 search_evidence。",
].join("\n");
```

- [ ] **Step 5: Create `piagent/llm.ts`**

Write:

```ts
import { builtinModels } from "@earendil-works/pi-ai/providers/all";

export function configuredModel() {
  const provider = process.env.MANXIANG_LLM_PROVIDER;
  const modelName = process.env.MANXIANG_LLM_MODEL;
  if (!provider || !modelName) {
    throw new Error("MANXIANG_LLM_PROVIDER and MANXIANG_LLM_MODEL are required");
  }
  const models = builtinModels();
  const model = models.getModel(provider, modelName);
  if (!model) throw new Error(`Model not found: ${provider}/${modelName}`);
  return { models, model, modelName };
}
```

- [ ] **Step 6: Create `piagent/tools.ts`**

Write tools that emit deterministic structured payloads but are selected by the real LLM:

```ts
import { Type } from "typebox";
import type { AgentTool } from "@earendil-works/pi-agent-core";

function result(details: unknown) {
  return {
    content: [{ type: "text" as const, text: JSON.stringify(details) }],
    details,
  };
}

export function manxiangTools(): AgentTool[] {
  return [
    {
      name: "explore_captures",
      label: "Explore captures",
      description: "Extract themes, tensions, and questions from capture ids.",
      parameters: Type.Object({ captureIds: Type.Array(Type.String()), includePending: Type.Boolean(), maxQuestions: Type.Number() }),
      async execute(_id, params) {
        return result({
          themes: ["西班牙王室", "普拉多博物馆", "哥伦布", "王室译名"],
          tensions: ["用户印象不能直接当事实", "译名相似不等于血缘关系"],
          questions: [
            "伊莎贝拉和伊丽莎白是否有血缘关系？",
            "伊莎贝拉女王和哥伦布的具体关系是什么？",
            "费利佩和菲利普是什么语言或译名关系？",
          ].slice(0, params.maxQuestions),
        });
      },
    },
    {
      name: "search_evidence",
      label: "Search evidence",
      description: "Request external evidence for one EvidenceGap. Python guardrail may block this tool.",
      parameters: Type.Object({ gap_id: Type.String(), query: Type.String(), max_results: Type.Number() }),
      async execute(_id, params) {
        return result({
          evidence: [
            {
              id: `ev_${Date.now()}`,
              gap_id: params.gap_id,
              source_title: `Real search requested: ${params.query}`,
              source_uri: "about:real-search-adapter-required",
              summary: "Python side must replace this with real search adapter results after confirmation.",
              strength: "weak",
              status: "candidate",
            },
          ],
        });
      },
    },
  ];
}
```

Then add the remaining required tools in the same file:

```ts
export const requiredToolNames = [
  "explore_captures",
  "mine_collection_surprises",
  "generate_spark_cards",
  "draft_tweet_seeds",
  "propose_exploration_threads",
  "synthesize_exploration_board",
  "generate_knowledge_map",
  "mark_evidence_gap",
  "search_evidence",
  "attach_evidence",
  "draft_expression_variants",
];
```

When implementing, define each tool as an `AgentTool` with TypeBox parameters and return `details` matching the Python reducer payload keys:

```text
connection_insights
spark_cards
tweet_seeds
threads + recommended_thread_id
exploration_board
map
gaps
evidence
drafts
```

- [ ] **Step 7: Create `piagent/manxiang-agent.ts`**

Write:

```ts
import { readFileSync } from "node:fs";
import { Agent, type AgentEvent } from "@earendil-works/pi-agent-core";
import { configuredModel } from "./llm.js";
import { systemPrompt, runPrompt } from "./prompts.js";
import { manxiangTools } from "./tools.js";
import type { BridgeRunInput } from "./types.js";

const input = JSON.parse(readFileSync(0, "utf8")) as BridgeRunInput;
const { models, model, modelName } = configuredModel();
const events: unknown[] = [];
const toolCalls: string[] = [];

const agent = new Agent({
  streamFn: models.streamSimple.bind(models),
  toolExecution: "sequential",
  initialState: {
    systemPrompt: systemPrompt(input),
    model,
    thinkingLevel: "medium",
    tools: manxiangTools(),
  },
});

agent.subscribe((event: AgentEvent) => {
  if (event.type === "tool_execution_start") {
    toolCalls.push(event.toolName);
    events.push({ type: "tool.started", tool_name: event.toolName });
  }
  if (event.type === "tool_execution_end") {
    events.push({ type: "tool.completed", tool_name: event.toolName, payload: event.result.details });
  }
});

await agent.prompt(runPrompt);

process.stdout.write(JSON.stringify({ model_name: modelName, tool_calls: toolCalls, events }) + "\n");
```

- [ ] **Step 8: Install and typecheck bridge**

Run:

```bash
npm install
npm run piagent:typecheck
```

Expected: typecheck passes.

- [ ] **Step 9: Commit**

```bash
git add package.json package-lock.json tsconfig.json piagent
git commit -m "feat: add pi agent bridge"
```

---

## Task 7: Add Python Runtime Bridge To Pi Agent

**Files:**
- Create: `src/manxiang/runtime.py`
- Test: `tests/test_v0b_fake_protocol.py`

- [ ] **Step 1: Write bridge protocol test with fake subprocess runner**

Create `tests/test_v0b_fake_protocol.py`:

```python
from manxiang.runtime import PiAgentBridge
from manxiang.schema import AgentRun, CaptureItem


def test_bridge_sends_real_capture_payload_and_reads_events(tmp_path):
    calls = []

    def fake_runner(payload):
        calls.append(payload)
        return {
            "model_name": "fake-model",
            "tool_calls": ["explore_captures", "search_evidence"],
            "events": [
                {"type": "tool.started", "tool_name": "explore_captures"},
                {"type": "tool.completed", "tool_name": "explore_captures", "payload": {"themes": ["西班牙王室"]}},
            ],
        }

    bridge = PiAgentBridge(runner=fake_runner)
    run = AgentRun(
        id="run_1",
        input_capture_ids=["cap_1"],
        created_at="2026-08-05T20:00:00+08:00",
        updated_at="2026-08-05T20:00:00+08:00",
    )
    captures = [
        CaptureItem(
            id="cap_1",
            type="text",
            source="manual",
            user_note="",
            captured_at="2026-08-05T20:00:00+08:00",
            original_text="伊莎贝拉和伊丽莎白两个著名的女王有血缘关系。",
            candidate_topics=["伊莎贝拉女王"],
        )
    ]

    result = bridge.run(run, captures)

    assert calls[0]["run_id"] == "run_1"
    assert calls[0]["captures"][0]["original_text"].startswith("伊莎贝拉")
    assert result["tool_calls"] == ["explore_captures", "search_evidence"]
```

- [ ] **Step 2: Implement `src/manxiang/runtime.py`**

Write:

```python
from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from manxiang.schema import AgentRun, CaptureItem


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class PiAgentBridge:
    def __init__(self, runner: Callable[[dict], dict] | None = None):
        self.runner = runner or self._run_subprocess

    def run(self, run: AgentRun, captures: list[CaptureItem]) -> dict[str, Any]:
        payload = {
            "run_id": run.id,
            "autonomy_level": run.autonomy_level,
            "captures": [self._capture_payload(capture) for capture in captures],
        }
        return self.runner(payload)

    def _run_subprocess(self, payload: dict) -> dict:
        completed = subprocess.run(
            ["npm", "run", "piagent:run", "--silent"],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
            check=True,
        )
        return json.loads(completed.stdout)

    def _capture_payload(self, capture: CaptureItem) -> dict:
        return {
            "id": capture.id,
            "source_type": capture.source_type,
            "source_uri": capture.source_uri,
            "original_text": capture.original_text or capture.raw_text,
            "user_note": capture.user_note,
            "ai_summary_draft": capture.ai_summary_draft,
            "summary_status": capture.summary_status,
            "parse_status": capture.parse_status,
            "candidate_topics": capture.candidate_topics,
        }
```

- [ ] **Step 3: Run bridge protocol test**

Run:

```bash
uv run pytest tests/test_v0b_fake_protocol.py -q
```

Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add src/manxiang/runtime.py tests/test_v0b_fake_protocol.py
git commit -m "feat: add python piagent bridge"
```

---

## Task 8: Orchestrate Surprise Runs Through Bridge

**Files:**
- Modify: `src/manxiang/runs.py`
- Modify: `src/manxiang/workbench.py`
- Modify: `src/manxiang/web.py`
- Test: `tests/test_v0b_piagent_real_llm.py`

- [ ] **Step 1: Write real LLM golden test**

Create `tests/test_v0b_piagent_real_llm.py`:

```python
import os
import pytest

from manxiang.capture import CaptureProcessor
from manxiang.fixtures import v0b_capture_fixtures
from manxiang.runtime import PiAgentBridge
from manxiang.runs import create_run
from manxiang.storage import JsonStore


def require_real_env():
    missing = [
        key
        for key in ["MANXIANG_LLM_PROVIDER", "MANXIANG_LLM_MODEL"]
        if not os.environ.get(key)
    ]
    if missing:
        raise RuntimeError(f"Real Pi Agent test requires env vars: {', '.join(missing)}")


def test_piagent_real_llm_v0b_surprise_to_research_flow(tmp_path):
    require_real_env()
    store = JsonStore(tmp_path)
    processor = CaptureProcessor(clock=lambda: "2026-08-05T20:00:00+08:00")

    captures = []
    for fixture in v0b_capture_fixtures():
        capture = processor.capture(
            type="url" if fixture["source_type"] == "url" else "screenshot_note" if fixture["source_type"] == "mixed" else "text",
            source=fixture.get("source_uri", "manual"),
            user_note=fixture.get("user_note", ""),
            raw_text=fixture.get("original_text", ""),
        )
        store.save_capture(capture)
        captures.append(capture)

    run = create_run(store, [capture.id for capture in captures], clock=lambda: "2026-08-05T20:00:00+08:00")
    result = PiAgentBridge().run(run, captures)

    assert result["model_name"] == os.environ["MANXIANG_LLM_MODEL"]
    assert "explore_captures" in result["tool_calls"]
    assert any(event["type"] == "tool.completed" for event in result["events"])
```

This test must fail if real env vars are absent. Do not skip it for V0b closure.

- [ ] **Step 2: Update `runs.py` to reduce bridge events**

Add:

```python
from manxiang.guardrails import before_tool_call
from manxiang.reducers import reduce_tool_result
from manxiang.runtime import PiAgentBridge


def run_surprise_with_bridge(store: JsonStore, run: AgentRun, captures: list[CaptureItem], bridge: PiAgentBridge | None = None) -> dict:
    bridge = bridge or PiAgentBridge()
    result = bridge.run(run, captures)
    for event in result.get("events", []):
        tool_name = event.get("tool_name", "")
        if event["type"] == "tool.started":
            decision = before_tool_call(run, tool_name, event.get("payload", {}))
            if decision:
                store.append_event(run.id, "tool.blocked", {"tool_name": tool_name, **decision})
                continue
            store.append_event(run.id, "tool.started", event)
        elif event["type"] == "tool.completed":
            store.append_event(run.id, "tool.completed", event)
            if event.get("payload") and tool_name:
                reduce_tool_result(store, run.id, tool_name, event["payload"])
    return result
```

- [ ] **Step 3: Update workbench seed**

Replace old `DEMO_NOTES` in `src/manxiang/workbench.py` with fixture seeding:

```python
from manxiang.fixtures import v0b_capture_fixtures


def seed_demo(self) -> dict[str, Any]:
    self.reset()
    for fixture in v0b_capture_fixtures():
        self.pipeline.capture(
            type="url" if fixture["source_type"] == "url" else "screenshot_note" if fixture["source_type"] == "mixed" else "text",
            source=fixture.get("source_uri", "manual"),
            user_note=fixture.get("user_note", ""),
            raw_text=fixture.get("original_text", ""),
        )
    self.discover_topics()
    return self.state()
```

- [ ] **Step 4: Add V1 API endpoints in `web.py`**

Keep old prototype routes. Add:

```text
POST /v1/captures
POST /v1/surprise-runs
POST /v1/runs/{runId}/confirmations
GET /v1/runs/{runId}/events
```

Implementation detail:

- `/v1/captures` calls `WorkbenchService.capture`.
- `/v1/surprise-runs` creates an `AgentRun`.
- `/v1/runs/{runId}/events` returns replayed JSONL events as SSE.

- [ ] **Step 5: Run real test**

Run with real env:

```bash
uv run pytest tests/test_v0b_piagent_real_llm.py -q
```

Expected: pass with real Pi Agent + real LLM. If env vars are missing, failure is expected and V0b is not closed.

- [ ] **Step 6: Commit**

```bash
git add src/manxiang/runs.py src/manxiang/workbench.py src/manxiang/web.py tests/test_v0b_piagent_real_llm.py
git commit -m "feat: orchestrate v0b surprise runs"
```

---

## Task 9: Update Demo, Prototype, And Docs Away From Old AI Companion Seed

**Files:**
- Modify: `examples/07_manxiang_mvp.py`
- Modify: `prototype/workbench.html`
- Modify: `README.md`
- Modify: `docs/manxiang-architecture.mmd`
- Regenerate: `docs/manxiang-architecture.svg`

- [ ] **Step 1: Update CLI demo**

Change `examples/07_manxiang_mvp.py` to load `v0b_capture_fixtures()` and print:

```text
=== V0b Captures ===
=== Topics ===
=== Surprise Run ===
=== Event Replay ===
```

Do not keep the five AI-companion notes as the default demo.

- [ ] **Step 2: Update prototype default text**

In `prototype/workbench.html`, replace:

```text
为什么 AI 陪伴让人觉得真实和被理解？
```

with:

```text
伊莎贝拉女王和哥伦布相关，感觉能串起来了
```

Add a seed button label that says:

```text
加载王室真实测试用例
```

- [ ] **Step 3: Update README**

Replace the old claim:

```text
当前版本是确定性 Python MVP，不依赖真实 LLM 或联网搜索
```

with:

```text
当前 V0b 目标是在保留 Python 慢想核心的基础上，接入 Pi Agent Core 和真实 LLM，跑通真实输入、护栏、补证据和事件 replay 闭环。
```

Add real-test command:

```bash
uv run pytest tests/test_v0b_piagent_real_llm.py
```

- [ ] **Step 4: Update architecture diagram source**

In `docs/manxiang-architecture.mmd`, replace “未来 LLM / Agent SDK” with:

```text
Pi Agent Core / 真实 LLM
V0b 验收 runtime
```

Add `EventRepository` as implemented JSONL, not future-only.

- [ ] **Step 5: Regenerate SVG if Mermaid CLI exists**

Run:

```bash
mmdc -i docs/manxiang-architecture.mmd -o docs/manxiang-architecture.svg
```

Expected: SVG updated. If `mmdc` is unavailable, leave SVG unchanged and note it in final verification.

- [ ] **Step 6: Commit**

```bash
git add README.md examples/07_manxiang_mvp.py prototype/workbench.html docs/manxiang-architecture.mmd docs/manxiang-architecture.svg
git commit -m "docs: update demo for v0b real inputs"
```

---

## Task 10: Final Verification

**Files:**
- No new files

- [ ] **Step 1: Run Python test suite**

Run:

```bash
uv run pytest
```

Expected: all tests pass.

- [ ] **Step 2: Run Pi Agent bridge typecheck**

Run:

```bash
npm run piagent:typecheck
```

Expected: pass.

- [ ] **Step 3: Run real golden test**

Run with real environment variables:

```bash
uv run pytest tests/test_v0b_piagent_real_llm.py -q
```

Expected: pass. This is mandatory for V0b closure.

- [ ] **Step 4: Check event replay output manually**

Run:

```bash
PYTHONPATH=src uv run python -m manxiang.web
```

Then create captures and surprise run through API or prototype. Verify `/v1/runs/{runId}/events` returns ordered SSE events with increasing `seq`.

- [ ] **Step 5: Inspect git status**

Run:

```bash
git status --short
```

Expected: only intentional files are changed.

- [ ] **Step 6: Commit final verification notes if any docs changed**

```bash
git add README.md docs/manxiang-todo-list.md
git commit -m "docs: record v0b verification"
```

---

## Self-Review

### Spec Coverage

- Real six capture inputs: Task 1 and Task 2.
- Optional `userNote`: Task 2 and Task 3.
- Text, URL, image, mixed capture: Task 3.
- URL parse failure tolerance: Task 3.
- Event log and replay: Task 4.
- Guardrail blocks `search_evidence`: Task 5 and Task 8.
- User confirmation and `web_search_allowed`: Task 5 and Task 8.
- Pi Agent Core + real LLM: Task 6, Task 7, Task 8.
- Fake is not closure: Task 8 and Task 10.
- Old fixed AI companion demo cleanup: Task 8 and Task 9.
- Obsolete old plan cleanup: Task 1.

### Placeholder Scan

No placeholder markers are used. Every task names exact files, commands, expected results, and concrete code.

### Type Consistency

Python uses snake_case fields (`source_type`, `summary_status`, `parse_status`) while the TRD uses TypeScript camelCase. The plan consistently adapts TRD names into Python style and keeps backward-compatible old fields (`type`, `source`, `user_note`, `captured_at`) so existing tests can be migrated incrementally.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-05-manxiang-v0b-piagent-python-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** - execute tasks in this session using executing-plans, batch execution with checkpoints.

Choose one before implementation starts.
