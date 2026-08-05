# Manxiang MVP Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first testable Python core for 慢想: collect links/notes, discover topic clusters, create a research task, recommend a mainline, generate a text + tree knowledge map, manage the parking lot, and allow evidence search only in the evidence-patching stage.

**Architecture:** Add a new `app/manxiang/` package beside the existing demo packages. Keep the first version deterministic and rule-based so every state transition can be tested without a real LLM. Later, LLM calls can replace specific processors behind the same interfaces.

**Tech Stack:** Python 3.10+, standard-library dataclasses/JSON/pathlib, pytest, existing `uv run pytest` test command.

---

## Scope Check

The PRD contains product UI, browser capture, editable graph, writing upgrade, style memory, and long-term archive. This plan intentionally implements only the MVP core engine and a CLI demo. A web UI, browser plugin, and full writing editor should each get their own later plan.

## File Structure

- Create `app/manxiang/__init__.py`: package exports.
- Create `app/manxiang/schema.py`: all shared dataclasses and literal state types.
- Create `app/manxiang/storage.py`: local JSON persistence for captures, topics, tasks, maps, evidence, and parking items.
- Create `app/manxiang/capture.py`: light capture processor; no network calls.
- Create `app/manxiang/topics.py`: topic clustering, maturity scoring, and trigger decisions.
- Create `app/manxiang/navigation.py`: research task creation, line recommendation, and line override risk explanation.
- Create `app/manxiang/maps.py`: text view and read-only tree knowledge map generation.
- Create `app/manxiang/intervention.py`: detour detection and three-level strong intervention protocol.
- Create `app/manxiang/evidence.py`: evidence-patching guard, search provider interface, fake provider for tests.
- Create `app/manxiang/pipeline.py`: orchestration facade used by examples and future UI.
- Create `examples/07_manxiang_mvp.py`: runnable CLI demo.
- Create tests under `tests/`: focused tests for each behavior.
- Modify `README.md`: document how to run the 慢想 MVP demo and tests.

---

### Task 1: Create Shared Schema

**Files:**
- Create: `app/manxiang/__init__.py`
- Create: `app/manxiang/schema.py`
- Test: `tests/test_manxiang_schema.py`

- [ ] **Step 1: Write the failing schema test**

```python
# tests/test_manxiang_schema.py
from app.manxiang.schema import CaptureItem, KnowledgeMap, ResearchTask, TextView, TreeNode


def test_capture_item_has_default_light_tagged_state():
    item = CaptureItem(
        id="cap_001",
        type="url",
        source="https://example.com",
        user_note="为什么这个 AI 陪伴产品让人觉得被理解？",
        captured_at="2026-08-02T20:00:00+08:00",
    )

    assert item.status == "captured"
    assert item.tags == []
    assert item.candidate_topics == []


def test_knowledge_map_has_text_and_tree_views():
    task = ResearchTask(
        id="task_001",
        title="AI 陪伴为什么让人觉得像真的",
        topic_id="topic_001",
        stage="map_drafted",
        default_output="knowledge_map",
        mode="gentle_editor",
        goal="生成知识地图",
        core_question="为什么人会把情感需求交给 AI？",
        completion_definition="形成文本 + 树状图知识地图",
        allowed_scope=["用户心理"],
        blocked_scope=["底层模型架构"],
        created_at="2026-08-02T20:00:00+08:00",
        updated_at="2026-08-02T20:00:00+08:00",
    )
    tree = TreeNode(id="root", label=task.title, kind="root")
    text = TextView(
        core_question=task.core_question,
        mainline_summary="孤独感增加 -> 低风险表达 -> 即时回应",
        recommendation_reason="用户感想多次出现为什么和真实感。",
        next_action="确认主线节点",
    )
    knowledge_map = KnowledgeMap(task_id=task.id, version=1, text_view=text, tree=tree)

    assert knowledge_map.text_view.core_question == task.core_question
    assert knowledge_map.tree.label == task.title
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_manxiang_schema.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.manxiang'`.

- [ ] **Step 3: Create the package export file**

```python
# app/manxiang/__init__.py
"""Core package for the 慢想 MVP."""
```

- [ ] **Step 4: Create shared dataclasses and state literals**

```python
# app/manxiang/schema.py
from dataclasses import dataclass, field
from typing import Literal


CaptureType = Literal["url", "text", "screenshot_note", "video_note"]
CaptureStatus = Literal["new", "captured", "light_tagged", "clustered", "used_in_task", "parked", "archived"]
TopicStatus = Literal["fragment", "gathering", "ready", "task_created", "settled"]
TaskStage = Literal[
    "candidate",
    "scoping",
    "line_chosen",
    "map_drafted",
    "evidence_gap_found",
    "evidence_patching",
    "map_confirmed",
    "optional_writing",
    "reviewed",
    "archived",
]
AgentMode = Literal["strict_mentor", "gentle_editor", "research_buddy"]
LineType = Literal["causal", "timeline", "question", "stakeholder", "emotion"]
NodeKind = Literal["root", "core_question", "mainline", "concept", "evidence", "evidence_gap", "parking_lot", "next_action"]
EvidenceStrength = Literal["weak", "medium", "strong"]
EvidenceStatus = Literal["usable", "weak_related", "discarded"]
InterventionLevel = Literal["remind", "limit", "refuse"]


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


@dataclass(frozen=True)
class TopicCluster:
    id: str
    name: str
    status: TopicStatus
    capture_ids: list[str]
    repeated_questions: list[str]
    emotion_patterns: list[str]
    maturity_score: float
    suggested_action: str


@dataclass(frozen=True)
class ResearchTask:
    id: str
    title: str
    topic_id: str
    stage: TaskStage
    default_output: str
    mode: AgentMode
    goal: str
    core_question: str
    completion_definition: str
    allowed_scope: list[str]
    blocked_scope: list[str]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class LineNode:
    id: str
    title: str
    kind: str
    summary: str
    depth_limit: int
    status: str


@dataclass(frozen=True)
class LinePlan:
    task_id: str
    recommended_line: LineType
    selected_line: LineType
    auxiliary_lines: list[LineType]
    recommendation_reason: str
    risk_notes: list[str]
    line_nodes: list[LineNode]


@dataclass(frozen=True)
class TextView:
    core_question: str
    mainline_summary: str
    recommendation_reason: str
    next_action: str


@dataclass(frozen=True)
class TreeNode:
    id: str
    label: str
    kind: NodeKind
    children: list["TreeNode"] = field(default_factory=list)


@dataclass(frozen=True)
class KnowledgeMap:
    task_id: str
    version: int
    text_view: TextView
    tree: TreeNode


@dataclass(frozen=True)
class EvidenceGap:
    id: str
    task_id: str
    node_id: str
    description: str
    search_goal: str
    stop_condition: str


@dataclass(frozen=True)
class SearchRequest:
    task_id: str
    gap_id: str
    query: str
    search_goal: str
    stop_condition: str


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    task_id: str
    source_type: str
    source_url: str
    title: str
    summary: str
    supports_node_id: str
    evidence_type: str
    strength: EvidenceStrength
    retrieved_at: str
    status: EvidenceStatus = "usable"


@dataclass(frozen=True)
class ParkingLotItem:
    id: str
    task_id: str
    title: str
    reason: str
    related_node_id: str
    suggested_future_output: str
    created_at: str
    status: str = "parked"


@dataclass(frozen=True)
class InterventionDecision:
    level: InterventionLevel
    message: str
    should_park: bool
    timebox_minutes: int | None = None
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_manxiang_schema.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/manxiang/__init__.py app/manxiang/schema.py tests/test_manxiang_schema.py
git commit -m "feat: add manxiang shared schema"
```

