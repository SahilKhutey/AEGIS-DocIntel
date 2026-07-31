"""SSE streaming: replay of historical events + backpressure + job status endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from amdi.api.app import create_app
from amdi.config import get_settings
from amdi.jobs.ledger import InMemoryJobLedger
from amdi.jobs.progress import ProgressBus
from amdi.jobs.schemas import JobEnvelope, JobEvent, JobState


@pytest.mark.asyncio
async def test_sse_replays_history_then_closes_for_terminal_job(monkeypatch, tmp_path):
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("AMDI_QUEUE_BACKEND", "memory")
    get_settings.cache_clear()  # type: ignore[attr-defined]

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        async with app.router.lifespan_context(app):
            ledger: InMemoryJobLedger = app.state.ledger  # type: ignore[assignment]
            bus: ProgressBus = app.state.bus  # type: ignore[assignment]

            env = JobEnvelope(job_id="job-x", state=JobState.SUCCEEDED, finished_at=1.0)
            await ledger.put(env)
            for ts in (0.1, 0.2, 0.3):
                await ledger.record_event(JobEvent(
                    job_id="job-x", ts=ts, kind="progress",
                    pct=ts * 100, message=f"step-{ts}",
                ))

            r = await c.get("/v1/jobs/job-x/events")
            assert r.status_code == 200
            body = r.text
            assert "step-0.1" in body
            assert "step-0.2" in body
            assert "step-0.3" in body


@pytest.mark.asyncio
async def test_get_job_and_cancel_endpoints(monkeypatch, tmp_path):
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("AMDI_QUEUE_BACKEND", "memory")
    get_settings.cache_clear()  # type: ignore[attr-defined]

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        async with app.router.lifespan_context(app):
            ledger: InMemoryJobLedger = app.state.ledger  # type: ignore[assignment]

            # 404 test
            r404 = await c.get("/v1/jobs/nonexistent-id")
            assert r404.status_code == 404

            # Valid job GET test
            env = JobEnvelope(job_id="job-y", state=JobState.RUNNING)
            await ledger.put(env)

            r_get = await c.get("/v1/jobs/job-y")
            assert r_get.status_code == 200
            assert r_get.json()["job"]["state"] == "running"

            # Cancel running job
            r_del = await c.delete("/v1/jobs/job-y")
            assert r_del.status_code == 200
            assert r_del.json()["state"] == "cancelled"

            # Cancel already terminal job returns 409
            r_del_again = await c.delete("/v1/jobs/job-y")
            assert r_del_again.status_code == 409
