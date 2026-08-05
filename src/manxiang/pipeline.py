from collections.abc import Callable
from pathlib import Path

from manxiang.capture import CaptureProcessor
from manxiang.maps import KnowledgeMapBuilder
from manxiang.navigation import TaskNavigator
from manxiang.schema import AgentMode, CaptureItem, CaptureType, KnowledgeMap, LinePlan, ResearchTask, TopicCluster
from manxiang.storage import JsonStore
from manxiang.topics import TopicDiscoverer


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
            raise ValueError(
                f"Unknown topic id: {topic_id}. Run discover_topics() before creating a knowledge map."
            )
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
