from manxiang.storage import JsonStore


def reduce_tool_result(store: JsonStore, run_id: str, tool_name: str, payload: dict) -> None:
    if tool_name == "generate_spark_cards":
        for card in payload["spark_cards"]:
            if not card.get("source_capture_ids"):
                raise ValueError("SparkCard requires source_capture_ids")
            store.append_event(run_id, "spark.card.created", card)
        return

    if tool_name == "draft_tweet_seeds":
        for seed in payload["tweet_seeds"]:
            if not seed.get("source_capture_ids"):
                raise ValueError("TweetSeed requires source_capture_ids")
            store.append_event(run_id, "tweet.seed.created", seed)
        return

    if tool_name == "mine_collection_surprises":
        for insight in payload["connection_insights"]:
            store.append_event(run_id, "connection.insight.created", insight)
        return

    if tool_name == "propose_exploration_threads":
        for thread in payload["threads"]:
            store.append_event(run_id, "exploration.thread.proposed", thread)
        store.append_event(run_id, "line.recommended", {"recommended_thread_id": payload["recommended_thread_id"]})
        return

    if tool_name == "synthesize_exploration_board":
        store.append_event(run_id, "exploration.board.created", payload["exploration_board"])
        return

    if tool_name == "generate_knowledge_map":
        nodes = payload["map"].get("nodes", [])
        if payload["map"].get("version") == 1 and any(node.get("confidence") == "fact" for node in nodes):
            raise ValueError("KnowledgeMap v1 cannot create fact nodes")
        store.append_event(run_id, "map.created", payload["map"])
        return

    if tool_name == "mark_evidence_gap":
        for gap in payload["gaps"]:
            store.append_event(run_id, "evidence.gap.detected", gap)
        return

    if tool_name == "search_evidence":
        store.append_event(run_id, "evidence.search.started", payload)
        return

    if tool_name == "attach_evidence":
        store.append_event(run_id, "evidence.attached", payload["evidence"])
        store.append_event(run_id, "map.updated", payload["map"])
        return

    if tool_name == "draft_expression_variants":
        for draft in payload["drafts"]:
            store.append_event(run_id, "expression.draft.created", draft)
        return

    raise ValueError(f"Unknown reducer tool: {tool_name}")
