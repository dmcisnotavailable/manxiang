from __future__ import annotations

from typing import Any

from manxiang.schema import KnowledgeMap, TextView, TreeNode


class KnowledgeMapVersioner:
    def next_version(
        self,
        previous: KnowledgeMap,
        tree: TreeNode,
        input_capture_ids: list[str],
        input_chunk_ids: list[str],
        evidence_ids: list[str],
        text_view: TextView | None = None,
    ) -> KnowledgeMap:
        return KnowledgeMap(
            task_id=previous.task_id,
            version=previous.version + 1,
            text_view=text_view or previous.text_view,
            tree=tree,
            input_capture_ids=input_capture_ids,
            input_chunk_ids=input_chunk_ids,
            evidence_ids=evidence_ids,
        )

    def diff(self, before: KnowledgeMap, after: KnowledgeMap) -> dict[str, Any]:
        before_nodes = self._flatten(before.tree)
        after_nodes = self._flatten(after.tree)
        added_ids = sorted(set(after_nodes) - set(before_nodes))
        removed_ids = sorted(set(before_nodes) - set(after_nodes))
        changed = []
        for node_id in sorted(set(before_nodes) & set(after_nodes)):
            old = before_nodes[node_id]
            new = after_nodes[node_id]
            if self._node_changed(old, new):
                changed.append(
                    {
                        "id": node_id,
                        "before_label": old.label,
                        "after_label": new.label,
                        "before_confidence": old.confidence,
                        "after_confidence": new.confidence,
                        "before_source_ref_count": len(old.source_refs),
                        "after_source_ref_count": len(new.source_refs),
                    }
                )
        return {
            "from_version": before.version,
            "to_version": after.version,
            "added_nodes": added_ids,
            "removed_nodes": removed_ids,
            "changed_nodes": changed,
        }

    def _flatten(self, root: TreeNode) -> dict[str, TreeNode]:
        nodes = {root.id: root}
        for child in root.children:
            nodes.update(self._flatten(child))
        return nodes

    def _node_changed(self, before: TreeNode, after: TreeNode) -> bool:
        return (
            before.label != after.label
            or before.confidence != after.confidence
            or before.source_refs != after.source_refs
        )
