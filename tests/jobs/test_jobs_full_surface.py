"""Async ingestion jobs + SSE smoke."""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

from amdi.api.app import create_app
from amdi.security.auth import JWTIssuer


@pytest.mark.asyncio
async def test_upload_then_get_job(monkeypatch, tmp_path) -> None:
    os.environ["AMDI_STORAGE_BACKEND"] = "filesystem"
    os.environ["AMDI_STORAGE_ROOT"] = str(tmp_path)
    os.environ["AMDI_QUEUE_BACKEND"] = "memory"
    os.environ["AMDI_JWT_SECRET"] = "test-secret-with-enough-entropy-1234"
    from amdi.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]

    app = create_app()
    token = JWTIssuer().issue(user_id="alice", roles=("admin",))
    files = {"file": ("h.txt", b"hello", "text/plain")}

    async with AsyncClient(transport=ASGITransport(app=app),
                            base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            r = await c.post("/v1/documents/upload", files=files,
                              headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 202, r.text
        job_id = r.json()["job_id"]
        async with app.router.lifespan_context(app):
            r = await c.get(f"/v1/jobs/{job_id}",
                             headers={"Authorization": f"Bearer {token}"})
        # Job may be 'pending' or already 'succeeded' (memory backend is sync)
        assert r.status_code == 200
