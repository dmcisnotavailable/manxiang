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
