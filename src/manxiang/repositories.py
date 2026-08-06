from __future__ import annotations

from typing import Protocol

from manxiang.schema import CaptureItem, SourceArtifact, SourceChunk, StateEvent


class CaptureRepository(Protocol):
    def save_capture(self, item: CaptureItem) -> None:
        raise NotImplementedError

    def list_captures(self) -> list[CaptureItem]:
        raise NotImplementedError


class SourceRepository(Protocol):
    def save_source_artifact(self, artifact: SourceArtifact) -> None:
        raise NotImplementedError

    def save_source_chunk(self, chunk: SourceChunk) -> None:
        raise NotImplementedError

    def list_source_chunks(self, artifact_id: str) -> list[SourceChunk]:
        raise NotImplementedError


class EventRepository(Protocol):
    def append_event(self, run_id: str, event_type: str, payload: dict) -> StateEvent:
        raise NotImplementedError

    def replay_events(self, run_id: str, after_seq: int = 0) -> list[StateEvent]:
        raise NotImplementedError
