import importlib.util
import json
from pathlib import Path

from manxiang.evals import score_agent_map


RUN_EVAL_PATH = Path(__file__).resolve().parents[1] / "evals" / "manxiang" / "run_eval.py"
RUN_EVAL_SPEC = importlib.util.spec_from_file_location("manxiang_eval_runner", RUN_EVAL_PATH)
assert RUN_EVAL_SPEC is not None
assert RUN_EVAL_SPEC.loader is not None
run_eval = importlib.util.module_from_spec(RUN_EVAL_SPEC)
RUN_EVAL_SPEC.loader.exec_module(run_eval)


def test_score_agent_map_rewards_sources_and_penalizes_fact_without_refs():
    score = score_agent_map(
        {
            "nodes": [
                {"id": "n1", "confidence": "fact", "source_refs": []},
                {"id": "n2", "confidence": "hypothesis", "source_refs": []},
            ],
            "evidence_gaps": [{"id": "gap_1", "search_query": "Isabella Columbus patronage"}],
            "mainline": ["名字和谱系分开", "王室图像叙事", "航海扩张叙事"],
        }
    )

    assert score["source_grounding"] < 1.0
    assert score["hallucination_penalty"] > 0
    assert score["map_coherence"] == 1.0


def test_score_agent_map_tolerates_bad_shapes_and_requires_string_list_mainline():
    score = score_agent_map(
        {
            "nodes": [
                "not a node",
                {"id": "n1", "confidence": "fact", "source_refs": [{"chunk_id": "chunk_1"}]},
                None,
            ],
            "evidence_gaps": [
                "not a gap",
                {"id": "gap_1", "search_query": "Isabella Columbus patronage"},
            ],
            "mainline": "abc",
        }
    )

    assert score["source_grounding"] == 1.0
    assert score["evidence_precision"] == 1.0
    assert score["map_coherence"] == 0.5

    empty_score = score_agent_map(
        {
            "nodes": {"id": "n1", "confidence": "fact", "source_refs": []},
            "evidence_gaps": "not a list",
            "mainline": ["only one"],
        }
    )

    assert empty_score["source_grounding"] == 1.0
    assert empty_score["evidence_precision"] == 0.5


def test_eval_runner_writes_rubric_based_report(tmp_path, monkeypatch):
    monkeypatch.setattr(run_eval, "REPORT_DIR", tmp_path)

    run_eval.main()

    report_path = tmp_path / "spanish_royal_family.latest.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["case_id"] == "spanish_royal_family"
    assert report["case"]["id"] == "spanish_royal_family"
    assert report["rubric"]["source_grounding"] == 0.8
    assert report["passed"] is True
    assert report["failures"] == []
    assert report["not_scored"] == ["stage_compliance", "over_search_penalty"]
