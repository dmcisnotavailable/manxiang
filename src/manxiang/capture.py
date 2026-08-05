from collections.abc import Callable
from hashlib import sha1
from pathlib import Path
import re

from manxiang.schema import CaptureItem, CaptureType, SourceType
from manxiang.source_adapters import ParsedSource, infer_v0b_topics, parse_url_light


class CaptureProcessor:
    """Lightweight capture processor.

    The collection phase must stay shallow: save the input, infer rough tags,
    and avoid opening a research rabbit hole.
    """

    def __init__(self, clock: Callable[[], str]):
        self.clock = clock

    def capture(self, type: CaptureType, source: str, user_note: str = "", raw_text: str = "") -> CaptureItem:
        captured_at = self.clock()
        item_id = self._make_id(source=source, user_note=user_note, raw_text=raw_text, captured_at=captured_at)
        source_type = self._source_type_for(type=type, source=source)
        original_text = raw_text or (source if source_type == "text" else "")
        parsed = self._parse_source(source_type=source_type, source=source, user_note=user_note)
        all_text = " ".join([source, user_note, raw_text, parsed.ai_summary_draft])
        tags = self._infer_tags(" ".join([source, user_note, raw_text]))
        emotion_keywords = self._infer_emotions(user_note)
        candidate_topics = self._infer_topics(tags, user_note, all_text, parsed.candidate_topics)
        summary = self._summarize(type, tags)
        attachment_ids = [Path(source).name] if source_type in {"image", "mixed"} and Path(source).exists() else []
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
            source_type=source_type,
            source_uri=source if source_type in {"url", "image", "mixed"} else "",
            original_text=original_text,
            ai_summary_draft=parsed.ai_summary_draft,
            summary_status="summary_pending",
            parse_status=parsed.parse_status,
            attachment_ids=attachment_ids,
        )

    def _make_id(self, source: str, user_note: str, raw_text: str, captured_at: str) -> str:
        digest = sha1(f"{source}|{user_note}|{raw_text}|{captured_at}".encode("utf-8")).hexdigest()[:10]
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
            ("王室", "欧洲王室"),
            ("女王", "欧洲王室"),
            ("普拉多", "艺术史"),
            ("哥伦布", "大航海"),
            ("费利佩", "译名"),
            ("菲利普", "译名"),
            ("spanish", "欧洲王室"),
            ("royal", "欧洲王室"),
        ]
        tags: list[str] = []
        for keyword, tag in rules:
            if self._contains_keyword(text, keyword) and tag not in tags:
                tags.append(tag)
        return tags or ["未分类"]

    def _contains_keyword(self, text: str, keyword: str) -> bool:
        if keyword == "AI":
            return re.search(r"(?<![a-zA-Z])ai(?![a-zA-Z])", text, flags=re.IGNORECASE) is not None
        return keyword.lower() in text.lower()

    def _infer_emotions(self, user_note: str) -> list[str]:
        emotions: list[str] = []
        if "为什么" in user_note or "?" in user_note or "？" in user_note:
            emotions.append("困惑")
        if "觉得" in user_note or "被理解" in user_note:
            emotions.append("被触动")
        return emotions

    def _infer_topics(
        self,
        tags: list[str],
        user_note: str,
        all_text: str = "",
        parsed_topics: list[str] | None = None,
    ) -> list[str]:
        topics: list[str] = []
        if "AI 陪伴" in tags or "真实感" in tags:
            topics.append("AI 陪伴与亲密关系")
        if "注意力管理" in tags:
            topics.append("注意力管理与信息摄入")
        if "去 AI 味写作" in tags:
            topics.append("AI 味写作")
        for topic in [*(parsed_topics or []), *infer_v0b_topics(all_text)]:
            if topic not in topics:
                topics.append(topic)
        if not topics:
            topics.append(self._fallback_topic(user_note))
        return topics

    def _source_type_for(self, type: CaptureType, source: str) -> SourceType:
        if type == "url" or source.startswith(("http://", "https://")):
            return "url"
        if type == "screenshot_note":
            return "mixed"
        if source.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            return "image"
        return "text"

    def _parse_source(self, source_type: SourceType, source: str, user_note: str) -> ParsedSource:
        if source_type == "url":
            return parse_url_light(source, user_note=user_note)
        return ParsedSource(parse_status="not_parsed", candidate_topics=infer_v0b_topics(f"{source} {user_note}"))

    def _fallback_topic(self, user_note: str) -> str:
        compact = user_note.strip().replace("\n", " ")
        return compact[:18] if compact else "未命名兴趣"

    def _summarize(self, type: CaptureType, tags: list[str]) -> str:
        source_name = "链接" if type == "url" else "内容"
        visible_tags = "、".join(tags[:2])
        return f"用户收藏了一个{source_name}，并记录了关于 {visible_tags} 的即时感想。"
