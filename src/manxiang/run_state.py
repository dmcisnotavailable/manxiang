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
