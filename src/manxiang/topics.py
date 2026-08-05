from collections import defaultdict
from hashlib import sha1

from manxiang.schema import CaptureItem, TopicCluster, TopicStatus


class TopicDiscoverer:
    """Find repeated interests from lightweight captures."""

    def discover(self, captures: list[CaptureItem]) -> list[TopicCluster]:
        grouped: dict[str, list[CaptureItem]] = defaultdict(list)
        for capture in captures:
            for topic in self._unique_topics(capture.candidate_topics):
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

    def _unique_topics(self, topics: list[str]) -> list[str]:
        unique: list[str] = []
        for topic in topics:
            if topic not in unique:
                unique.append(topic)
        return unique

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