---

### Task 2: Add Local JSON Store

**Files:**
- Create: `app/manxiang/storage.py`
- Test: `tests/test_manxiang_storage.py`

- [ ] **Step 1: Write the failing storage test**

```python
# tests/test_manxiang_storage.py
from app.manxiang.schema import CaptureItem, TextView, TreeNode, KnowledgeMap
from app.manxiang.storage import JsonStore


def test_json_store_round_trips_capture_items(tmp_path):
    store = JsonStore(tmp_path)
    item = CaptureItem(
        id="cap_001",
        type="url",
        source="https://example.com",
        user_note="这个观点让我想知道为什么。",
        captured_at="2026-08-02T20:00:00+08:00",
        tags=["AI 陪伴"],
        candidate_topics=["AI 陪伴与亲密关系"],
        status="light_tagged",
    )

    store.save_capture(item)

    assert store.list_captures() == [item]


def test_json_store_round_trips_knowledge_maps(tmp_path):
    store = JsonStore(tmp_path)
    knowledge_map = KnowledgeMap(
        task_id="task_001",
        version=1,
        text_view=TextView(
            core_question="为什么人会把情感需求交给 AI？",
            mainline_summary="孤独感增加 -> 低风险表达",
            recommendation_reason="资料集中在原因解释。",
            next_action="补长期使用动机的证据",
        ),
        tree=TreeNode(
            id="root",
            label="AI 陪伴为什么让人觉得像真的",
            kind="root",
            children=[TreeNode(id="mainline", label="推荐主线", kind="mainline")],
        ),
    )

    store.save_map(knowledge_map)

    assert store.list_maps() == [knowledge_map]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_manxiang_storage.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.manxiang.storage'`.

- [ ] **Step 3: Implement JSON store**

```python
# app/manxiang/storage.py
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, TypeVar

from app.manxiang.schema import (
    CaptureItem,
    EvidenceItem,
    KnowledgeMap,
    ParkingLotItem,
    ResearchTask,
    TextView,
    TopicCluster,
    TreeNode,
)


T = TypeVar("T")


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_manxiang_storage.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/manxiang/storage.py tests/test_manxiang_storage.py
git commit -m "feat: add manxiang json store"
```

---

### Task 3: Implement Lightweight Capture Processing

**Files:**
- Create: `app/manxiang/capture.py`
- Test: `tests/test_manxiang_capture.py`

- [ ] **Step 1: Write the failing capture test**

```python
# tests/test_manxiang_capture.py
from app.manxiang.capture import CaptureProcessor


def test_capture_processor_tags_ai_companion_without_network():
    processor = CaptureProcessor(clock=lambda: "2026-08-02T20:00:00+08:00")

    item = processor.capture(
        type="url",
        source="https://example.com/ai-companion",
        user_note="明知道是 AI，为什么还是会觉得被理解和陪伴？",
    )

    assert item.id.startswith("cap_")
    assert item.status == "light_tagged"
    assert "AI 陪伴" in item.tags
    assert "真实感" in item.tags
    assert "AI 陪伴与亲密关系" in item.candidate_topics
    assert item.summary == "用户收藏了一个链接，并记录了关于 AI 陪伴、真实感 的即时感想。"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_manxiang_capture.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.manxiang.capture'`.

- [ ] **Step 3: Implement capture processor**

