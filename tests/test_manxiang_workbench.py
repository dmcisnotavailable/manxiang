from manxiang.workbench import WorkbenchService


def test_workbench_capture_and_discover_topics_use_pipeline(tmp_path):
    service = WorkbenchService(storage_root=tmp_path)

    for index in range(5):
        service.capture(type="text", source=f"note {index}", user_note=f"为什么 AI 陪伴让人觉得真实？第 {index} 条")

    state = service.discover_topics()

    assert len(state["captures"]) == 5
    assert state["topics"][0]["status"] == "ready"
    assert state["topics"][0]["name"] == "AI 陪伴与亲密关系"


def test_workbench_creates_map_and_draft_from_pipeline(tmp_path):
    service = WorkbenchService(storage_root=tmp_path)
    seeded = service.seed_demo()
    topic_id = seeded["topics"][0]["id"]

    mapped = service.create_knowledge_map(topic_id=topic_id)
    drafted = service.create_draft("note")

    assert mapped["task"]["title"] == "AI 陪伴为什么让人觉得像真的"
    assert mapped["linePlan"]["recommendedLine"] == "因果线"
    assert mapped["map"]["gaps"] == ["长期使用动机", "真实用户反馈"]
    assert "长期使用动机" in drafted["draft"]


def test_workbench_reset_clears_persisted_state(tmp_path):
    service = WorkbenchService(storage_root=tmp_path)
    service.seed_demo()

    state = service.reset()

    assert state["captures"] == []
    assert state["topics"] == []
    assert state["task"] is None
