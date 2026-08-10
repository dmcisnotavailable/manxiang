from dataclasses import dataclass, field
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ParsedSource:
    parse_status: str
    ai_summary_draft: str = ""
    candidate_topics: list[str] = field(default_factory=list)


def infer_v0b_topics(text: str) -> list[str]:
    normalized = text.lower()
    rules = [
        ("普拉多", "普拉多博物馆"),
        ("西班牙", "西班牙王室"),
        ("spanish", "西班牙王室"),
        ("王室", "欧洲王室亲缘"),
        ("royal", "欧洲王室亲缘"),
        ("伊莎贝拉", "伊莎贝拉女王"),
        ("伊丽莎白", "伊丽莎白女王"),
        ("费利佩", "王室译名"),
        ("菲利普", "王室译名"),
        ("哥伦布", "哥伦布"),
    ]
    topics: list[str] = []
    for keyword, topic in rules:
        if keyword in normalized and topic not in topics:
            topics.append(topic)
    return topics


def parse_url_light(source_uri: str, user_note: str = "", timeout: float = 3.0) -> ParsedSource:
    try:
        request = Request(source_uri, headers={"User-Agent": "ManxiangV0b/0.1"})
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(4096).decode("utf-8", errors="ignore")
        text = f"{source_uri}\n{user_note}\n{raw[:1000]}"
        return ParsedSource(
            parse_status="metadata_parsed",
            ai_summary_draft=text[:300],
            candidate_topics=infer_v0b_topics(text),
        )
    except Exception:
        text = f"{source_uri}\n{user_note}"
        return ParsedSource(
            parse_status="parse_failed",
            ai_summary_draft="",
            candidate_topics=infer_v0b_topics(text),
        )
