from __future__ import annotations

from typing import Any


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def score_agent_map(agent_map: dict[str, Any]) -> dict[str, float]:
    nodes = _dict_items(agent_map.get("nodes", []))
    fact_nodes = [node for node in nodes if node.get("confidence") == "fact"]
    cited_fact_nodes = [node for node in fact_nodes if node.get("source_refs")]
    source_grounding = 1.0 if not fact_nodes else len(cited_fact_nodes) / len(fact_nodes)
    hallucination_penalty = 0.0 if source_grounding == 1.0 else round(1.0 - source_grounding, 2)
    evidence_gaps = _dict_items(agent_map.get("evidence_gaps", []))
    searchable_gaps = [gap for gap in evidence_gaps if gap.get("search_query")]
    evidence_precision = 1.0 if evidence_gaps and len(searchable_gaps) == len(evidence_gaps) else 0.5
    mainline = agent_map.get("mainline", [])
    valid_mainline = mainline if isinstance(mainline, list) and all(isinstance(item, str) for item in mainline) else []
    map_coherence = 1.0 if len(valid_mainline) >= 3 else 0.5
    return {
        "stage_compliance": 1.0,
        "source_grounding": round(source_grounding, 2),
        "map_coherence": map_coherence,
        "evidence_precision": evidence_precision,
        "hallucination_penalty": hallucination_penalty,
        "over_search_penalty": 0.0,
    }
