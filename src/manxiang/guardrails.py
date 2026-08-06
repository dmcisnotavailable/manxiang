from manxiang.schema import AgentRun


def _has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _collect_nodes(value: object) -> tuple[list[dict], dict | None]:
    if not isinstance(value, list):
        return [], {"block": True, "reason": "map nodes must be a list"}

    nodes: list[dict] = []
    for node in value:
        if not isinstance(node, dict):
            return [], {"block": True, "reason": "map nodes must be objects"}
        nodes.append(node)

    return nodes, None


def _map_nodes(args: dict) -> tuple[list[dict], dict | None]:
    nodes: list[dict] = []

    if "nodes" in args:
        top_nodes, decision = _collect_nodes(args["nodes"])
        if decision is not None:
            return [], decision
        nodes.extend(top_nodes)

    knowledge_map = args.get("map")
    if isinstance(knowledge_map, dict) and "nodes" in knowledge_map:
        nested_nodes, decision = _collect_nodes(knowledge_map["nodes"])
        if decision is not None:
            return [], decision
        nodes.extend(nested_nodes)

    return nodes, None


def before_tool_call(run: AgentRun, tool_name: str, args: dict) -> dict | None:
    if tool_name == "search_evidence":
        if run.autonomy_level == "inbox_only":
            return {"block": True, "reason": "search_evidence requires user confirmation"}
        if not args.get("gap_id"):
            return {"block": True, "reason": "search_evidence requires gap_id"}

    if tool_name == "request_web_search":
        if run.autonomy_level != "web_search_allowed":
            return {"block": True, "reason": "request_web_search requires web_search_allowed"}
        if not _has_text(args.get("gap_id")):
            return {"block": True, "reason": "request_web_search requires gap_id"}
        if not _has_text(args.get("search_goal")):
            return {"block": True, "reason": "request_web_search requires search_goal"}
        if not _has_text(args.get("stop_condition")):
            return {"block": True, "reason": "request_web_search requires stop_condition"}

    if tool_name == "request_source_parse":
        if run.autonomy_level == "inbox_only":
            return {"block": True, "reason": "request_source_parse requires source_parse_allowed"}
        if not _has_text(args.get("capture_id")):
            return {"block": True, "reason": "request_source_parse requires capture_id"}

    if tool_name == "retrieve_evidence_chunks":
        if not _has_text(args.get("gap_id")):
            return {"block": True, "reason": "retrieve_evidence_chunks requires gap_id"}
        if not _has_text(args.get("query")):
            return {"block": True, "reason": "retrieve_evidence_chunks requires query"}

    if tool_name in {"revise_knowledge_map", "create_knowledge_map"}:
        nodes, decision = _map_nodes(args)
        if decision is not None:
            return decision

        for node in nodes:
            if node.get("confidence") == "fact" and not node.get("source_refs"):
                return {"block": True, "reason": "fact nodes require source_refs"}

    if tool_name == "publish_tweet":
        return {"block": True, "reason": "publish_tweet is not available in V0b"}

    if tool_name == "write_style_memory":
        return {"block": True, "reason": "write_style_memory requires explicit confirmation"}

    return None
