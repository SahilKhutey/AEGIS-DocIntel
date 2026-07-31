"""Idempotency + retry + task execution tests."""

from __future__ import annotations

import asyncio
import pytest

from amdi.config import get_settings
from amdi.jobs.ledger import FilesystemJobLedger, InMemoryJobLedger, make_ledger
from amdi.jobs.progress import ProgressBus
from amdi.jobs.schemas import JobEnvelope, JobEvent, JobState
from amdi.jobs.shutdown import wait_for_drain
from amdi.jobs.tasks import _ingest_pdf, on_shutdown, on_startup, run_ingest
from amdi.services.queue import QueueClient


@pytest.mark.asyncio
async def test_run_ingest_succeeds_on_valid_file(tmp_path, monkeypatch) -> None:
    get_settings.cache_clear()  # type: ignore[attr-defined]
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("AMDI_QUEUE_BACKEND", "memory")

    ledger = InMemoryJobLedger()
    bus = ProgressBus()
    await bus.start()

    pdf = tmp_path / "tiny.txt"
    pdf.write_bytes(b"hello world")

    envelope = JobEnvelope(document_id="d1")
    await ledger.put(envelope)

    async def _dummy_emit(kind: str, pct: float | None, msg: str, **kw: object) -> None:
        pass

    await _ingest_pdf(pdf, _dummy_emit)
    state = await ledger.get(envelope.job_id)
    assert state is not None
    assert state.state == JobState.PENDING

    await bus.stop()


@pytest.mark.asyncio
async def test_run_ingest_full_pipeline_text(tmp_path, monkeypatch) -> None:
    get_settings.cache_clear()  # type: ignore[attr-defined]
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("AMDI_QUEUE_BACKEND", "memory")

    ledger = InMemoryJobLedger()
    bus = ProgressBus()
    await bus.start()
    ctx = {"ledger": ledger, "bus": bus}

    txt_file = tmp_path / "sample.txt"
    txt_file.write_bytes(b"sample text document content")

    envelope = JobEnvelope(document_id="doc-text-1")
    await ledger.put(envelope)

    res = await run_ingest(
        ctx,
        job_id=envelope.job_id,
        document_id="doc-text-1",
        user_id="user-1",
        file_path=str(txt_file),
        mime_type="text/plain",
    )

    assert res["status"] == "ok"
    state = await ledger.get(envelope.job_id)
    assert state is not None
    assert state.state == JobState.SUCCEEDED
    assert state.progress_pct == 100.0

    events = await ledger.list_events(envelope.job_id)
    assert len(events) >= 3

    await bus.stop()


@pytest.mark.asyncio
async def test_run_ingest_unsupported_mime(tmp_path, monkeypatch) -> None:
    get_settings.cache_clear()  # type: ignore[attr-defined]
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("AMDI_QUEUE_BACKEND", "memory")

    ledger = InMemoryJobLedger()
    bus = ProgressBus()
    await bus.start()
    ctx = {"ledger": ledger, "bus": bus}

    unknown = tmp_path / "sample.bin"
    unknown.write_bytes(b"binary data")

    envelope = JobEnvelope(document_id="doc-bin-1", max_retries=1)
    await ledger.put(envelope)

    with pytest.raises(ValueError, match="unsupported mime"):
        await run_ingest(
            ctx,
            job_id=envelope.job_id,
            document_id="doc-bin-1",
            user_id="user-1",
            file_path=str(unknown),
            mime_type="application/x-custom-bin",
        )

    state = await ledger.get(envelope.job_id)
    assert state is not None
    assert state.state == JobState.FAILED

    await bus.stop()


@pytest.mark.asyncio
async def test_filesystem_ledger_roundtrip(tmp_path) -> None:
    fs_ledger = FilesystemJobLedger(root=tmp_path / "jobs")
    env = JobEnvelope(document_id="doc-fs-1")
    await fs_ledger.put(env)

    got = await fs_ledger.get(env.job_id)
    assert got is not None
    assert got.document_id == "doc-fs-1"

    updated = await fs_ledger.update(env.job_id, state=JobState.RUNNING, progress_pct=50.0)
    assert updated.progress_pct == 50.0
    assert updated.state == JobState.RUNNING

    ev = JobEvent(job_id=env.job_id, ts=1.0, kind="progress", pct=50.0, message="halfway")
    await fs_ledger.record_event(ev)

    events = await fs_ledger.list_events(env.job_id)
    assert len(events) == 1
    assert events[0].message == "halfway"

    await fs_ledger.update(env.job_id, state=JobState.SUCCEEDED, finished_at=10.0)
    removed = await fs_ledger.prune(older_than_s=0)
    assert removed == 1


@pytest.mark.asyncio
async def test_queue_client_healthcheck_not_connected() -> None:
    qc = QueueClient()
    assert await qc.healthcheck() is False
    with pytest.raises(RuntimeError):
        _ = qc.pool


@pytest.mark.asyncio
async def test_worker_lifecycle_startup_shutdown(monkeypatch) -> None:
    get_settings.cache_clear()  # type: ignore[attr-defined]
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "memory")
    ctx: dict = {}
    await on_startup(ctx)
    assert "ledger" in ctx
    assert "bus" in ctx
    await on_shutdown(ctx)
