"""Job ledger and SSE streaming endpoints.

GET  /v1/jobs/{job_id}              — current envelope + last 50 events
GET  /v1/jobs/{job_id}/events       — Server-Sent Events stream (real-time)
GET  /v1/jobs?user_id=...&limit=    — recent jobs (best-effort)
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from amdi.api.deps import get_bus, get_ledger
from amdi.jobs.ledger import JobLedger
from amdi.jobs.progress import ProgressBus
from amdi.jobs.schemas import JobEnvelope, JobState

logger = logging.getLogger("amdi.jobs")
router = APIRouter()


@router.get("/{job_id}", summary="Get a job envelope")
async def get_job(
    job_id: str,
    ledger: JobLedger = Depends(get_ledger),
) -> dict[str, object]:
    env = await ledger.get(job_id)
    if env is None:
        raise HTTPException(status_code=404, detail="job not found")
    events = await ledger.list_events(job_id, since_ts=0.0)
    return {
        "job": env.to_dict(),
        "events": [e.to_dict() for e in events[-50:]],
        "links": {
            "events": f"/v1/jobs/{job_id}/events",
            "cancel": f"/v1/jobs/{job_id}",
        },
    }



@router.get("/{job_id}/events", summary="Stream job events via SSE")
async def stream_events(
    job_id: str,
    request: Request,
    bus: ProgressBus = Depends(get_bus),
    ledger: JobLedger = Depends(get_ledger),
    since_ts: float = Query(default=0.0, ge=0.0),
) -> StreamingResponse:
    # 404 if unknown job — fail-fast for clients
    env = await ledger.get(job_id)
    if env is None:
        raise HTTPException(status_code=404, detail="job not found")

    async def event_source() -> AsyncIterator[str]:
        # 1) Replay historical events from the ledger.
        last_ts = since_ts
        for ev in await ledger.list_events(job_id, since_ts=since_ts):
            yield ev.to_sse()
            last_ts = max(last_ts, ev.ts)

        if env.is_terminal:
            # 2) Job is already done — no live stream needed.
            return

        # 3) Subscribe to live events. Stop on disconnect or terminal state.
        async with bus.subscribe(job_id) as q:
            try:
                while True:
                    if await request.is_disconnected():
                        return
                    try:
                        ev = await asyncio.wait_for(
                            q.get(),
                            timeout=float(get_settings_or(15.0)),
                        )
                    except asyncio.TimeoutError:
                        yield sse_keepalive()
                        continue

                    if ev.ts < last_ts:
                        continue  # dedupe
                    last_ts = max(last_ts, ev.ts)
                    yield ev.to_sse()

                    # If the job reached terminal state, exit after the
                    # terminal event.
                    if env.state in {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}:
                        latest = await ledger.get(job_id)
                        if latest and latest.is_terminal:
                            return
            except asyncio.CancelledError:
                return

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.delete("/{job_id}", summary="Mark a job as cancelled")
async def cancel_job(
    job_id: str,
    ledger: JobLedger = Depends(get_ledger),
) -> dict[str, object]:
    env = await ledger.get(job_id)
    if env is None:
        raise HTTPException(status_code=404, detail="job not found")
    if env.is_terminal:
        st_val = env.state.value if hasattr(env.state, "value") else str(env.state)
        raise HTTPException(status_code=409, detail=f"already {st_val}")
    env = await ledger.update(
        job_id, state=JobState.CANCELLED, finished_at=time.time(),
    )
    st_val = env.state.value if hasattr(env.state, "value") else str(env.state)
    return {"job_id": job_id, "state": st_val}



def get_settings_or(default: float) -> float:
    try:
        from amdi.config import get_settings
        return float(get_settings().sse_heartbeat_s)
    except Exception:  # noqa: BLE001
        return default


def sse_keepalive() -> str:
    return ": keepalive\n\n"


__all__ = ["router"]
