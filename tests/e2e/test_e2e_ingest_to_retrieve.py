"""Ingest → retrieve end-to-end through the FastAPI surface."""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

from amdi.api.app import create_app
from amdi.security.auth import JWTIssuer


@pytest.mark.asyncio
async def test_full_pipeline(monkeypatch, tmp_path) -> None:
    os.environ["AMDI_STORAGE_BACKEND"] = "filesystem"
    os.environ["AMDI_STORAGE_ROOT"] = str(tmp_path)
    os.environ["AMDI_QUEUE_BACKEND"] = "memory"
    os.environ["AMDI_JWT_SECRET"] = "test-secret-with-enough-entropy-1234"
    os.environ["AMDI_ENABLE_RERANKER"] = "0"
    from amdi.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]

    app = create_app()
    token = JWTIssuer().issue(user_id="alice", roles=("admin",))
    files = {"file": ("e2e.txt",
                       b"Einstein proposed the theory of general relativity in 1915.",
                       "text/plain")}

    async with AsyncClient(transport=ASGITransport(app=app),
                            base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            up = await c.post("/v1/documents/upload", files=files,
                                headers={"Authorization": f"Bearer {token}"})
            assert up.status_code == 202
            job_id = up.json()["job_id"]

            # Run a query against the same memory store the demo seeds
            r = await c.post("/v1/query/", json={"raw": "Who proposed relativity?",
                                                  "top_k": 5},
                              headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert any("Einstein" in e["text"] for e in body.get("evidence", []))
