from __future__ import annotations

import shutil
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from manxiang.fixtures import v0b_capture_fixtures
from manxiang.pipeline import ManxiangPipeline
from manxiang.runs import confirm_search, create_run, run_surprise_with_bridge
from manxiang.schema import AgentMode, AgentRun, CaptureType, KnowledgeMap, LinePlan, ResearchTask
from manxiang.source_parser import SourceParser


class WorkbenchService:
    """Small stateful bridge between the prototype UI and ManxiangPipeline."""

    def __init__(self, storage_root: str | Path, clock=lambda: "2026-08-02T20:00:00+08:00"):
        self.storage_root = Path(storage_root)
        self.clock = clock
        self._reset_runtime()

    def reset(self) -> dict[str, Any]:
        if self.storage_root.exists():
            shutil.rmtree(self.storage_root)
        self._reset_runtime()
        return self.state()

    def capture(
        self,
        type: CaptureType = "text",
        source: str = "工作台输入",
        user_note: str = "",
        raw_text: str = "",
    ) -> dict[str, Any]:
        self.pipeline.capture(type=type, source=source or "工作台输入", user_note=user_note, raw_text=raw_text)
        self._clear_downstream()
        return self.state()

    def seed_demo(self) -> dict[str, Any]:
        self.reset()
        for fixture in v0b_capture_fixtures():
            self.pipeline.capture(
                type=_capture_type_for_fixture(fixture),
                source=fixture.get("source_uri", "manual"),
                user_note=fixture.get("user_note", ""),
                raw_text=fixture.get("original_text", ""),
            )
        self.discover_topics()
        return self.state()

    def create_surprise_run(self, run_bridge: bool = False, bridge=None) -> dict[str, Any]:
        captures = self.pipeline.store.list_captures()
        if not captures:
            raise ValueError("captures are required before surprise run")
        run = create_run(self.pipeline.store, [capture.id for capture in captures], clock=self.clock)
        self.surprise_run = _to_jsonable(run)
        if run_bridge:
            self.surprise_result = run_surprise_with_bridge(
                self.pipeline.store,
                run,
                captures,
                bridge=bridge,
                clock=self.clock,
            )
            if self.surprise_result.get("run"):
                self.surprise_run = self.surprise_result["run"]
            self._sync_agent_outputs(run.id)
        return self.state()

    def confirm_run_search(self, run_id: str, gap_id: str, max_search_queries: int = 3) -> dict[str, Any]:
        if not self.surprise_run or self.surprise_run.get("id") != run_id:
            raise ValueError(f"Unknown run id: {run_id}")
        run = AgentRun(**self.surprise_run)
        run = confirm_search(self.pipeline.store, run, gap_id, max_search_queries, clock=self.clock)
        self.surprise_run = _to_jsonable(run)
        return self.state()

    def discover_topics(self) -> dict[str, Any]:
        topics = self.pipeline.discover_topics()
        self.topics = [_to_jsonable(topic) for topic in topics]
        if self.topics and not self.selected_topic_id:
            self.selected_topic_id = self.topics[0]["id"]
        self._clear_task_outputs()
        return self.state()

    def select_topic(self, topic_id: str) -> dict[str, Any]:
        if not topic_id:
            raise ValueError("topic_id is required")
        self.selected_topic_id = topic_id
        self._clear_task_outputs()
        return self.state()

    def create_knowledge_map(self, topic_id: str | None = None, mode: AgentMode = "gentle_editor") -> dict[str, Any]:
        if not self.topics:
            self.discover_topics()
        selected = topic_id or self.selected_topic_id
        if not selected:
            raise ValueError("topic_id is required")
        self.selected_topic_id = selected
        task, line_plan, knowledge_map = self.pipeline.create_knowledge_map(selected, mode=mode)
        self.task = _task_view(task)
        self.line_plan = _line_plan_view(line_plan)
        self.knowledge_map = _map_view(knowledge_map)
        self.draft = ""
        self.draft_type = "outline"
        return self.state()

    def create_draft(self, draft_type: str = "outline") -> dict[str, Any]:
        if not self.knowledge_map or not self.task:
            raise ValueError("knowledge_map is required before drafting")
        self.draft_type = "note" if draft_type == "note" else "outline"
        self.draft = _draft_for(self.draft_type, self.task, self.knowledge_map)
        return self.state()

    def park_branch(self, title: str = "新出现的偏题分支") -> dict[str, Any]:
        if title not in self.parking:
            self.parking.append(title)
        return self.state()

    def patch_evidence_hint(self) -> dict[str, Any]:
        gaps = self.knowledge_map.get("gaps", []) if self.knowledge_map else []
        self.notice = f"补证据入口：{gaps[0]}" if gaps else "当前还没有明确证据缺口"
        return self.state()

    def state(self) -> dict[str, Any]:
        return {
            "captures": [_to_jsonable(capture) for capture in self.pipeline.store.list_captures()],
            "topics": self.topics,
            "selectedTopicId": self.selected_topic_id,
            "task": self.task,
            "linePlan": self.line_plan,
            "map": self.knowledge_map,
            "agentMap": self.agent_map,
            "draftType": self.draft_type,
            "draft": self.draft,
            "parking": self.parking,
            "notice": self.notice,
            "surpriseRun": self.surprise_run,
            "surpriseResult": self.surprise_result,
        }

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
            "sourceChunks": self.v1_source_chunks,
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

    def _reset_runtime(self) -> None:
        self.pipeline = ManxiangPipeline(storage_root=self.storage_root, clock=self.clock)
        self.topics: list[dict[str, Any]] = []
        self.selected_topic_id = ""
        self.task: dict[str, Any] | None = None
        self.line_plan: dict[str, Any] | None = None
        self.knowledge_map: dict[str, Any] | None = None
        self.agent_map: dict[str, Any] | None = None
        self.draft_type = "outline"
        self.draft = ""
        self.parking = ["底层模型架构", "语音克隆技术史"]
        self.notice = ""
        self.surprise_run: dict[str, Any] | None = None
        self.surprise_result: dict[str, Any] | None = None
        self.v1_source_chunks: list[dict[str, Any]] = []

    def _clear_downstream(self) -> None:
        self.topics = []
        self.selected_topic_id = ""
        self.v1_source_chunks = []
        self._clear_task_outputs()

    def _clear_task_outputs(self) -> None:
        self.task = None
        self.line_plan = None
        self.knowledge_map = None
        self.agent_map = None
        self.draft = ""
        self.draft_type = "outline"
        self.surprise_run = None
        self.surprise_result = None

    def _sync_agent_outputs(self, run_id: str) -> None:
        maps = [event.payload for event in self.pipeline.store.replay_events(run_id) if event.type == "map.created"]
        if not maps:
            return
        self.agent_map = maps[-1]
        self.knowledge_map = _agent_map_view(self.agent_map)


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value


