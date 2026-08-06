from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from manxiang.workbench import WorkbenchService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORAGE = PROJECT_ROOT / ".manxiang-workbench"
PROTOTYPE_ROOT = PROJECT_ROOT / "prototype"


def run(host: str = "127.0.0.1", port: int = 8765, storage_root: Path = DEFAULT_STORAGE) -> None:
    service = WorkbenchService(storage_root=storage_root)

    class Handler(WorkbenchHandler):
        workbench = service

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"慢想工作台：http://{host}:{port}")
    print("按 Ctrl+C 停止。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止慢想工作台。")
    finally:
        server.server_close()


class WorkbenchHandler(BaseHTTPRequestHandler):
    workbench: WorkbenchService

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_common_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path in {"/", "/workbench", "/prototype/workbench.html"}:
            self._serve_file(PROTOTYPE_ROOT / "workbench.html", "text/html; charset=utf-8")
            return
        if path == "/api/state":
            self._send_json(self.workbench.state())
            return
        if path.startswith("/v1/runs/") and path.endswith("/events"):
            run_id = path.removeprefix("/v1/runs/").removesuffix("/events").strip("/")
            after_seq = int(parse_qs(parsed.query).get("after_seq", ["0"])[0])
            self._send_sse_events(run_id=run_id, after_seq=after_seq)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/reset":
                result = self.workbench.reset()
            elif path == "/api/seed":
                result = self.workbench.seed_demo()
            elif path == "/api/captures":
                result = self.workbench.capture(
                    type=payload.get("type", "text"),
                    source=payload.get("source", "工作台输入"),
                    user_note=payload.get("user_note", ""),
                    raw_text=payload.get("raw_text", ""),
                )
            elif path == "/v1/captures":
                result = self.workbench.capture(
                    type=payload.get("type", "text"),
                    source=payload.get("source", payload.get("source_uri", "工作台输入")),
                    user_note=payload.get("user_note", ""),
                    raw_text=payload.get("raw_text", payload.get("original_text", "")),
                )
            elif path == "/v1/surprise-runs":
                result = self.workbench.create_surprise_run(run_bridge=bool(payload.get("run_bridge", False)))
            elif path.startswith("/v1/runs/") and path.endswith("/confirmations"):
                run_id = path.removeprefix("/v1/runs/").removesuffix("/confirmations").strip("/")
                result = self.workbench.confirm_run_search(
                    run_id=run_id,
                    gap_id=payload.get("gap_id", ""),
                    max_search_queries=int(payload.get("max_search_queries", 3)),
                )
            elif path == "/api/topics":
                result = self.workbench.discover_topics()
            elif path == "/api/select-topic":
                result = self.workbench.select_topic(payload.get("topic_id", ""))
            elif path == "/api/knowledge-map":
                result = self.workbench.create_knowledge_map(
                    topic_id=payload.get("topic_id"),
                    mode=payload.get("mode", "gentle_editor"),
                )
            elif path == "/api/draft":
                result = self.workbench.create_draft(payload.get("type", "outline"))
            elif path == "/api/parking":
                result = self.workbench.park_branch(payload.get("title", "新出现的偏题分支"))
            elif path == "/api/evidence-hint":
                result = self.workbench.patch_evidence_hint()
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            self._send_json(result)
        except ValueError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_common_headers("application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_sse_events(self, run_id: str, after_seq: int) -> None:
        events = self.workbench.pipeline.store.replay_events(run_id, after_seq=after_seq)
        body = "".join(
            f"id: {event.seq}\nevent: {event.type}\ndata: {json.dumps(_to_jsonable(event), ensure_ascii=False)}\n\n"
            for event in events
        ).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self._send_common_headers("text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self._send_common_headers(content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_common_headers(self, content_type: str | None = None) -> None:
        if content_type:
            self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _to_jsonable(getattr(value, key)) for key in value.__dataclass_fields__}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the 慢想 local workbench.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE)
    args = parser.parse_args()
    run(host=args.host, port=args.port, storage_root=args.storage_root)


if __name__ == "__main__":
    main()
