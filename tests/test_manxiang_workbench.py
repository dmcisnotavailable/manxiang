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

    assert len(seeded["captures"]) == 6
    assert mapped["task"]["title"] in {"西班牙王室", "欧洲王室亲缘", "伊莎贝拉女王"}
    assert mapped["linePlan"]["recommendedLine"] in {"因果线", "问题线", "人物/利益线"}
    assert mapped["map"]["gaps"]
    assert "证据缺口" in drafted["draft"]


def test_workbench_reset_clears_persisted_state(tmp_path):
    service = WorkbenchService(storage_root=tmp_path)
    service.seed_demo()

    state = service.reset()

    assert state["captures"] == []
    assert state["topics"] == []
    assert state["task"] is None