def _capture_type_for_fixture(fixture: dict[str, str]) -> CaptureType:
    if fixture["source_type"] == "url":
        return "url"
    if fixture["source_type"] == "mixed":
        return "screenshot_note"
    return "text"


def _task_view(task: ResearchTask) -> dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "topicId": task.topic_id,
        "mode": _mode_label(task.mode),
        "output": "知识地图",
        "coreQuestion": task.core_question,
        "allowed": task.allowed_scope,
        "blocked": task.blocked_scope,
        "goal": task.goal,
        "stage": task.stage,
    }


def _line_plan_view(line_plan: LinePlan) -> dict[str, Any]:
    return {
        "recommendedLine": _line_label(line_plan.selected_line),
        "auxiliary": [_line_label(line) for line in line_plan.auxiliary_lines],
        "reason": line_plan.recommendation_reason,
        "nodes": [node.title for node in line_plan.line_nodes],
        "riskNotes": line_plan.risk_notes,
    }


def _map_view(knowledge_map: KnowledgeMap) -> dict[str, Any]:
    root = knowledge_map.tree
    mainline = _child_labels(root, "mainline")
    concepts = _child_labels(root, "concept")
    evidence = _child_labels(root, "evidence")
    gaps = _child_labels(root, "evidence_gap")
    return {
        "taskId": knowledge_map.task_id,
        "version": knowledge_map.version,
        "title": root.label,
        "coreQuestion": knowledge_map.text_view.core_question,
        "mainline": mainline,
        "concepts": concepts,
        "evidence": evidence,
        "gaps": gaps,
        "nextAction": knowledge_map.text_view.next_action,
        "recommendationReason": knowledge_map.text_view.recommendation_reason,
        "tree": _tree_view(root),
    }


