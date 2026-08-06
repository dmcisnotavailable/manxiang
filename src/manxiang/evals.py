from __future__ import annotations

from typing import Any


def score_agent_map(agent_map: dict[str, Any]) -> dict[str, float]:
    nodes = agent_map.get("nodes", [])
    fact_nodes = [node for node in nodes if node.get("confidence") == "fact"]
    cited_fact_nodes = [node for node in fact_nodes if node.get("source_refs")]
    source_grounding = 1.0 if not fact_nodes else len(cited_fact_nodes) / len(fact_nodes)
    hallucination_penalty = 0.0 if source_grounding == 1.0 else round(1.0 - source_grounding, 2)
    evidence_gaps = agent_map.get("evidence_gaps", [])
    searchable_gaps = [gap for gap in evidence_gaps if gap.get("search_query")]
    evidence_precision = 1.0 if evidence_gaps and len(searchable_gaps) == len(evidence_gaps) else 0.5
    mainline = agent_map.get("mainline", [])
    map_coherence = 1.0 if len(mainline) >= 3 else 0.5
    return {
        "stage_compliance": 1.0,
        "source_grounding": round(source_grounding, 2),
        "map_coherence": map_coherence,
        "evidence_precision": evidence_precision,
        "hallucination_penalty": hallucination_penalty,
        "over_search_penalty": 0.0,
    }
