"""Coordinated drain logic.

Refuses new ingest jobs after a deadline; waits up to N seconds for in-flight
jobs to reach a terminal state before forcing worker exit.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time

from amdi.config import get_settings
from amdi.jobs.ledger import make_ledger
from amdi.jobs.schemas import JobEnvelope, JobState

logger = logging.getLogger("amdi.jobs.shutdown")


async def wait_for_drain(deadline_s: float = 30.0, poll_s: float = 0.5) -> int:
    """Block until all RUNNING/RETRYING jobs finish or deadline passes."""
    start = time.monotonic()
    settings = get_settings()
    jobs_dir = settings.storage_root / "jobs"

    while time.monotonic() - start < deadline_s:
        if not jobs_dir.exists():
            return 0
        active = 0
        for p in jobs_dir.glob("*.json"):
            if p.name.endswith(".events.ndjson"):
                continue
            try:
                env = JobEnvelope(**json.loads(p.read_text(encoding="utf-8")))
                if env.state in {JobState.RUNNING, JobState.RETRYING, JobState.PENDING}:
                    active += 1
            except Exception:  # noqa: BLE001
                continue
        if active == 0:
            return 0
        logger.info("shutdown.draining", active=active)
        await asyncio.sleep(poll_s)
    return -1


__all__ = ["wait_for_drain"]
