from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
# The runner is executed as a source-tree script, so expose the src package path.
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from manxiang.evals import score_agent_map

CASE_PATH = ROOT / "evals" / "manxiang" / "cases" / "spanish_royal_family.json"
RUBRIC_PATH = ROOT / "evals" / "manxiang" / "rubrics" / "research_map.json"
REPORT_DIR = ROOT / "evals" / "manxiang" / "reports"
NOT_SCORED = ["stage_compliance", "over_search_penalty"]


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_thresholds(
    score: dict[str, float],
    passing: dict[str, float],
    not_scored: list[str],
) -> list[dict[str, object]]:
    failures: list[dict[str, object]] = []
    for field, threshold in passing.items():
        if field in not_scored:
            continue
        value = score.get(field, 0.0)
        if field.endswith("_penalty"):
            passed = value <= threshold
            operator = "<="
        else:
            passed = value >= threshold
            operator = ">="
        if not passed:
            failures.append(
                {
                    "field": field,
                    "score": value,
                    "expected": threshold,
                    "operator": operator,
                }
            )
    return failures


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    case = load_json(CASE_PATH)
    rubric_config = load_json(RUBRIC_PATH)
    passing = rubric_config["passing"]
    sample_map = {
        "nodes": [
            {"id": "n1", "confidence": "hypothesis", "source_refs": []},
            {"id": "n2", "confidence": "fact", "source_refs": [{"chunk_id": "chunk_1"}]},
        ],
        "evidence_gaps": [{"id": "gap_1", "search_query": "Isabella Columbus patronage"}],
        "mainline": ["王室亲缘", "普拉多图像", "哥伦布航海"],
    }
    score = score_agent_map(sample_map)
    failures = evaluate_thresholds(score, passing, NOT_SCORED)
    report = {
        "case_id": case["id"],
        "case": case,
        "score": score,
        "passed": not failures,
        "failures": failures,
        "rubric": passing,
        "not_scored": NOT_SCORED,
    }
    (REPORT_DIR / "spanish_royal_family.latest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
