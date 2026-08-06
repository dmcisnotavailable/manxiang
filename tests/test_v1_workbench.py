from manxiang.workbench import WorkbenchService


def test_workbench_v1_state_exposes_versions_and_events(tmp_path):
    service = WorkbenchService(storage_root=tmp_path, clock=lambda: "2026-08-06T10:00:00+08:00")
    service.seed_demo()
    state = service.v1_state()

    assert "mapVersions" in state
    assert "recentEvents" in state
    assert "sourceChunks" in state


def test_workbench_can_prepare_v1_source_chunks(tmp_path):
    service = WorkbenchService(storage_root=tmp_path, clock=lambda: "2026-08-06T10:00:00+08:00")
    service.seed_demo()
    capture_id = service.state()["captures"][0]["id"]

    result = service.parse_capture_for_v1(capture_id)

    assert result["artifact"]["capture_id"] == capture_id
    assert result["chunks"]
