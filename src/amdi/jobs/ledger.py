"""Persistent job state.

Backing store is pluggable via the `storage_backend` setting:
- memory  : in-process dict (testing)
- filesystem: append-only NDJSON log under storage_root/jobs/
- redis   : Redis hash + TTL (preferred for production)

The ledger is the source of truth for status queries. The ProgressBus is
*transient*: it feeds the SSE stream and dies if nothing is listening.
"""

from __future__ import annotations

import abc
import asyncio
import json
import time
from pathlib import Path
from typing import Any

from amdi.config import get_settings
from amdi.jobs.schemas import JobEnvelope, JobEvent, JobState


class JobLedger(abc.ABC):
    @abc.abstractmethod
    async def put(self, env: JobEnvelope) -> None: ...
    @abc.abstractmethod
    async def get(self, job_id: str) -> JobEnvelope | None: ...
    @abc.abstractmethod
    async def update(self, job_id: str, **patch: Any) -> JobEnvelope: ...
    @abc.abstractmethod
    async def list_events(self, job_id: str, since_ts: float = 0.0) -> list[JobEvent]: ...
    @abc.abstractmethod
    async def prune(self, older_than_s: int) -> int: ...
    @abc.abstractmethod
    async def record_event(self, ev: JobEvent) -> None: ...


# ─────────────────────────────────────────────────────────────────────────────
# In-memory implementation (tests + dev)
# ─────────────────────────────────────────────────────────────────────────────
class InMemoryJobLedger(JobLedger):
    def __init__(self) -> None:
        self._jobs: dict[str, JobEnvelope] = {}
        self._events: dict[str, list[JobEvent]] = {}
        self._lock = asyncio.Lock()

    async def put(self, env: JobEnvelope) -> None:
        async with self._lock:
            self._jobs[env.job_id] = env
            self._events.setdefault(env.job_id, [])

    async def get(self, job_id: str) -> JobEnvelope | None:
        async with self._lock:
            env = self._jobs.get(job_id)
            if env is None:
                return None
            # Return a deep copy so callers cannot mutate ledger state.
            return JobEnvelope(
                **{**env.to_dict(), "metadata": dict(env.metadata)}
            )

    async def update(self, job_id: str, **patch: Any) -> JobEnvelope:
        async with self._lock:
            env = self._jobs[job_id]
            for k, v in patch.items():
                setattr(env, k, v)
            return JobEnvelope(**{**env.to_dict(), "metadata": dict(env.metadata)})

    async def list_events(self, job_id: str, since_ts: float = 0.0) -> list[JobEvent]:
        async with self._lock:
            return [e for e in self._events.get(job_id, []) if e.ts > since_ts]

    async def prune(self, older_than_s: int) -> int:
        cutoff = time.time() - older_than_s
        async with self._lock:
            victims = [jid for jid, env in self._jobs.items()
                       if env.is_terminal and (env.finished_at or 0) < cutoff]
            for jid in victims:
                self._jobs.pop(jid, None)
                self._events.pop(jid, None)
            return len(victims)

    async def record_event(self, ev: JobEvent) -> None:
        async with self._lock:
            self._events.setdefault(ev.job_id, []).append(ev)


# ─────────────────────────────────────────────────────────────────────────────
# Filesystem implementation (single-node, durable, easy to inspect)
# ─────────────────────────────────────────────────────────────────────────────
class FilesystemJobLedger(JobLedger):
    """Atomic write per job: <storage>/jobs/<job_id>.json

    Events are written to <storage>/jobs/<job_id>.events.ndjson (append-only).
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, asyncio.Lock] = {}
        self._registry_lock = asyncio.Lock()

    def _job_path(self, jid: str) -> Path:
        return self._root / f"{jid}.json"

    def _events_path(self, jid: str) -> Path:
        return self._root / f"{jid}.events.ndjson"

    async def _lock_for(self, jid: str) -> asyncio.Lock:
        async with self._registry_lock:
            lock = self._locks.get(jid)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[jid] = lock
            return lock

    async def put(self, env: JobEnvelope) -> None:
        lock = await self._lock_for(env.job_id)
        async with lock:
            self._atomic_write_json(self._job_path(env.job_id), env.to_dict())

    async def get(self, job_id: str) -> JobEnvelope | None:
        p = self._job_path(job_id)
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        return JobEnvelope(**data)

    async def update(self, job_id: str, **patch: Any) -> JobEnvelope:
        lock = await self._lock_for(job_id)
        async with lock:
            p = self._job_path(job_id)
            data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
            env = JobEnvelope(**data)
            for k, v in patch.items():
                setattr(env, k, v)
            self._atomic_write_json(p, env.to_dict())
            return env

    async def list_events(self, job_id: str, since_ts: float = 0.0) -> list[JobEvent]:
        p = self._events_path(job_id)
        if not p.exists():
            return []
        events: list[JobEvent] = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            ed = json.loads(line)
            ev = JobEvent(**ed)
            if ev.ts > since_ts:
                events.append(ev)
        return events

    async def prune(self, older_than_s: int) -> int:
        cutoff = time.time() - older_than_s
        removed = 0
        for p in self._root.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                env = JobEnvelope(**data)
                if env.is_terminal and (env.finished_at or 0) < cutoff:
                    p.unlink(missing_ok=True)
                    events_p = p.with_name(p.stem + ".events.ndjson")
                    events_p.unlink(missing_ok=True)
                    removed += 1
            except Exception:  # noqa: BLE001 — best-effort
                continue
        return removed

    async def record_event(self, ev: JobEvent) -> None:
        path = self._events_path(ev.job_id)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev.to_dict()) + "\n")


    @staticmethod
    def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        tmp.replace(path)


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────
def make_ledger() -> JobLedger:
    s = get_settings()
    if s.queue_backend == "memory" or s.storage_backend == "memory":
        return InMemoryJobLedger()
    return FilesystemJobLedger(s.storage_root / "jobs")


__all__ = [
    "JobLedger",
    "InMemoryJobLedger",
    "FilesystemJobLedger",
    "make_ledger",
]