```python
# app/manxiang/capture.py
from collections.abc import Callable
from hashlib import sha1

from app.manxiang.schema import CaptureItem, CaptureType


class CaptureProcessor:
    """Lightweight capture processor.

    The collection phase must stay shallow: save the input, infer rough tags,
    and avoid opening a research rabbit hole.
    """

    def __init__(self, clock: Callable[[], str]):
        self.clock = clock

    def capture(self, type: CaptureType, source: str, user_note: str, raw_text: str = "") -> CaptureItem:
        captured_at = self.clock()
        item_id = self._make_id(source=source, user_note=user_note, captured_at=captured_at)
        tags = self._infer_tags(" ".join([source, user_note, raw_text]))
        emotion_keywords = self._infer_emotions(user_note)
        candidate_topics = self._infer_topics(tags, user_note)
        summary = self._summarize(type, tags)
        return CaptureItem(
            id=item_id,
            type=type,
            source=source,
            raw_text=raw_text,
            user_note=user_note,
            captured_at=captured_at,
            summary=summary,
            tags=tags,
            emotion_keywords=emotion_keywords,
            candidate_topics=candidate_topics,
            status="light_tagged",
        )

    def _make_id(self, source: str, user_note: str, captured_at: str) -> str:
        digest = sha1(f"{source}|{user_note}|{captured_at}".encode("utf-8")).hexdigest()[:10]
        return f"cap_{digest}"

    def _infer_tags(self, text: str) -> list[str]:
        rules = [
            ("AI", "AI 陪伴"),
            ("陪伴", "AI 陪伴"),
            ("被理解", "真实感"),
            ("真实", "真实感"),
            ("依赖", "依赖"),
            ("孤独", "孤独感"),
            ("写作", "去 AI 味写作"),
            ("注意力", "注意力管理"),
            ("跑偏", "注意力管理"),
        ]
        tags: list[str] = []
        for keyword, tag in rules:
            if keyword.lower() in text.lower() and tag not in tags:
                tags.append(tag)
        return tags or ["未分类"]

    def _infer_emotions(self, user_note: str) -> list[str]:
        emotions: list[str] = []
        if "为什么" in user_note or "?" in user_note or "？" in user_note:
            emotions.append("困惑")
        if "觉得" in user_note or "被理解" in user_note:
            emotions.append("被触动")
        return emotions

    def _infer_topics(self, tags: list[str], user_note: str) -> list[str]:
        topics: list[str] = []
        if "AI 陪伴" in tags or "真实感" in tags:
            topics.append("AI 陪伴与亲密关系")
        if "注意力管理" in tags:
            topics.append("注意力管理与信息摄入")
        if "去 AI 味写作" in tags:
            topics.append("AI 味写作")
        if not topics:
            topics.append(self._fallback_topic(user_note))
        return topics

    def _fallback_topic(self, user_note: str) -> str:
        compact = user_note.strip().replace("\n", " ")
        return compact[:18] if compact else "未命名兴趣"

    def _summarize(self, type: CaptureType, tags: list[str]) -> str:
        source_name = "链接" if type == "url" else "内容"
        visible_tags = "、".join(tags[:2])
        return f"用户收藏了一个{source_name}，并记录了关于 {visible_tags} 的即时感想。"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_manxiang_capture.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/manxiang/capture.py tests/test_manxiang_capture.py
git commit -m "feat: add lightweight capture processor"
```

---

### Task 4: Implement Topic Discovery and Maturity Scoring

**Files:**
- Create: `app/manxiang/topics.py`
- Test: `tests/test_manxiang_topics.py`

- [ ] **Step 1: Write the failing topic discovery test**

```python
# tests/test_manxiang_topics.py
from app.manxiang.schema import CaptureItem
from app.manxiang.topics import TopicDiscoverer


def make_capture(index: int, topic: str, note: str) -> CaptureItem:
    return CaptureItem(
        id=f"cap_{index:03d}",
        type="text",
        source=f"source {index}",
        user_note=note,
        captured_at="2026-08-02T20:00:00+08:00",
        tags=["AI 陪伴"],
        emotion_keywords=["困惑"],
        candidate_topics=[topic],
        status="light_tagged",
    )


def test_topic_discoverer_marks_five_related_captures_ready():
    captures = [
        make_capture(i, "AI 陪伴与亲密关系", f"为什么 AI 陪伴让人觉得真实？第 {i} 条")
        for i in range(5)
    ]
    discoverer = TopicDiscoverer()

    topics = discoverer.discover(captures)

    assert len(topics) == 1
    assert topics[0].name == "AI 陪伴与亲密关系"
    assert topics[0].status == "ready"
    assert topics[0].maturity_score >= 0.8
    assert topics[0].suggested_action == "升级为知识地图"


def test_topic_discoverer_keeps_small_topic_as_fragment():
    captures = [make_capture(1, "AI 味写作", "这个表达很像 AI。")]
    discoverer = TopicDiscoverer()

    topics = discoverer.discover(captures)

    assert topics[0].status == "fragment"
    assert topics[0].suggested_action == "继续收集"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_manxiang_topics.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.manxiang.topics'`.

- [ ] **Step 3: Implement topic discoverer**

```python
# app/manxiang/topics.py
from collections import defaultdict
from hashlib import sha1

from app.manxiang.schema import CaptureItem, TopicCluster, TopicStatus


class TopicDiscoverer:
    """Find repeated interests from lightweight captures."""

    def discover(self, captures: list[CaptureItem]) -> list[TopicCluster]:
        grouped: dict[str, list[CaptureItem]] = defaultdict(list)
        for capture in captures:
            for topic in capture.candidate_topics:
                grouped[topic].append(capture)

        clusters = [self._build_cluster(topic, items) for topic, items in grouped.items()]
        return sorted(clusters, key=lambda cluster: cluster.maturity_score, reverse=True)

    def _build_cluster(self, topic: str, captures: list[CaptureItem]) -> TopicCluster:
        count = len(captures)
        emotion_count = sum(1 for capture in captures if capture.emotion_keywords)
        question_count = sum(1 for capture in captures if self._looks_like_question(capture.user_note))
        maturity_score = min(1.0, count / 5 * 0.7 + min(emotion_count, 2) / 2 * 0.2 + min(question_count, 3) / 3 * 0.1)
        status = self._status_for(count=count, maturity_score=maturity_score)
        return TopicCluster(
            id=self._topic_id(topic),
            name=topic,
            status=status,
            capture_ids=[capture.id for capture in captures],
            repeated_questions=self._questions(captures),
            emotion_patterns=self._emotion_patterns(captures),
            maturity_score=round(maturity_score, 2),
            suggested_action=self._suggested_action(status),
        )

    def _topic_id(self, topic: str) -> str:
        return "topic_" + sha1(topic.encode("utf-8")).hexdigest()[:10]

    def _looks_like_question(self, text: str) -> bool:
        return "为什么" in text or "怎么" in text or "?" in text or "？" in text

    def _questions(self, captures: list[CaptureItem]) -> list[str]:
        questions = []
        for capture in captures:
            if self._looks_like_question(capture.user_note):
                questions.append(capture.user_note)
        return questions[:3]

    def _emotion_patterns(self, captures: list[CaptureItem]) -> list[str]:
        patterns: list[str] = []
        for capture in captures:
            for emotion in capture.emotion_keywords:
                if emotion not in patterns:
                    patterns.append(emotion)
        return patterns

    def _status_for(self, count: int, maturity_score: float) -> TopicStatus:
        if count >= 5 and maturity_score >= 0.75:
            return "ready"
        if count >= 3:
            return "gathering"
        return "fragment"

    def _suggested_action(self, status: TopicStatus) -> str:
        if status == "ready":
            return "升级为知识地图"
        if status == "gathering":
            return "先做问题地图"
        return "继续收集"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_manxiang_topics.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/manxiang/topics.py tests/test_manxiang_topics.py
git commit -m "feat: discover manxiang topic clusters"
```

