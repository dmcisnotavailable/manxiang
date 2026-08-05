from collections.abc import Callable
from hashlib import sha1
from typing import Any, Protocol

from manxiang.schema import EvidenceGap, EvidenceItem, ResearchTask, SearchResult


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

    ALLOWED_STAGES = {"evidence_patching"}

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
        if not query.strip():
            raise ValueError("搜索前必须有明确查询词")

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
