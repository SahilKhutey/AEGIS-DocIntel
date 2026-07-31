"""POST /v1/documents/upload — fire-and-forget ingestion.

Returns HTTP 202 Accepted with a job_id, then the worker does the heavy
lifting. Clients poll /v1/jobs/{id} or subscribe to /v1/jobs/{id}/events.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from amdi.api.deps import get_queue
from amdi.config import get_settings
from amdi.jobs.ledger import make_ledger
from amdi.jobs.schemas import JobEnvelope, JobState
from amdi.services.queue import QueueClient

logger = logging.getLogger("amdi.documents")
router = APIRouter()

_ALLOWED_MIME_CACHE: tuple[str, ...] | None = None


def _allowed_mime() -> tuple[str, ...]:
    global _ALLOWED_MIME_CACHE
    if _ALLOWED_MIME_CACHE is None:
        _ALLOWED_MIME_CACHE = get_settings().allowed_mime
    return _ALLOWED_MIME_CACHE


async def _dispatch_job(envelope: JobEnvelope, file_path: Path, mime: str, queue: QueueClient | None = None) -> None:
    """Enqueue to arq. Caller is the upload route handler."""
    settings = get_settings()
    if settings.queue_backend == "arq":
        qc = queue or QueueClient()
        if qc._pool is None:
            await qc.connect()
        await qc.enqueue_ingest(
            job_id=envelope.job_id,
            document_id=envelope.document_id or "",
            user_id=envelope.user_id,
            file_path=str(file_path),
            mime_type=mime,
            max_retries=settings.job_max_retries,
        )
    else:
        # Memory backend: run inline as a fire-and-forget task.
        from amdi.jobs.tasks import run_ingest
        asyncio.create_task(run_ingest(
            {"ledger": make_ledger()},
            job_id=envelope.job_id,
            document_id=envelope.document_id or "",
            user_id=envelope.user_id,
            file_path=str(file_path),
            mime_type=mime,
        ))


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit an ingestion job",
)
async def upload(
    file: UploadFile = File(...),
    user_id: str | None = Form(default=None),
    queue: QueueClient = Depends(get_queue),
) -> dict[str, object]:
    settings = get_settings()
    if file.content_type not in _allowed_mime():
        raise HTTPException(status_code=415, detail=f"unsupported mime: {file.content_type}")

    storage = settings.storage_root / "uploads"
    storage.mkdir(parents=True, exist_ok=True)
    doc_id = str(uuid.uuid4())
    target = storage / f"{doc_id}{Path(file.filename or '').suffix}"

    size = 0
    chunk_size = 1024 * 1024
    with target.open("wb") as out:
        while chunk := await file.read(chunk_size):
            size += len(chunk)
            if size > settings.max_upload_bytes:
                out.close()
                target.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="payload too large")
            out.write(chunk)

    envelope = JobEnvelope(
        document_id=doc_id,
        user_id=user_id,
        state=JobState.PENDING,
        max_retries=settings.job_max_retries,
        metadata={
            "filename": file.filename,
            "mime": file.content_type,
            "bytes": size,
        },
    )

    ledger = make_ledger()
    await ledger.put(envelope)
    await _dispatch_job(envelope, target, file.content_type or "application/octet-stream", queue)

    return {
        "job_id": envelope.job_id,
        "document_id": envelope.document_id,
        "state": envelope.state.value,
        "links": {
            "self": f"/v1/jobs/{envelope.job_id}",
            "events": f"/v1/jobs/{envelope.job_id}/events",
        },
        "submitted_at": envelope.submitted_at,
    }
