import json
import sys
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from manxiang.fixtures import v0b_capture_fixtures
from manxiang.pipeline import ManxiangPipeline
from manxiang.runs import create_run


def now() -> str:
    return "2026-08-05T20:00:00+08:00"


def main() -> None:
    with TemporaryDirectory(prefix="manxiang-demo-") as tmpdir:
        pipeline = ManxiangPipeline(storage_root=Path(tmpdir), clock=now)
        captures = []
        for fixture in v0b_capture_fixtures():
            capture = pipeline.capture(
                type=_capture_type_for(fixture),
                source=fixture.get("source_uri", "manual"),
                user_note=fixture.get("user_note", ""),
                raw_text=fixture.get("original_text", ""),
            )
            captures.append(capture)

        topics = pipeline.discover_topics()
        run = create_run(pipeline.store, [capture.id for capture in captures], clock=now)
        events = pipeline.store.replay_events(run.id)

        print("=== V0b Captures ===")
        print(json.dumps([asdict(capture) for capture in captures], ensure_ascii=False, indent=2))
        print("=== Topics ===")
        print(json.dumps([asdict(topic) for topic in topics], ensure_ascii=False, indent=2))
        print("\n=== Surprise Run ===")
        print(json.dumps(asdict(run), ensure_ascii=False, indent=2))
        print("\n=== Event Replay ===")
        print(json.dumps([asdict(event) for event in events], ensure_ascii=False, indent=2))


def _capture_type_for(fixture: dict[str, str]) -> str:
    if fixture["source_type"] == "url":
        return "url"
    if fixture["source_type"] == "mixed":
        return "screenshot_note"
    return "text"


if __name__ == "__main__":
    main()
