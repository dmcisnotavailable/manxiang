from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from manxiang.evals import score_agent_map

REPORT_DIR = ROOT / "evals" / "manxiang" / "reports"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    sample_map = {
        "nodes": [
            {"id": "n1", "confidence": "hypothesis", "source_refs": []},
            {"id": "n2", "confidence": "fact", "source_refs": [{"chunk_id": "chunk_1"}]},
        ],
        "evidence_gaps": [{"id": "gap_1", "search_query": "Isabella Columbus patronage"}],
        "mainline": ["王室亲缘", "普拉多图像", "哥伦布航海"],
    }
    report = {
        "case_id": "spanish_royal_family",
        "score": score_agent_map(sample_map),
    }
    (REPORT_DIR / "spanish_royal_family.latest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
