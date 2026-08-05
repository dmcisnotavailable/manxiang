import json
import sys
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from manxiang.pipeline import ManxiangPipeline


def now() -> str:
    return "2026-08-02T20:00:00+08:00"


def main() -> None:
    with TemporaryDirectory(prefix="manxiang-demo-") as tmpdir:
        pipeline = ManxiangPipeline(storage_root=Path(tmpdir), clock=now)
        notes = [
            "为什么 AI 陪伴让人觉得真实和被理解？",
            "明知道是 AI，为什么还是有人会依赖？",
            "AI 陪伴的即时回应是不是降低了表达压力？",
            "AI 陪伴的长期记忆会不会增强被理解的感觉？",
            "AI 陪伴这类产品为什么能让人产生亲密感？",
        ]
        for index, note in enumerate(notes):
            pipeline.capture(type="text", source=f"demo note {index + 1}", user_note=note)

        topics = pipeline.discover_topics()
        task, line_plan, knowledge_map = pipeline.create_knowledge_map(topics[0].id, mode="gentle_editor")

        print("=== Topics ===")
        print(json.dumps([asdict(topic) for topic in topics], ensure_ascii=False, indent=2))
        print("\n=== Task ===")
        print(json.dumps(asdict(task), ensure_ascii=False, indent=2))
        print("\n=== Line Plan ===")
        print(json.dumps(asdict(line_plan), ensure_ascii=False, indent=2))
        print("\n=== Knowledge Map ===")
        print(json.dumps(asdict(knowledge_map), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
