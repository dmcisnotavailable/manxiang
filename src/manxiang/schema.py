from dataclasses import dataclass, field
from typing import Literal


CaptureType = Literal["url", "text", "screenshot_note", "video_note"]
CaptureStatus = Literal["new", "captured", "light_tagged", "clustered", "used_in_task", "parked", "archived"]
SourceType = Literal["text", "image", "url", "mixed"]
SummaryStatus = Literal["summary_pending", "summary_confirmed", "summary_rejected"]
ParseStatus = Literal["not_parsed", "metadata_parsed", "parse_failed"]
SourceParseStatus = Literal["not_parsed", "parse_requested", "parsed", "parse_failed", "parse_skipped"]
EmbeddingStatus = Literal["not_embedded", "embedded", "embedding_failed"]
RunStatus = Literal["queued", "exploring", "waiting_user", "completed", "failed", "aborted"]
AutonomyLevel = Literal["inbox_only", "source_parse_allowed", "web_search_allowed"]
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
NodeConfidence = Literal["user_impression", "hypothesis", "needs_evidence", "fact"]
EvidenceStrength = Literal["weak", "medium", "strong"]
EvidenceStatus = Literal["usable", "weak_related", "discarded"]
InterventionLevel = Literal["remind", "limit", "refuse"]
CheckpointStage = Literal[
    "captured",
    "topic_discovered",
    "research_scoped",
    "map_drafted",
    "evidence_patched",
    "map_reviewed",
]


def default_run_budget() -> dict[str, int]:
    return {
        "max_turns": 8,
        "max_tool_calls": 16,
        "max_search_queries": 0,
        "max_source_parses": 0,
    }


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
