"""End-to-end: POST upload -> 202 + job envelope exists in ledger."""

from __future__ import annotations

import io

import pytest
from httpx import ASGITransport, AsyncClient

from amdi.api.app import create_app
from amdi.config import get_settings


@pytest.mark.asyncio
async def test_upload_returns_202_and_job_id(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "filesystem")
    monkeypatch.setenv("AMDI_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("AMDI_QUEUE_BACKEND", "memory")
    get_settings.cache_clear()  # type: ignore[attr-defined]

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        async with app.router.lifespan_context(app):
            files = {"file": ("hello.txt", io.BytesIO(b"hi"), "text/plain")}
            r = await c.post("/v1/documents/upload", files=files)
    assert r.status_code == 202, r.text
    body = r.json()
    assert "job_id" in body
    assert body["state"] == "pending"
    assert body["links"]["events"].startswith("/v1/jobs/")
