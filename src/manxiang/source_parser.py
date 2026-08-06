from __future__ import annotations

from collections.abc import Callable
from hashlib import sha1

from manxiang.schema import CaptureItem, SourceArtifact, SourceChunk


class SourceParser:
    def __init__(self, clock: Callable[[], str], chunk_size: int = 500, overlap: int = 80):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be >= 0 and smaller than chunk_size")
        self.clock = clock
        self.chunk_size = chunk_size
        self.overlap = overlap

    def parse_capture(self, capture: CaptureItem) -> tuple[SourceArtifact, list[SourceChunk]]:
        text = self._text_for(capture)
        artifact_id = self._artifact_id(capture.id, text)
        artifact = SourceArtifact(
            id=artifact_id,
            capture_id=capture.id,
            source_type=capture.source_type,
            uri=self._uri_for(capture),
            content_hash=sha1(text.encode("utf-8")).hexdigest(),
            parse_status="parsed" if text else "parse_failed",
            parser_name="jit_plain_text",
            parser_version="v1",
            created_at=self.clock(),
        )
        chunks = self._chunks_for(artifact_id, text)
        return artifact, chunks

    def _text_for(self, capture: CaptureItem) -> str:
        candidates = [
            capture.original_text,
            capture.raw_text,
            capture.user_summary,
            capture.ai_summary_draft,
            capture.user_note,
        ]
        for candidate in candidates:
            if candidate.strip():
                return candidate.strip()
        return ""

    def _uri_for(self, capture: CaptureItem) -> str:
        if capture.source_uri:
            return capture.source_uri
        if capture.type == "url" or capture.source.startswith(("http://", "https://")):
            return capture.source
        if capture.source_type == "text":
            return f"manual://{capture.id}"
        return capture.source

    def _chunks_for(self, artifact_id: str, text: str) -> list[SourceChunk]:
        if not text:
            return []
        chunks: list[SourceChunk] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + self.chunk_size)
            chunk_text = text[start:end]
            chunk_id = self._chunk_id(artifact_id, start, end, chunk_text)
            chunks.append(
                SourceChunk(
                    id=chunk_id,
                    artifact_id=artifact_id,
                    text=chunk_text,
                    start_offset=start,
                    end_offset=end,
                    anchor=f"text:{start}-{end}",
                    embedding_status="not_embedded",
                    created_at=self.clock(),
                )
            )
            if end == len(text):
                break
            start = end - self.overlap
        return chunks

    def _artifact_id(self, capture_id: str, text: str) -> str:
        digest = sha1(f"{capture_id}|{text}".encode("utf-8")).hexdigest()[:12]
        return f"artifact_{digest}"

    def _chunk_id(self, artifact_id: str, start: int, end: int, text: str) -> str:
        digest = sha1(f"{artifact_id}|{start}|{end}|{text}".encode("utf-8")).hexdigest()[:12]
        return f"chunk_{digest}"