---

### Task 5: Implement Task Navigation and Mainline Recommendation

**Files:**
- Create: `app/manxiang/navigation.py`
- Test: `tests/test_manxiang_navigation.py`

- [ ] **Step 1: Write the failing navigation test**

```python
# tests/test_manxiang_navigation.py
from app.manxiang.navigation import TaskNavigator
from app.manxiang.schema import CaptureItem, TopicCluster


def test_navigator_creates_task_and_recommends_causal_line():
    topic = TopicCluster(
        id="topic_001",
        name="AI 陪伴与亲密关系",
        status="ready",
        capture_ids=["cap_001", "cap_002"],
        repeated_questions=["为什么 AI 陪伴让人觉得真实？"],
        emotion_patterns=["困惑"],
        maturity_score=0.9,
        suggested_action="升级为知识地图",
    )
    captures = [
        CaptureItem(
            id="cap_001",
            type="text",
            source="source",
            user_note="为什么 AI 陪伴让人觉得真实？",
            captured_at="2026-08-02T20:00:00+08:00",
            tags=["AI 陪伴", "真实感"],
            candidate_topics=["AI 陪伴与亲密关系"],
        )
    ]
    navigator = TaskNavigator(clock=lambda: "2026-08-02T20:00:00+08:00")

    task = navigator.create_task(topic, mode="gentle_editor")
    line_plan = navigator.recommend_line(task, captures)

    assert task.stage == "scoping"
    assert task.default_output == "knowledge_map"
    assert line_plan.recommended_line == "causal"
    assert line_plan.selected_line == "causal"
    assert line_plan.line_nodes


def test_navigator_explains_risk_before_line_override():
    navigator = TaskNavigator(clock=lambda: "2026-08-02T20:00:00+08:00")

    notes = navigator.explain_line_override(current="causal", requested="emotion")

    assert "个人表达" in notes[0]
    assert "逻辑严谨度" in notes[1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_manxiang_navigation.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.manxiang.navigation'`.

- [ ] **Step 3: Implement task navigator**

```python
# app/manxiang/navigation.py
from collections.abc import Callable

from app.manxiang.schema import AgentMode, CaptureItem, LineNode, LinePlan, LineType, ResearchTask, TopicCluster


class TaskNavigator:
    """Owns task scope, mainline selection, and user override warnings."""

    def __init__(self, clock: Callable[[], str]):
        self.clock = clock

    def create_task(self, topic: TopicCluster, mode: AgentMode) -> ResearchTask:
        now = self.clock()
        return ResearchTask(
            id=topic.id.replace("topic_", "task_", 1),
            title=self._title_for(topic.name),
            topic_id=topic.id,
            stage="scoping",
            default_output="knowledge_map",
            mode=mode,
            goal=f"生成一张解释「{topic.name}」的文本 + 树状图知识地图",
            core_question=self._core_question_for(topic),
            completion_definition="形成文本 + 树状图知识地图，并标出证据缺口和停车场分支",
            allowed_scope=["用户心理", "产品机制", "典型案例"],
            blocked_scope=["底层模型架构", "融资细节", "无关技术史"],
            created_at=now,
            updated_at=now,
        )

    def recommend_line(self, task: ResearchTask, captures: list[CaptureItem]) -> LinePlan:
        joined = " ".join([capture.user_note for capture in captures] + [task.core_question, task.title])
        recommended = self._recommend_line_type(joined)
        auxiliary = self._auxiliary_lines(joined, recommended)
        nodes = self._nodes_for(recommended)
        return LinePlan(
            task_id=task.id,
            recommended_line=recommended,
            selected_line=recommended,
            auxiliary_lines=auxiliary,
            recommendation_reason=self._reason_for(recommended),
            risk_notes=[],
            line_nodes=nodes,
        )

    def explain_line_override(self, current: LineType, requested: LineType) -> list[str]:
        if current == requested:
            return []
        if requested == "emotion":
            return [
                "切换到情绪/个人触动线会让文章更有个人表达。",
                "风险是逻辑严谨度会下降，建议保留原主线作为分析骨架。",
            ]
        if requested == "timeline":
            return [
                "切换到时间线会更适合讲演变过程。",
                "风险是如果资料没有阶段变化，地图会显得松散。",
            ]
        if requested == "stakeholder":
            return [
                "切换到人物/利益线会更适合商业和社会议题。",
                "风险是需要更多关于平台、用户、监管或公司的证据。",
            ]
        return [
            "切换主线会改变知识地图的组织方式。",
            "风险是当前资料可能不支撑新的主线，需要重新检查证据缺口。",
        ]

    def _title_for(self, topic_name: str) -> str:
        if topic_name == "AI 陪伴与亲密关系":
            return "AI 陪伴为什么让人觉得像真的"
        return topic_name

    def _core_question_for(self, topic: TopicCluster) -> str:
        if topic.repeated_questions:
            return topic.repeated_questions[0]
        return f"我真正想通过「{topic.name}」搞懂什么？"

    def _recommend_line_type(self, text: str) -> LineType:
        if "为什么" in text or "原因" in text:
            return "causal"
        if "发展" in text or "历史" in text or "阶段" in text:
            return "timeline"
        if "谁" in text or "公司" in text or "平台" in text or "利益" in text:
            return "stakeholder"
        if "我" in text or "触动" in text or "感受" in text:
            return "emotion"
        return "question"

    def _auxiliary_lines(self, text: str, recommended: LineType) -> list[LineType]:
        candidates: list[LineType] = []
        if recommended != "emotion" and ("我" in text or "触动" in text or "感受" in text):
            candidates.append("emotion")
        if recommended != "question":
            candidates.append("question")
        return candidates[:2]

    def _reason_for(self, line_type: LineType) -> str:
        reasons = {
            "causal": "用户感想和问题集中在「为什么会这样」，适合用因果线组织。",
            "timeline": "资料更适合按阶段演变理解，适合用时间线组织。",
            "question": "当前还处在探索期，适合用问题线逐步搞懂。",
            "stakeholder": "主题涉及多个角色和利益关系，适合用人物/利益线组织。",
            "emotion": "用户个人触动很强，适合用情绪/个人触动线作为显性主线。",
        }
        return reasons[line_type]

    def _nodes_for(self, line_type: LineType) -> list[LineNode]:
        if line_type == "causal":
            titles = ["需求背景", "低风险表达", "即时回应", "记忆与人格化", "陪伴感形成"]
        elif line_type == "timeline":
            titles = ["早期形态", "关键转折", "当下状态", "下一阶段"]
        elif line_type == "stakeholder":
            titles = ["用户", "产品平台", "内容生态", "监管与社会影响"]
        elif line_type == "emotion":
            titles = ["最初触动", "反复出现的困惑", "个人判断", "回到公共问题"]
        else:
            titles = ["我已知道什么", "我还不懂什么", "哪个问题最关键", "下一步验证什么"]
        return [
            LineNode(
                id=f"line_{index + 1}",
                title=title,
                kind="mainline",
                summary=f"围绕「{title}」整理当前资料。",
                depth_limit=2,
                status="expandable",
            )
            for index, title in enumerate(titles[:5])
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_manxiang_navigation.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/manxiang/navigation.py tests/test_manxiang_navigation.py
git commit -m "feat: add manxiang task navigation"
```

