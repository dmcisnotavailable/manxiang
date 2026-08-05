from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from manxiang.schema import AgentRun, CaptureItem


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class PiAgentBridge:
    def __init__(self, runner: Callable[[dict], dict] | None = None):
        self.runner = runner or self._run_subprocess

    def run(self, run: AgentRun, captures: list[CaptureItem]) -> dict[str, Any]:
        payload = {
            "run_id": run.id,
            "autonomy_level": run.autonomy_level,
            "captures": [self._capture_payload(capture) for capture in captures],
        }
        return self.runner(payload)

    def _run_subprocess(self, payload: dict) -> dict:
        completed = subprocess.run(
            ["npm", "run", "piagent:run", "--silent"],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
            check=True,
        )
        return json.loads(completed.stdout)

    def _capture_payload(self, capture: CaptureItem) -> dict:
        return {
            "id": capture.id,
            "source_type": capture.source_type,
            "source_uri": capture.source_uri,
            "original_text": capture.original_text or capture.raw_text,
            "user_note": capture.user_note,
            "ai_summary_draft": capture.ai_summary_draft,
            "summary_status": capture.summary_status,
            "parse_status": capture.parse_status,
            "candidate_topics": capture.candidate_topics,
        }
