# 慢想

慢想是一个独立的研究工作流 Agent 原型。它从随手收藏和实时感想出发，把零散材料整理成有主线、有证据缺口、有边界的知识地图。

当前版本是确定性 Python MVP，不依赖真实 LLM 或联网搜索，方便先验证领域状态机和规则。

长期方向：慢想不会把自己做成通用数据库或大而全知识库。未来会接入本地或云端知识库作为长期记忆与检索层，Agent 本身只负责发现主题、组织材料、控制研究边界、生成知识地图和引导用户补证据。

## 目录

```text
src/manxiang/       # 慢想核心模块
tests/              # 慢想单元测试
examples/           # 可运行 demo
docs/               # PRD、架构图、TodoList 和实现计划
prototype/          # 单页五步工作台页面原型
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

如果从仓库根目录运行：

```bash
cd manxiang
uv run pytest
```
