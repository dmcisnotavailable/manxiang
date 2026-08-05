from collections.abc import Callable
from hashlib import sha1

from manxiang.schema import CaptureItem, CaptureType


class CaptureProcessor:
    """Lightweight capture processor.

    The collection phase must stay shallow: save the input, infer rough tags,
    and avoid opening a research rabbit hole.
    """

    def __init__(self, clock: Callable[[], str]):
        self.clock = clock

    def capture(self, type: CaptureType, source: str, user_note: str, raw_text: str = "") -> CaptureItem:
        captured_at = self.clock()
        item_id = self._make_id(source=source, user_note=user_note, captured_at=captured_at)
        tags = self._infer_tags(" ".join([source, user_note, raw_text]))
        emotion_keywords = self._infer_emotions(user_note)
        candidate_topics = self._infer_topics(tags, user_note)
        summary = self._summarize(type, tags)
        return CaptureItem(
            id=item_id,
            type=type,
            source=source,
            raw_text=raw_text,
            user_note=user_note,
            captured_at=captured_at,
            summary=summary,
            tags=tags,
            emotion_keywords=emotion_keywords,
            candidate_topics=candidate_topics,
            status="light_tagged",
        )

    def _make_id(self, source: str, user_note: str, captured_at: str) -> str:
        digest = sha1(f"{source}|{user_note}|{captured_at}".encode("utf-8")).hexdigest()[:10]
        return f"cap_{digest}"

    def _infer_tags(self, text: str) -> list[str]:
        rules = [
            ("AI", "AI 陪伴"),
            ("陪伴", "AI 陪伴"),
            ("被理解", "真实感"),
            ("真实", "真实感"),
            ("依赖", "依赖"),
            ("孤独", "孤独感"),
            ("写作", "去 AI 味写作"),
            ("注意力", "注意力管理"),
            ("跑偏", "注意力管理"),
        ]
        tags: list[str] = []
        for keyword, tag in rules:
            if keyword.lower() in text.lower() and tag not in tags:
                tags.append(tag)
        return tags or ["未分类"]

    def _infer_emotions(self, user_note: str) -> list[str]:
        emotions: list[str] = []
        if "为什么" in user_note or "?" in user_note or "？" in user_note:
            emotions.append("困惑")
        if "觉得" in user_note or "被理解" in user_note:
            emotions.append("被触动")
        return emotions

    def _infer_topics(self, tags: list[str], user_note: str) -> list[str]:
        topics: list[str] = []
        if "AI 陪伴" in tags or "真实感" in tags:
            topics.append("AI 陪伴与亲密关系")
        if "注意力管理" in tags:
            topics.append("注意力管理与信息摄入")
        if "去 AI 味写作" in tags:
            topics.append("AI 味写作")
        if not topics:
            topics.append(self._fallback_topic(user_note))
        return topics

    def _fallback_topic(self, user_note: str) -> str:
        compact = user_note.strip().replace("\n", " ")
        return compact[:18] if compact else "未命名兴趣"

    def _summarize(self, type: CaptureType, tags: list[str]) -> str:
        source_name = "链接" if type == "url" else "内容"
        visible_tags = "、".join(tags[:2])
        return f"用户收藏了一个{source_name}，并记录了关于 {visible_tags} 的即时感想。"
