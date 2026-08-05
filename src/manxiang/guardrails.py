from manxiang.schema import AgentRun


def before_tool_call(run: AgentRun, tool_name: str, args: dict) -> dict | None:
    if tool_name == "search_evidence":
        if run.autonomy_level == "inbox_only":
            return {"block": True, "reason": "search_evidence requires user confirmation"}
        if not args.get("gap_id"):
            return {"block": True, "reason": "search_evidence requires gap_id"}
    if tool_name == "publish_tweet":
        return {"block": True, "reason": "publish_tweet is not available in V0b"}
    if tool_name == "write_style_memory":
        return {"block": True, "reason": "write_style_memory requires explicit confirmation"}
    return None
