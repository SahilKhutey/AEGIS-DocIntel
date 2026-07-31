"""Canonical job schema. Used by HTTP layer, worker, ledger, and SSE bus."""

from __future__ import annotations

import enum
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


class JobState(str, enum.Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    SUCCEEDED = "succeeded"
    FAILED    = "failed"
    CANCELLED = "cancelled"
    RETRYING  = "retrying"


@dataclass
class JobEnvelope:
    """All state needed for one ingestion job, end-to-end."""

    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: JobState = JobState.PENDING
    submitted_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    attempts: int = 0
    max_retries: int = 3
    document_id: str | None = None
    user_id: str | None = None
    progress_pct: float = 0.0
    progress_message: str = ""
    error_code: str | None = None
    error_detail: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.state, str) and not isinstance(self.state, JobState):
            try:
                self.state = JobState(self.state)
            except ValueError:
                pass

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value if hasattr(self.state, "value") else str(self.state)
        return d

    @property
    def is_terminal(self) -> bool:
        return self.state in {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}

    @property
    def duration_s(self) -> float | None:
        if self.started_at and self.finished_at:
            return self.finished_at - self.started_at
        return None


@dataclass(slots=True)
class JobEvent:
    """A single progress event published on the SSE bus."""

    job_id: str
    ts: float
    kind: str            # "progress" | "log" | "warning" | "milestone" | "heartbeat"
    pct: float | None = None
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "ts": self.ts,
            "kind": self.kind,
            "pct": self.pct,
            "message": self.message,
            "data": self.data,
        }

    def to_sse(self) -> str:
        lines = [f"event: {self.kind}"]
        payload = self.to_dict()
        lines.append(f"data: {json.dumps(payload, separators=(',', ':'))}")
        return "\n".join(lines) + "\n\n"



__all__ = ["JobEnvelope", "JobEvent", "JobState"]
