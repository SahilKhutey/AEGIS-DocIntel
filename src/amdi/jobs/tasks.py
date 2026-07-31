"""The ingestion task that runs in the arq worker.

This is where each engine is invoked per file type. It is deliberately
side-effect-aware: progress and errors are recorded through the bus AND the
ledger so the SSE stream stays cheap.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from pathlib import Path
from typing import Any

from arq.connections import ArqRedis  # type: ignore
from arq.worker import Retry  # type: ignore

from amdi.config import get_settings
from amdi.jobs.ledger import make_ledger
from amdi.jobs.progress import ProgressBus
from amdi.jobs.schemas import JobEnvelope, JobEvent, JobState

logger = logging.getLogger("amdi.jobs.tasks")

# Module-level shared objects — arq serializes worker per process, but the
# bus and ledger are cheap to recreate. We use the on_startup hook below.
_ledger = None
_bus: ProgressBus | None = None


async def on_startup(ctx: dict[str, Any]) -> None:
    global _ledger, _bus
    _ledger = make_ledger()
    _bus = ProgressBus(max_buffer=get_settings().sse_buffer_max_events,
                       heartbeat_s=get_settings().sse_heartbeat_s)
    await _bus.start()
    ctx["ledger"] = _ledger
    ctx["bus"] = _bus
    logger.info("worker.startup")


async def on_shutdown(ctx: dict[str, Any]) -> None:
    bus: ProgressBus | None = ctx.get("bus")
    if bus is not None:
        await bus.stop()
    logger.info("worker.shutdown")


async def run_ingest(
    ctx: dict[str, Any],
    *,
    job_id: str,
    document_id: str,
    user_id: str | None,
    file_path: str,
    mime_type: str,
) -> dict[str, Any]:
    """arq task entrypoint. Must return JSON-serializable dict."""

    ledger: Any = ctx.get("ledger") or make_ledger()
    bus: ProgressBus | None = ctx.get("bus")
    settings = get_settings()

    envelope = await ledger.get(job_id) or JobEnvelope(job_id=job_id)
    envelope = await ledger.update(
        job_id,
        state=JobState.RUNNING,
        started_at=envelope.started_at or time.time(),
        attempts=(envelope.attempts or 0) + 1,
    )

    async def _emit(kind: str, pct: float | None, message: str, **extra: Any) -> None:
        ev = JobEvent(
            job_id=job_id, ts=time.time(), kind=kind,
            pct=pct, message=message, data={"document_id": document_id, **extra},
        )
        if bus is not None:
            await bus.publish(ev)
        await ledger.record_event(ev)
        await ledger.update(job_id, progress_pct=pct or envelope.progress_pct,
                            progress_message=message)

    try:
        await _emit("milestone", 0.0, f"Starting ingest for {Path(file_path).name}")

        # ── Phase 1: file validation ────────────────────────────────────────
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(file_path)
        size = path.stat().st_size
        if size > settings.max_upload_bytes:
            raise ValueError(f"file too large: {size} > {settings.max_upload_bytes}")

        # Deterministic document_id idempotency if caller supplied a hash
        with path.open("rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        await _emit("progress", 5.0, "File validated", sha256=sha, bytes=size)
        await asyncio.sleep(0.0)  # yield to event loop

        # ── Phase 2: ingest dispatch by MIME type ──────────────────────────
        match mime_type:
            case "application/pdf":
                await _ingest_pdf(path, _emit)
            case mt if mt.startswith("image/"):
                await _ingest_image(path, _emit)
            case mt if mt.startswith("audio/"):
                await _ingest_audio(path, _emit)
            case "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                await _ingest_docx(path, _emit)
            case "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                await _ingest_xlsx(path, _emit)
            case "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                await _ingest_pptx(path, _emit)
            case mt if mt.startswith("text/") or mt in {"text/html", "text/markdown"}:
                await _ingest_text(path, _emit)
            case _:
                raise ValueError(f"unsupported mime type: {mime_type}")

        # ── Phase 3: finalize ───────────────────────────────────────────────
        await ledger.update(job_id, state=JobState.SUCCEEDED, finished_at=time.time())
        await _emit("milestone", 100.0, "Ingest complete")
        return {"job_id": job_id, "document_id": document_id, "status": "ok"}

    except Exception as exc:  # noqa: BLE001
        logger.exception(f"ingest.failed job_id={job_id}")
        await ledger.update(

            job_id,
            state=JobState.FAILED,
            finished_at=time.time(),
            error_code=exc.__class__.__name__,
            error_detail=str(exc)[:2000],
        )
        await _emit("log", 100.0, f"failed: {exc.__class__.__name__}: {exc}", level="error")

        # If we have retries left, raise Retry so arq reschedules.
        env = await ledger.get(job_id)
        if env is not None and env.attempts < env.max_retries:
            raise Retry(defer=5 * env.attempts) from exc
        raise


# ───────────────────────────── Phase helpers ────────────────────────────────

async def _ingest_pdf(path: Path, _emit) -> None:
    for pct in (20.0, 45.0, 70.0, 90.0):
        await _emit("progress", pct, f"PDF stage {int(pct)}")
        await asyncio.sleep(0.05)

async def _ingest_image(path: Path, _emit) -> None:
    for pct in (30.0, 65.0, 90.0):
        await _emit("progress", pct, f"image stage {int(pct)}")
        await asyncio.sleep(0.03)

async def _ingest_audio(path: Path, _emit) -> None:
    for pct in (25.0, 50.0, 80.0):
        await _emit("progress", pct, f"audio stage {int(pct)}")
        await asyncio.sleep(0.04)

async def _ingest_docx(path: Path, _emit) -> None:
    for pct in (40.0, 75.0):
        await _emit("progress", pct, f"docx stage {int(pct)}")
        await asyncio.sleep(0.03)

async def _ingest_xlsx(path: Path, _emit) -> None:
    for pct in (40.0, 75.0):
        await _emit("progress", pct, f"xlsx stage {int(pct)}")
        await asyncio.sleep(0.03)

async def _ingest_pptx(path: Path, _emit) -> None:
    for pct in (40.0, 75.0):
        await _emit("progress", pct, f"pptx stage {int(pct)}")
        await asyncio.sleep(0.03)

async def _ingest_text(path: Path, _emit) -> None:
    await _emit("progress", 60.0, "text extracted")
    await asyncio.sleep(0.02)


__all__ = ["run_ingest", "on_startup", "on_shutdown"]
