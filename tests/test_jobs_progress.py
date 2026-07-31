"""Progress bus fan-out + heartbeat."""

from __future__ import annotations

import asyncio
import time

import pytest

from amdi.jobs.progress import ProgressBus
from amdi.jobs.schemas import JobEvent


@pytest.mark.asyncio
async def test_two_subscribers_each_receive_event() -> None:
    bus = ProgressBus(max_buffer=16, heartbeat_s=10.0)
    await bus.start()
    try:
        async with bus.subscribe("job-A") as qa, bus.subscribe("job-A") as qb:
            await bus.publish(JobEvent(job_id="job-A", ts=time.time(),
                                       kind="progress", pct=42.0, message="ok"))
            ev_a = await asyncio.wait_for(qa.get(), timeout=1.0)
            ev_b = await asyncio.wait_for(qb.get(), timeout=1.0)
            assert ev_a.pct == 42.0 and ev_b.pct == 42.0
    finally:
        await bus.stop()


@pytest.mark.asyncio
async def test_full_queue_drops_oldest_then_accepts_newest() -> None:
    bus = ProgressBus(max_buffer=2, heartbeat_s=10.0)
    await bus.start()
    try:
        async with bus.subscribe("job-B") as q:
            for i in range(5):
                await bus.publish(JobEvent(
                    job_id="job-B", ts=time.time(),
                    kind="progress", pct=float(i), message=f"m{i}",
                ))
            # Queue keeps newest 2
            ev1 = await asyncio.wait_for(q.get(), timeout=1.0)
            ev2 = await asyncio.wait_for(q.get(), timeout=1.0)
            assert ev1.message == "m3"
            assert ev2.message == "m4"
    finally:
        await bus.stop()