def _agent_map_view(agent_map: dict[str, Any]) -> dict[str, Any]:
    insights = agent_map.get("non_obvious_insights", [])
    gaps = agent_map.get("evidence_gaps", [])
    mainline = agent_map.get("mainline", [])
    known_unknowns = agent_map.get("known_unknowns", [])
    title = agent_map.get("title", "Agent 分析知识图")
    core_question = agent_map.get("core_question", "")
    thesis = agent_map.get("thesis", "")
    return {
        "taskId": agent_map.get("id", "agent_map"),
        "version": agent_map.get("version", 1),
        "title": title,
        "coreQuestion": core_question,
        "mainline": mainline,
        "concepts": [item.get("claim", "") for item in insights],
        "evidence": [item.get("why_interesting", "") for item in insights],
        "gaps": [gap.get("description", "") for gap in gaps],
        "nextAction": gaps[0].get("search_query", "选择一个证据缺口开始验证") if gaps else "确认 Agent 分析方向",
        "recommendationReason": thesis,
        "tree": {
            "id": agent_map.get("id", "agent_map"),
            "label": title,
            "kind": "root",
            "children": [
                {"id": "core_question", "label": core_question, "kind": "core_question", "children": []},
                {
                    "id": "mainline",
                    "label": "Agent 推荐主线",
                    "kind": "mainline",
                    "children": [
                        {"id": f"mainline_{index + 1}", "label": item, "kind": "mainline", "children": []}
                        for index, item in enumerate(mainline)
                    ],
                },
                {
                    "id": "insights",
                    "label": "非显而易见洞察",
                    "kind": "concept",
                    "children": [
                        {
                            "id": f"insight_{index + 1}",
                            "label": item.get("claim", ""),
                            "kind": "concept",
                            "children": [
                                {
                                    "id": f"insight_{index + 1}_why",
                                    "label": item.get("why_interesting", ""),
                                    "kind": "evidence",
                                    "children": [],
                                }
                            ],
                        }
                        for index, item in enumerate(insights)
                    ],
                },
                {
                    "id": "known_unknowns",
                    "label": "待澄清问题",
                    "kind": "evidence_gap",
                    "children": [
                        {"id": f"unknown_{index + 1}", "label": item, "kind": "evidence_gap", "children": []}
                        for index, item in enumerate(known_unknowns)
                    ],
                },
                {
                    "id": "evidence_gaps",
                    "label": "可执行证据缺口",
                    "kind": "evidence_gap",
                    "children": [
                        {
                            "id": gap.get("id", f"gap_{index + 1}"),
                            "label": f"{gap.get('description', '')}｜检索：{gap.get('search_query', '')}",
                            "kind": "evidence_gap",
                            "children": [],
                        }
                        for index, gap in enumerate(gaps)
                    ],
                },
            ],
        },
    }


def _tree_view(node) -> dict[str, Any]:
    return {
        "id": node.id,
        "label": node.label,
        "kind": node.kind,
        "children": [_tree_view(child) for child in node.children],
    }


def _child_labels(root, kind: str) -> list[str]:
    for child in root.children:
        if child.kind == kind:
            return [grandchild.label for grandchild in child.children]
    return []


def _draft_for(draft_type: str, task: dict[str, Any], knowledge_map: dict[str, Any]) -> str:
    if draft_type == "note":
        return (
            "我真正想弄清楚的是：\n"
            f"{knowledge_map['coreQuestion']}\n\n"
            "目前看，关键不只是模型多聪明，而是它提供了一种低风险表达空间："
            "不用担心被评价，也能立刻得到回应。\n\n"
            "但这里还有两个证据缺口："
            f"{'、'.join(knowledge_map['gaps'])}。"
        )
    gaps = "\n".join(f"- {gap}" for gap in knowledge_map["gaps"])
    return (
        f"标题：\n{task['title']}\n\n"
        "一、问题从哪里来\n"
        "- 需求背景\n"
        "- 用户为什么会产生陪伴需求\n\n"
        "二、为什么 AI 陪伴降低表达压力\n"
        "- 低风险表达\n"
        "- 即时回应\n\n"
        "三、陪伴感如何形成\n"
        "- 记忆与人格化\n"
        "- 持续互动\n\n"
        "四、目前证据不足的地方\n"
        f"{gaps}\n\n"
        "五、下一步要补什么\n"
        "- 找 2-3 条用户研究或产品案例"
    )


def _line_label(line: str) -> str:
    labels = {
        "causal": "因果线",
        "timeline": "时间线",
        "question": "问题线",
        "stakeholder": "人物/利益线",
        "emotion": "情绪/个人触动线",
    }
    return labels.get(line, line)


def _mode_label(mode: str) -> str:
    labels = {
        "strict_mentor": "严格导师型",
        "gentle_editor": "温和编辑型",
        "research_buddy": "研究搭子型",
    }
    return labels.get(mode, mode)
