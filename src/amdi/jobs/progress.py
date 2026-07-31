"""In-process pub/sub for job events.

Per-job asyncio.Queue consumed by SSE endpoints. Survives worker process
boundary because events are also persisted to the ledger (TTL-bounded).
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator

from amdi.jobs.schemas import JobEvent


class ProgressBus:
    """Fan-out broker of JobEvents to multiple SSE subscribers."""

    def __init__(self, max_buffer: int = 1024, heartbeat_s: float = 15.0) -> None:
        self._subs: dict[str, list[asyncio.Queue[JobEvent]]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._max_buffer = max_buffer
        self._heartbeat_s = heartbeat_s
        self._heartbeat_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop(self) -> None:
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except (asyncio.CancelledError, Exception):
                pass

    async def publish(self, ev: JobEvent) -> None:
        async with self._lock:
            queues = list(self._subs.get(ev.job_id, ()))
        for q in queues:
            try:
                q.put_nowait(ev)
            except asyncio.QueueFull:
                # Drop oldest, keep newest. Prevents head-of-line blocking.
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    q.put_nowait(ev)
                except asyncio.QueueFull:  # pragma: no cover
                    pass

    @asynccontextmanager
    async def subscribe(self, job_id: str) -> AsyncIterator[asyncio.Queue[JobEvent]]:
        q: asyncio.Queue[JobEvent] = asyncio.Queue(maxsize=self._max_buffer)
        async with self._lock:
            self._subs[job_id].append(q)
        try:
            yield q
        finally:
            async with self._lock:
                subs = self._subs.get(job_id, [])
                if q in subs:
                    subs.remove(q)
                if not subs:
                    self._subs.pop(job_id, None)

    async def _heartbeat_loop(self) -> None:  # pragma: no cover — long running
        while True:
            await asyncio.sleep(self._heartbeat_s)
            now = time.time()
            async with self._lock:
                targets: list[tuple[str, asyncio.Queue[JobEvent]]] = []
                for jid, qs in self._subs.items():
                    for q in qs:
                        targets.append((jid, q))
            for jid, q in targets:
                try:
                    q.put_nowait(JobEvent(
                        job_id=jid, ts=now, kind="heartbeat",
                        message="keepalive",
                    ))
                except asyncio.QueueFull:
                    pass


__all__ = ["ProgressBus"]