---

### Task 6: Generate Text + Tree Knowledge Map

**Files:**
- Create: `app/manxiang/maps.py`
- Test: `tests/test_manxiang_maps.py`

- [ ] **Step 1: Write the failing map test**

```python
# tests/test_manxiang_maps.py
from app.manxiang.maps import KnowledgeMapBuilder
from app.manxiang.schema import LineNode, LinePlan, ResearchTask


def test_map_builder_creates_limited_text_and_tree_views():
    task = ResearchTask(
        id="task_001",
        title="AI 陪伴为什么让人觉得像真的",
        topic_id="topic_001",
        stage="line_chosen",
        default_output="knowledge_map",
        mode="gentle_editor",
        goal="生成知识地图",
        core_question="为什么 AI 陪伴让人觉得真实？",
        completion_definition="形成文本 + 树状图知识地图",
        allowed_scope=["用户心理"],
        blocked_scope=["模型架构"],
        created_at="2026-08-02T20:00:00+08:00",
        updated_at="2026-08-02T20:00:00+08:00",
    )
    line_plan = LinePlan(
        task_id=task.id,
        recommended_line="causal",
        selected_line="causal",
        auxiliary_lines=["emotion"],
        recommendation_reason="适合解释为什么。",
        risk_notes=[],
        line_nodes=[
            LineNode(id="line_1", title="低风险表达", kind="mainline", summary="用户表达成本降低。", depth_limit=2, status="expandable"),
            LineNode(id="line_2", title="即时回应", kind="mainline", summary="随时得到回应。", depth_limit=2, status="expandable"),
        ],
    )
    builder = KnowledgeMapBuilder()

    knowledge_map = builder.build(task, line_plan, concepts=["情绪价值", "长期记忆"], evidence_titles=["用户访谈"], gaps=["长期使用动机"])

    assert knowledge_map.text_view.core_question == task.core_question
    assert "低风险表达 -> 即时回应" in knowledge_map.text_view.mainline_summary
    root_labels = [child.label for child in knowledge_map.tree.children]
    assert "核心问题" in root_labels
    assert "推荐主线" in root_labels
    assert "分支停车场" in root_labels
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_manxiang_maps.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.manxiang.maps'`.

- [ ] **Step 3: Implement knowledge map builder**

