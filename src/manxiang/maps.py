from manxiang.schema import KnowledgeMap, LinePlan, ResearchTask, TextView, TreeNode


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
                        TreeNode(id=f"map_mainline_{node.id}", label=node.title, kind="mainline")
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
