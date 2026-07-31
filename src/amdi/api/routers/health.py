"""Health endpoints — readiness probes Redis as well as app state."""

from __future__ import annotations

from fastapi import APIRouter, Request

from amdi.services.queue import QueueClient
from amdi.version import __version__

router = APIRouter()


@router.get("/healthz", summary="Liveness probe")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@router.get("/readyz", summary="Readiness probe")
async def readyz(request: Request) -> dict[str, object]:
    queue: QueueClient | None = getattr(request.app.state, "queue", None)
    ledger_ready = getattr(request.app.state, "ledger", None) is not None
    queue_ready = (
        queue is not None and await queue.healthcheck()
    ) if queue is not None else False
    overall = ledger_ready and (queue_ready or not getattr(request.app.state, "queue_ready_required", False))
    return {
        "ready": overall,
        "ledger": ledger_ready,
        "queue": queue_ready,
        "version": __version__,
    }
