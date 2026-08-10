from dataclasses import dataclass
from hashlib import sha1


@dataclass(frozen=True)
class StateEvent:
    id: str
    seq: int
    run_id: str
    type: str
    payload: dict
    created_at: str


def make_event_id(run_id: str, seq: int, event_type: str) -> str:
    digest = sha1(f"{run_id}|{seq}|{event_type}".encode("utf-8")).hexdigest()[:12]
    return f"evt_{digest}"