```python
# app/manxiang/maps.py
from app.manxiang.schema import KnowledgeMap, LinePlan, ResearchTask, TextView, TreeNode


class KnowledgeMapBuilder:
    """Build the default MVP output: text explanation plus read-only tree."""

    def build(
        self,
        task: ResearchTask,
        line_plan: LinePlan,
        concepts: list[str],
        evidence_titles: list[str],
        gaps: list[str],
    ) -> KnowledgeMap:
        limited_nodes = line_plan.line_nodes[:5]
        mainline_summary = " -> ".join(node.title for node in limited_nodes)
        text_view = TextView(
            core_question=task.core_question,
            mainline_summary=mainline_summary,
            recommendation_reason=line_plan.recommendation_reason,
            next_action=self._next_action(gaps),
        )
        tree = TreeNode(
            id="root",
            label=task.title,
            kind="root",
            children=[
                TreeNode(id="core_question", label="核心问题", kind="core_question"),
                TreeNode(
                    id="mainline",
                    label="推荐主线",
                    kind="mainline",
                    children=[
                        TreeNode(id=node.id, label=node.title, kind="mainline")
                        for node in limited_nodes
                    ],
                ),
                TreeNode(
                    id="concepts",
                    label="关键概念",
                    kind="concept",
                    children=[
                        TreeNode(id=f"concept_{index + 1}", label=concept, kind="concept")
                        for index, concept in enumerate(concepts[:7])
                    ],
                ),
                TreeNode(
                    id="evidence",
                    label="证据材料",
                    kind="evidence",
                    children=[
                        TreeNode(id=f"evidence_{index + 1}", label=title, kind="evidence")
                        for index, title in enumerate(evidence_titles[:10])
                    ],
                ),
                TreeNode(
                    id="evidence_gaps",
                    label="证据缺口",
                    kind="evidence_gap",
                    children=[
                        TreeNode(id=f"gap_{index + 1}", label=gap, kind="evidence_gap")
                        for index, gap in enumerate(gaps[:5])
                    ],
                ),
                TreeNode(id="parking_lot", label="分支停车场", kind="parking_lot"),
                TreeNode(id="next_action", label=text_view.next_action, kind="next_action"),
            ],
        )
        return KnowledgeMap(task_id=task.id, version=1, text_view=text_view, tree=tree)

    def _next_action(self, gaps: list[str]) -> str:
        if gaps:
            return f"补充证据：{gaps[0]}"
        return "确认知识地图，决定是否升级为短札记或主题报告"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_manxiang_maps.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/manxiang/maps.py tests/test_manxiang_maps.py
git commit -m "feat: build manxiang knowledge maps"
```

---

### Task 7: Add Detour Intervention and Parking Lot Decisions

**Files:**
- Create: `app/manxiang/intervention.py`
- Test: `tests/test_manxiang_intervention.py`

- [ ] **Step 1: Write the failing intervention test**

```python
# tests/test_manxiang_intervention.py
from app.manxiang.intervention import InterventionPolicy


def test_strict_mode_refuses_low_relevance_detour():
    policy = InterventionPolicy()

    decision = policy.decide(
        mode="strict_mentor",
        detour_title="语音克隆技术史",
        relevance_score=0.1,
    )

    assert decision.level == "refuse"
    assert decision.should_park is True
    assert "不会继续展开" in decision.message


def test_gentle_mode_timeboxes_medium_relevance_detour():
    policy = InterventionPolicy()

    decision = policy.decide(
        mode="gentle_editor",
        detour_title="长期记忆产品机制",
        relevance_score=0.45,
    )

    assert decision.level == "limit"
    assert decision.timebox_minutes == 5
    assert decision.should_park is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_manxiang_intervention.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.manxiang.intervention'`.

- [ ] **Step 3: Implement intervention policy**

```python
# app/manxiang/intervention.py
from app.manxiang.schema import AgentMode, InterventionDecision


class InterventionPolicy:
    """Translate detour relevance and mode into a concrete intervention."""

    def decide(self, mode: AgentMode, detour_title: str, relevance_score: float) -> InterventionDecision:
        if mode == "strict_mentor":
            return self._strict(detour_title, relevance_score)
        if mode == "gentle_editor":
            return self._gentle(detour_title, relevance_score)
        return self._buddy(detour_title, relevance_score)

    def _strict(self, detour_title: str, relevance_score: float) -> InterventionDecision:
        if relevance_score < 0.3:
            return InterventionDecision(
                level="refuse",
                message=f"「{detour_title}」已经偏离本轮目标。我不会继续展开，会先放进停车场。",
                should_park=True,
            )
        return InterventionDecision(
            level="limit",
            message=f"「{detour_title}」和主线有一定关系，但严格导师模式下最多深入 5 分钟。",
            should_park=False,
            timebox_minutes=5,
        )

    def _gentle(self, detour_title: str, relevance_score: float) -> InterventionDecision:
        if relevance_score < 0.2:
            return InterventionDecision(
                level="remind",
                message=f"「{detour_title}」有趣，但现在只和主线弱相关。我建议先放进停车场。",
                should_park=True,
            )
        return InterventionDecision(
            level="limit",
            message=f"可以短暂看一下「{detour_title}」，目标只是判断它是否服务当前主线。",
            should_park=False,
            timebox_minutes=5,
        )

    def _buddy(self, detour_title: str, relevance_score: float) -> InterventionDecision:
        if relevance_score < 0.15:
            return InterventionDecision(
                level="remind",
                message=f"「{detour_title}」像是一个新分支，我会提醒你稍后收束。",
                should_park=False,
                timebox_minutes=15,
            )
        return InterventionDecision(
            level="remind",
            message=f"可以探索「{detour_title}」，我会在 15 分钟后帮你判断是否进入主线。",
            should_park=False,
            timebox_minutes=15,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_manxiang_intervention.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/manxiang/intervention.py tests/test_manxiang_intervention.py
git commit -m "feat: add manxiang detour intervention"
```

---

### Task 8: Guard Evidence Patching and Search Provider

**Files:**
- Create: `app/manxiang/evidence.py`
- Test: `tests/test_manxiang_evidence.py`

- [ ] **Step 1: Write the failing evidence test**

