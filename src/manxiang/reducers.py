from manxiang.storage import JsonStore


TEMPLATE_PLACEHOLDERS = [
    "我已知道什么",
    "我还不懂什么",
    "哪个问题最关键",
    "下一步验证什么",
    "核心问题还不清楚",
]


def reduce_tool_result(store: JsonStore, run_id: str, tool_name: str, payload: dict) -> None:
    if tool_name == "record_collection_reading":
        reading = payload["reading"]
        if not reading.get("hypotheses"):
            raise ValueError("CollectionReading requires hypotheses")
        for hypothesis in reading["hypotheses"]:
            if not hypothesis.get("source_capture_ids"):
                raise ValueError("CollectionReading hypothesis requires source_capture_ids")
        store.append_event(run_id, "collection.reading.recorded", payload)
        return

    if tool_name in {"generate_spark_cards", "create_spark_cards"}:
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

    if tool_name == "create_knowledge_map":
        _validate_agent_map(payload["map"])
        store.append_event(run_id, "map.created", payload["map"])
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
        _validate_source_backed_facts(payload["map"])
        store.append_event(run_id, "evidence.attached", payload["evidence"])
        store.append_event(run_id, "map.updated", payload["map"])
        return

    if tool_name == "draft_expression_variants":
        for draft in payload["drafts"]:
            store.append_event(run_id, "expression.draft.created", draft)
        return

    if tool_name == "revise_knowledge_map":
        map_payload = _revision_map_payload(payload)
        _validate_source_backed_facts(map_payload)
        store.append_event(run_id, "map.updated", map_payload)
        return

    raise ValueError(f"Unknown reducer tool: {tool_name}")


def _revision_map_payload(payload: dict) -> dict:
    if isinstance(payload, dict) and "map" in payload:
        return payload["map"]
    return payload


def _validate_source_backed_facts(map_payload: dict) -> None:
    if not isinstance(map_payload, dict):
        raise ValueError("map payload must be an object")

    nodes = map_payload.get("nodes", [])
    if not isinstance(nodes, list):
        raise ValueError("map nodes must be a list")

    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("map nodes must be objects")
        if node.get("confidence") == "fact":
            source_refs = node.get("source_refs")
            if not isinstance(source_refs, list) or not source_refs:
                raise ValueError("fact nodes require source_refs")


def _validate_agent_map(map_payload: dict) -> None:
    text = str(map_payload)
    if any(placeholder in text for placeholder in TEMPLATE_PLACEHOLDERS):
        raise ValueError("Agent map contains template placeholders")

    insights = map_payload.get("non_obvious_insights", [])
    if len(insights) < 3:
        raise ValueError("Agent map requires at least 3 non_obvious_insights")
    for insight in insights:
        if not insight.get("source_capture_ids"):
            raise ValueError("Agent insight requires source_capture_ids")
        if len(insight.get("claim", "")) < 12:
            raise ValueError("Agent insight claim is too shallow")

    gaps = map_payload.get("evidence_gaps", [])
    if len(gaps) < 2:
        raise ValueError("Agent map requires at least 2 evidence_gaps")
    for gap in gaps:
        if not gap.get("search_query"):
            raise ValueError("Evidence gap requires search_query")
