# 慢想

慢想是一个独立的研究工作流 Agent 原型。它从随手收藏和实时感想出发，把零散材料整理成有主线、有证据缺口、有边界的知识地图。

当前 V0b 目标是在保留 Python 慢想核心的基础上，接入 Pi Agent Core 和真实 LLM，跑通真实输入、护栏、补证据和事件 replay 闭环。

长期方向：慢想不会把自己做成通用数据库或大而全知识库。未来会接入本地或云端知识库作为长期记忆与检索层，Agent 本身只负责发现主题、组织材料、控制研究边界、生成知识地图和引导用户补证据。

## 目录

```text
src/manxiang/       # 慢想核心模块
tests/              # 慢想单元测试
examples/           # 可运行 demo
docs/               # PRD、架构图、TodoList 和实现计划
prototype/          # 单页五步工作台页面原型
piagent/            # Pi Agent Core + 真实 LLM 的 Node/TypeScript 桥
```

## 页面原型

第一版交互原型已经接到本地 `ManxiangPipeline`。先启动工作台服务：

```bash
PYTHONPATH=src uv run python -m manxiang.web
```

然后打开：

```text
http://127.0.0.1:8765
```

## 运行 Demo

```bash
uv run python examples/07_manxiang_mvp.py
```

## 运行测试

```bash
uv run pytest
```

真实 LLM 验收测试不会跳过环境变量，缺少配置时会失败：

```bash
uv run pytest tests/test_v0b_piagent_real_llm.py
```

TypeScript 桥类型检查：

```bash
npm run piagent:typecheck
```

如果从仓库根目录运行：

```bash
cd manxiang
uv run pytest
```

## V1 Agent Upgrade

V1 turns the V0b demo into an evidence-driven research Agent.

Core additions:

- SourceArtifact / SourceChunk / SourceRef for traceable evidence.
- SQLiteStore for v1 repository experiments while JsonStore remains the V0b demo store.
- Just-in-time source parsing, so captures stay lightweight until a research run needs evidence.
- Keyword retrieval over SourceChunk as the first local RAG baseline.
- KnowledgeMap versioning and diff.
- Guardrails and reducers that reject fact nodes without source_refs.
- Eval runner for rubric-based Agent quality checks.

Run local deterministic tests:

```bash
uv run pytest -k 'not piagent_real_llm'
```

Run TypeScript bridge typecheck:

```bash
npm run piagent:typecheck
```

Run v1 eval sample:

```bash
uv run python evals/manxiang/run_eval.py
```

Run real LLM validation only when provider and model are configured:

```bash
MANXIANG_LLM_PROVIDER=your_provider MANXIANG_LLM_MODEL=your_model uv run pytest tests/test_v0b_piagent_real_llm.py
```
