from __future__ import annotations

from typing import Any


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def score_agent_map(agent_map: dict[str, Any]) -> dict[str, float]:
    nodes_value = agent_map.get("nodes", [])
    evidence_gaps_value = agent_map.get("evidence_gaps", [])
    mainline = agent_map.get("mainline", [])
    structure_errors = [
        "nodes" in agent_map and not isinstance(nodes_value, list),
        isinstance(nodes_value, list) and any(not isinstance(node, dict) for node in nodes_value),
        "evidence_gaps" in agent_map and not isinstance(evidence_gaps_value, list),
        isinstance(evidence_gaps_value, list) and any(not isinstance(gap, dict) for gap in evidence_gaps_value),
        not (isinstance(mainline, list) and all(isinstance(item, str) for item in mainline)),
    ]
    stage_compliance = 0.0 if any(structure_errors) else 1.0
    nodes = _dict_items(nodes_value)
    fact_nodes = [node for node in nodes if node.get("confidence") == "fact"]
    cited_fact_nodes = [node for node in fact_nodes if node.get("source_refs")]
    source_grounding = 1.0 if not fact_nodes else len(cited_fact_nodes) / len(fact_nodes)
    hallucination_penalty = 0.0 if source_grounding == 1.0 else round(1.0 - source_grounding, 2)
    evidence_gaps = _dict_items(evidence_gaps_value)
    searchable_gaps = [gap for gap in evidence_gaps if gap.get("search_query")]
    evidence_precision = 1.0 if evidence_gaps and len(searchable_gaps) == len(evidence_gaps) else 0.5
    valid_mainline = mainline if isinstance(mainline, list) and all(isinstance(item, str) for item in mainline) else []
    map_coherence = 1.0 if len(valid_mainline) >= 3 else 0.5
    return {
        "stage_compliance": stage_compliance,
        "source_grounding": round(source_grounding, 2),
        "map_coherence": map_coherence,
        "evidence_precision": evidence_precision,
        "hallucination_penalty": hallucination_penalty,
        "over_search_penalty": 0.0,
    }
