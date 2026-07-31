"""Concurrency tests for the in-memory ledger."""

from __future__ import annotations

import asyncio

import pytest

from amdi.jobs.ledger import InMemoryJobLedger
from amdi.jobs.schemas import JobEnvelope, JobEvent, JobState


@pytest.mark.asyncio
async def test_put_and_get_roundtrip() -> None:
    L = InMemoryJobLedger()
    env = JobEnvelope(document_id="doc-1")
    await L.put(env)
    got = await L.get(env.job_id)
    assert got is not None
    assert got.document_id == "doc-1"
    assert got.state == JobState.PENDING


@pytest.mark.asyncio
async def test_concurrent_updates_are_serialized() -> None:
    L = InMemoryJobLedger()
    env = JobEnvelope(document_id="doc-1")
    await L.put(env)

    async def worker(i: int) -> None:
        for pct in range(0, 101, 10):
            await L.update(env.job_id, progress_pct=float(pct))
            await asyncio.sleep(0)

    await asyncio.gather(*(worker(i) for i in range(20)))

    got = await L.get(env.job_id)
    assert got is not None
    # Last writer wins — but no corruption and no race.
    assert got.progress_pct in {float(p) for p in range(0, 101, 10)}


@pytest.mark.asyncio
async def test_prune_removes_terminal() -> None:
    L = InMemoryJobLedger()
    e1 = JobEnvelope(state=JobState.SUCCEEDED, finished_at=0.0)
    e2 = JobEnvelope(state=JobState.RUNNING)
    await L.put(e1)
    await L.put(e2)
    import time
    now = time.time()
    # Make e1 ancient
    await L.update(e1.job_id, finished_at=now - 10_000)
    removed = await L.prune(older_than_s=5_000)
    assert removed == 1
    assert await L.get(e1.job_id) is None
    assert (await L.get(e2.job_id)) is not None
