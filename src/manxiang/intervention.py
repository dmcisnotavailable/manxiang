from manxiang.schema import AgentMode, InterventionDecision


class InterventionPolicy:
    """Translate detour relevance and mode into a concrete intervention."""

    def decide(self, mode: AgentMode, detour_title: str, relevance_score: float) -> InterventionDecision:
        if mode == "strict_mentor":
            return self._strict(detour_title, relevance_score)
        if mode == "gentle_editor":
            return self._gentle(detour_title, relevance_score)
        if mode == "research_buddy":
            return self._buddy(detour_title, relevance_score)
        raise ValueError(f"Unknown agent mode: {mode}")

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