```python
# tests/test_manxiang_evidence.py
import pytest

from app.manxiang.evidence import EvidencePatcher, FakeSearchProvider
from app.manxiang.schema import EvidenceGap, ResearchTask


def make_task(stage: str) -> ResearchTask:
    return ResearchTask(
        id="task_001",
        title="AI 陪伴为什么让人觉得像真的",
        topic_id="topic_001",
        stage=stage,
        default_output="knowledge_map",
        mode="gentle_editor",
        goal="生成知识地图",
        core_question="为什么 AI 陪伴让人觉得真实？",
        completion_definition="形成知识地图",
        allowed_scope=["用户心理"],
        blocked_scope=["模型架构"],
        created_at="2026-08-02T20:00:00+08:00",
        updated_at="2026-08-02T20:00:00+08:00",
    )


def test_evidence_patcher_rejects_search_outside_evidence_stage():
    patcher = EvidencePatcher(search_provider=FakeSearchProvider([]), clock=lambda: "2026-08-02T20:00:00+08:00")
    gap = EvidenceGap(
        id="gap_001",
        task_id="task_001",
        node_id="line_1",
        description="缺少长期使用动机证据",
        search_goal="找用户研究",
        stop_condition="找到 2 条可用证据后停止",
    )

    with pytest.raises(ValueError, match="只允许在补证据阶段搜索"):
        patcher.patch(make_task("map_drafted"), gap, query="AI companion user motivation")


def test_evidence_patcher_converts_search_results_to_evidence():
    provider = FakeSearchProvider(
        [
            {
                "title": "AI companion user report",
                "url": "https://example.com/report",
                "snippet": "Users mention immediate response and low-pressure expression.",
            }
        ]
    )
    patcher = EvidencePatcher(search_provider=provider, clock=lambda: "2026-08-02T20:00:00+08:00")
    gap = EvidenceGap(
        id="gap_001",
        task_id="task_001",
        node_id="line_1",
        description="缺少长期使用动机证据",
        search_goal="找用户研究",
        stop_condition="找到 2 条可用证据后停止",
    )

    evidence = patcher.patch(make_task("evidence_patching"), gap, query="AI companion user motivation")

    assert len(evidence) == 1
    assert evidence[0].supports_node_id == "line_1"
    assert evidence[0].strength == "medium"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_manxiang_evidence.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.manxiang.evidence'`.

- [ ] **Step 3: Implement evidence patcher**

```python
# app/manxiang/evidence.py
from collections.abc import Callable, Protocol
from hashlib import sha1
from typing import Any

from app.manxiang.schema import EvidenceGap, EvidenceItem, ResearchTask, SearchResult


class SearchProvider(Protocol):
    def search(self, query: str) -> list[SearchResult]:
        raise NotImplementedError


class FakeSearchProvider:
    """Deterministic provider for tests and local demos."""

    def __init__(self, rows: list[dict[str, Any]]):
        self.rows = rows

    def search(self, query: str) -> list[SearchResult]:
        return [
            SearchResult(
                title=str(row["title"]),
                url=str(row["url"]),
                snippet=str(row["snippet"]),
            )
            for row in self.rows
        ]


class EvidencePatcher:
    """Allow search only when the task is explicitly patching evidence."""

    ALLOWED_STAGES = {"evidence_gap_found", "evidence_patching"}

    def __init__(self, search_provider: SearchProvider, clock: Callable[[], str]):
        self.search_provider = search_provider
        self.clock = clock

    def patch(self, task: ResearchTask, gap: EvidenceGap, query: str) -> list[EvidenceItem]:
        if task.stage not in self.ALLOWED_STAGES:
            raise ValueError("只允许在补证据阶段搜索")
        if gap.task_id != task.id:
            raise ValueError("证据缺口必须属于当前研究任务")
        if not gap.search_goal.strip() or not gap.stop_condition.strip():
            raise ValueError("搜索前必须有搜索目标和停止条件")

        results = self.search_provider.search(query)
        return [self._to_evidence(task, gap, result) for result in results[:3]]

    def _to_evidence(self, task: ResearchTask, gap: EvidenceGap, result: SearchResult) -> EvidenceItem:
        digest = sha1(f"{task.id}|{gap.id}|{result.url}".encode("utf-8")).hexdigest()[:10]
        return EvidenceItem(
            id=f"ev_{digest}",
            task_id=task.id,
            source_type="web",
            source_url=result.url,
            title=result.title,
            summary=result.snippet,
            supports_node_id=gap.node_id,
            evidence_type="external_source",
            strength="medium",
            retrieved_at=self.clock(),
            status="usable",
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_manxiang_evidence.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/manxiang/evidence.py tests/test_manxiang_evidence.py
git commit -m "feat: guard manxiang evidence search"
```

---

### Task 9: Add Pipeline Facade and CLI Demo

**Files:**
- Create: `app/manxiang/pipeline.py`
- Create: `examples/07_manxiang_mvp.py`
- Test: `tests/test_manxiang_pipeline.py`

- [ ] **Step 1: Write the failing pipeline test**

```python
# tests/test_manxiang_pipeline.py
from app.manxiang.pipeline import ManxiangPipeline


def test_pipeline_turns_captures_into_ready_topic_and_map(tmp_path):
    pipeline = ManxiangPipeline(storage_root=tmp_path, clock=lambda: "2026-08-02T20:00:00+08:00")

    for index in range(5):
        pipeline.capture(
            type="text",
            source=f"note {index}",
            user_note=f"为什么 AI 陪伴让人觉得真实和被理解？第 {index} 条",
        )

    topics = pipeline.discover_topics()
    task, line_plan, knowledge_map = pipeline.create_knowledge_map(topics[0].id, mode="gentle_editor")

    assert topics[0].status == "ready"
    assert task.stage == "scoping"
    assert line_plan.recommended_line == "causal"
    assert knowledge_map.tree.label == task.title
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_manxiang_pipeline.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.manxiang.pipeline'`.

- [ ] **Step 3: Implement pipeline facade**

