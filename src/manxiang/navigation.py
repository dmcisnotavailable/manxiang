from collections.abc import Callable

from manxiang.schema import AgentMode, CaptureItem, LineNode, LinePlan, LineType, ResearchTask, TopicCluster


class TaskNavigator:
    """Owns task scope, mainline selection, and user override warnings."""

    def __init__(self, clock: Callable[[], str]):
        self.clock = clock

    def create_task(self, topic: TopicCluster, mode: AgentMode) -> ResearchTask:
        now = self.clock()
        return ResearchTask(
            id=self._task_id_for(topic.id),
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
        real_notes = [capture.user_note for capture in captures]
        real_questions = [] if self._is_default_core_question(task.core_question) else [task.core_question]
        joined = " ".join(real_notes + real_questions + [task.title])
        emotion_text = " ".join(real_notes + real_questions)
        recommended = self._recommend_line_type(joined, emotion_text=emotion_text)
        auxiliary = self._auxiliary_lines(joined, recommended, emotion_text=emotion_text)
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

    def _task_id_for(self, topic_id: str) -> str:
        if topic_id.startswith("topic_"):
            return topic_id.replace("topic_", "task_", 1)
        return f"task_{topic_id}"

    def _title_for(self, topic_name: str) -> str:
        if topic_name == "AI 陪伴与亲密关系":
            return "AI 陪伴为什么让人觉得像真的"
        return topic_name

    def _core_question_for(self, topic: TopicCluster) -> str:
        if topic.repeated_questions:
            return topic.repeated_questions[0]
        return f"我真正想通过「{topic.name}」搞懂什么？"

    def _is_default_core_question(self, core_question: str) -> bool:
        return core_question.startswith("我真正想通过「") and core_question.endswith("」搞懂什么？")

    def _recommend_line_type(self, text: str, emotion_text: str) -> LineType:
        if "为什么" in text or "原因" in text:
            return "causal"
        if "发展" in text or "历史" in text or "阶段" in text:
            return "timeline"
        if "谁" in text or "公司" in text or "平台" in text or "利益" in text:
            return "stakeholder"
        if "我" in emotion_text or "触动" in emotion_text or "感受" in emotion_text:
            return "emotion"
        return "question"

    def _auxiliary_lines(self, text: str, recommended: LineType, emotion_text: str) -> list[LineType]:
        candidates: list[LineType] = []
        if recommended != "emotion" and ("我" in emotion_text or "触动" in emotion_text or "感受" in emotion_text):
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
