from manxiang.evals import score_agent_map


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
