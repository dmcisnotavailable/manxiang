from manxiang.runs import run_surprise_with_bridge
from manxiang.schema import AgentRun, CaptureItem
from manxiang.storage import JsonStore
from manxiang.workbench import WorkbenchService


RICH_MAP = {
    "id": "map_agent_real_analysis",
    "version": 1,
    "title": "从王室亲缘误读到西班牙王权叙事",
    "core_question": "这些收藏真正串起来的不是“谁和谁有血缘”，而是王室如何通过婚姻、命名、艺术赞助和航海扩张制造合法性。",
    "thesis": "用户的直觉有价值，但第一层问题要从八卦式血缘关系升级为“王权叙事如何被看见、被翻译、被误读”。",
    "mainline": [
        "先拆开名字：伊莎贝拉/伊丽莎白、费利佩/菲利普分别属于不同语言和王朝语境，不能因为音译相近就判定亲缘。",
        "再看西班牙王室的权力展示：普拉多画作不是背景装饰，而是王室把婚姻、继承和宗教合法性视觉化的入口。",
        "最后接到哥伦布：伊莎贝拉与航海扩张让王室叙事从欧洲亲缘网络延伸到帝国开端。",
    ],
    "non_obvious_insights": [
        {
            "claim": "“欧洲真人人有亲缘”这个感想应被当成研究假设，而不是结论。",
            "why_interesting": "它能引出哈布斯堡、波旁等王朝联姻结构，但也容易把译名相似误读成血缘。",
            "source_capture_ids": ["cap_1", "cap_3", "cap_5"],
        },
        {
            "claim": "普拉多是理解王室故事的证据入口，不只是艺术兴趣点。",
            "why_interesting": "画作能把人物关系、权力合法性和王室自我叙事连起来。",
            "source_capture_ids": ["cap_2"],
        },
        {
            "claim": "伊莎贝拉和哥伦布这条线让主题从家族谱系转向国家扩张。",
            "why_interesting": "它解释了为什么一个女王名字能连接亲缘、宗教、航海和殖民史。",
            "source_capture_ids": ["cap_6"],
        },
    ],
    "known_unknowns": [
        "伊莎贝拉一世与伊丽莎白一世是否存在可说明的血缘路径，需要谱系证据。",
        "普拉多中哪些具体画作最适合作为西班牙王室叙事样本，需要作品清单。",
    ],
    "evidence_gaps": [
        {
            "id": "gap_genealogy",
            "description": "确认伊莎贝拉和伊丽莎白的谱系关系，而不是凭名字相似推断。",
            "search_query": "Isabella I of Castile Elizabeth I genealogy relationship",
            "source_capture_ids": ["cap_1"],
        },
        {
            "id": "gap_prado_paintings",
            "description": "找出普拉多馆藏中能代表西班牙王室叙事的具体画作。",
            "search_query": "Prado Museum Spanish royal family paintings Habsburg Bourbon",
            "source_capture_ids": ["cap_2", "cap_5"],
        },
    ],
}


def test_agent_map_from_bridge_rejects_template_placeholders(tmp_path):
    store = JsonStore(tmp_path)
    run = AgentRun(
        id="run_1",
        input_capture_ids=["cap_1", "cap_2", "cap_3"],
        created_at="2026-08-06T10:00:00+08:00",
        updated_at="2026-08-06T10:00:00+08:00",
    )
    captures = [
        CaptureItem(
            id="cap_1",
            type="text",
            source="manual",
            user_note="",
            captured_at="2026-08-06T10:00:00+08:00",
            original_text="伊莎贝拉和伊丽莎白两个著名的女王有血缘关系。",
        )
    ]

    class FakeBridge:
        def run(self, _run, _captures):
            return {
                "model_name": "fake-realistic-model",
                "tool_calls": ["create_knowledge_map"],
                "events": [
                    {"type": "tool.started", "tool_name": "create_knowledge_map", "payload": {"version": 1}},
                    {"type": "tool.completed", "tool_name": "create_knowledge_map", "payload": {"map": RICH_MAP}},
                ],
            }

    run_surprise_with_bridge(store, run, captures, bridge=FakeBridge())

    created = [event.payload for event in store.replay_events("run_1") if event.type == "map.created"]
    assert created
    text = str(created[-1])
    assert "我已知道什么" not in text
    assert "核心问题还不清楚" not in text
    assert "从王室亲缘误读到西班牙王权叙事" in text
    assert len(created[-1]["non_obvious_insights"]) >= 3
    assert all(item["source_capture_ids"] for item in created[-1]["non_obvious_insights"])
    assert all(gap["search_query"] for gap in created[-1]["evidence_gaps"])


def test_workbench_state_uses_agent_map_after_surprise_run(tmp_path):
    service = WorkbenchService(storage_root=tmp_path, clock=lambda: "2026-08-06T10:00:00+08:00")
    service.seed_demo()

    class FakeBridge:
        def run(self, _run, _captures):
            return {
                "model_name": "fake-realistic-model",
                "tool_calls": ["create_knowledge_map"],
                "events": [
                    {"type": "tool.started", "tool_name": "create_knowledge_map", "payload": {"version": 1}},
                    {"type": "tool.completed", "tool_name": "create_knowledge_map", "payload": {"map": RICH_MAP}},
                ],
            }

    state = service.create_surprise_run(run_bridge=True, bridge=FakeBridge())

    assert state["agentMap"]["title"] == "从王室亲缘误读到西班牙王权叙事"
    assert state["map"]["title"] == "从王室亲缘误读到西班牙王权叙事"
    assert len(state["agentMap"]["non_obvious_insights"]) == 3
    assert "我已知道什么" not in str(state["map"])