```python
# app/manxiang/pipeline.py
from collections.abc import Callable
from pathlib import Path

from app.manxiang.capture import CaptureProcessor
from app.manxiang.maps import KnowledgeMapBuilder
from app.manxiang.navigation import TaskNavigator
from app.manxiang.schema import AgentMode, CaptureItem, CaptureType, KnowledgeMap, LinePlan, ResearchTask, TopicCluster
from app.manxiang.storage import JsonStore
from app.manxiang.topics import TopicDiscoverer


class ManxiangPipeline:
    """Simple facade for the MVP workflow."""

    def __init__(self, storage_root: str | Path, clock: Callable[[], str]):
        self.store = JsonStore(storage_root)
        self.capture_processor = CaptureProcessor(clock=clock)
        self.topic_discoverer = TopicDiscoverer()
        self.navigator = TaskNavigator(clock=clock)
        self.map_builder = KnowledgeMapBuilder()

    def capture(self, type: CaptureType, source: str, user_note: str, raw_text: str = "") -> CaptureItem:
        item = self.capture_processor.capture(type=type, source=source, user_note=user_note, raw_text=raw_text)
        self.store.save_capture(item)
        return item

    def discover_topics(self) -> list[TopicCluster]:
        topics = self.topic_discoverer.discover(self.store.list_captures())
        for topic in topics:
            self.store.save_topic(topic)
        return topics

    def create_knowledge_map(self, topic_id: str, mode: AgentMode) -> tuple[ResearchTask, LinePlan, KnowledgeMap]:
        topics = {topic.id: topic for topic in self.store.list_topics()}
        if topic_id not in topics:
            raise ValueError(f"Unknown topic id: {topic_id}")
        topic = topics[topic_id]
        captures = [
            capture
            for capture in self.store.list_captures()
            if capture.id in topic.capture_ids
        ]
        task = self.navigator.create_task(topic, mode=mode)
        line_plan = self.navigator.recommend_line(task, captures)
        concepts = self._concepts_from(captures)
        evidence_titles = [capture.summary for capture in captures[:3]]
        gaps = ["长期使用动机", "真实用户反馈"] if topic.status == "ready" else ["核心问题还不清楚"]
        knowledge_map = self.map_builder.build(
            task=task,
            line_plan=line_plan,
            concepts=concepts,
            evidence_titles=evidence_titles,
            gaps=gaps,
        )
        self.store.save_task(task)
        self.store.save_map(knowledge_map)
        return task, line_plan, knowledge_map

    def _concepts_from(self, captures: list[CaptureItem]) -> list[str]:
        concepts: list[str] = []
        for capture in captures:
            for tag in capture.tags:
                if tag not in concepts and tag != "未分类":
                    concepts.append(tag)
        return concepts[:7]
```

- [ ] **Step 4: Add CLI demo**

```python
# examples/07_manxiang_mvp.py
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

try:
    from examples import _bootstrap  # noqa: F401
except ModuleNotFoundError:
    import _bootstrap  # noqa: F401

from app.manxiang.pipeline import ManxiangPipeline


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def main() -> None:
    storage_root = Path(".manxiang-demo")
    pipeline = ManxiangPipeline(storage_root=storage_root, clock=now)
    notes = [
        "为什么 AI 陪伴让人觉得真实和被理解？",
        "明知道是 AI，为什么还是有人会依赖？",
        "AI 陪伴的即时回应是不是降低了表达压力？",
        "长期记忆会不会增强被理解的感觉？",
        "这类产品为什么能让人产生亲密感？",
    ]
    for index, note in enumerate(notes):
        pipeline.capture(type="text", source=f"demo note {index + 1}", user_note=note)

    topics = pipeline.discover_topics()
    task, line_plan, knowledge_map = pipeline.create_knowledge_map(topics[0].id, mode="gentle_editor")

    print("=== Topics ===")
    print(json.dumps([asdict(topic) for topic in topics], ensure_ascii=False, indent=2))
    print("\n=== Task ===")
    print(json.dumps(asdict(task), ensure_ascii=False, indent=2))
    print("\n=== Line Plan ===")
    print(json.dumps(asdict(line_plan), ensure_ascii=False, indent=2))
    print("\n=== Knowledge Map ===")
    print(json.dumps(asdict(knowledge_map), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run pipeline test**

Run: `uv run pytest tests/test_manxiang_pipeline.py -v`

Expected: PASS.

- [ ] **Step 6: Run CLI demo**

Run: `uv run python examples/07_manxiang_mvp.py`

Expected: output sections named `=== Topics ===`, `=== Task ===`, `=== Line Plan ===`, and `=== Knowledge Map ===`.

- [ ] **Step 7: Commit**

```bash
git add app/manxiang/pipeline.py examples/07_manxiang_mvp.py tests/test_manxiang_pipeline.py
git commit -m "feat: add manxiang mvp pipeline demo"
```

---

### Task 10: Document the MVP and Run Full Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with 慢想 demo instructions**

Add this section after the existing "运行示例" section:

```markdown
## 慢想 MVP 核心演示

慢想第一版先实现 Python 核心闭环，不急着做前端：

```bash
uv run python examples/07_manxiang_mvp.py
```

这个演示会模拟 5 条关于 AI 陪伴的收藏和即时感想，然后依次输出：

- 主题发现结果；
- 研究任务；
- 主线推荐；
- 文本 + 树状知识地图。

慢想的第一版重点不是联网搜索，也不是自动写长文，而是验证：

> 能不能把随手收藏的内容，整理成一张有主线、有证据缺口、有停车场边界的知识地图。
```

- [ ] **Step 2: Run all tests**

Run: `uv run pytest`

Expected: all tests PASS.

- [ ] **Step 3: Run the demo**

Run: `uv run python examples/07_manxiang_mvp.py`

Expected: command exits 0 and prints valid JSON sections.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: describe manxiang mvp demo"
```

---

## Self-Review

### Spec Coverage

- Product positioning: covered by deterministic MVP core and README demo.
- User scenes: capture, topic discovery, research task creation, knowledge map generation are covered.
- Core flow: covered by `ManxiangPipeline`.
- Agent architecture: implemented as deterministic processors with clear boundaries.
- State machine: represented through schema literals and guarded evidence stage.
- Data structures: implemented in `schema.py`.
- MVP scope: implemented core engine, no UI or browser plugin.
- Later iteration gaps: writing upgrade, style memory, editable graph, browser plugin, and long-term archive are intentionally excluded from this plan and should get separate plans.

### Placeholder Scan

This plan avoids open-ended placeholders. Every created module has concrete test expectations and implementation code.

### Type Consistency

- Status literals use lowercase snake-case values across schema and tests.
- `ResearchTask.stage` values in tests match the schema literals.
- `LinePlan.recommended_line` values match `LineType`.
- `KnowledgeMap.tree` uses nested `TreeNode` objects consistently.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-02-manxiang-mvp-core.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
