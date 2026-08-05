from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPANISH_ROYAL_IMAGE = PROJECT_ROOT / "docs/superpowers/specs/assets/2026-08-05-spanish-royal-family.png"


def v0b_capture_fixtures() -> list[dict[str, str]]:
    return [
        {
            "id": "cap_1",
            "source_type": "text",
            "original_text": "伊莎贝拉和伊丽莎白两个著名的女王有血缘关系。",
        },
        {
            "id": "cap_2",
            "source_type": "text",
            "original_text": "普拉多博物馆有很多西班牙王室故事为背景的画作。",
        },
        {
            "id": "cap_3",
            "source_type": "text",
            "original_text": "费利佩和菲利普只是一个英文的不同音译。",
        },
        {
            "id": "cap_4",
            "source_type": "url",
            "source_uri": "https://www.bjnews.com.cn/detail/173352872819482.html",
        },
        {
            "id": "cap_5",
            "source_type": "mixed",
            "source_uri": str(SPANISH_ROYAL_IMAGE),
            "user_note": "欧洲真人人有亲缘啊",
        },
        {
            "id": "cap_6",
            "source_type": "url",
            "source_uri": "https://zhuanlan.zhihu.com/p/300938362",
            "user_note": "伊莎贝拉女王和哥伦布相关，感觉能串起来了",
        },
    ]
