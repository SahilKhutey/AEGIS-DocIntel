"""Verifies every REST endpoint mentioned in the README actually exists
in the FastAPI app surface and behaves with sane status codes.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from amdi.api.app import create_app


ENDPOINTS = [
    ("POST", "/v1/documents/upload",                       422),  # missing file
    ("GET",  "/v1/jobs/test-job-id",                       404),  # job not found
    ("GET",  "/healthz",                                   200),
    ("GET",  "/readyz",                                    200),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path,expected", ENDPOINTS)
async def test_endpoint_exists(method: str, path: str, expected: int,
                                monkeypatch, tmp_path) -> None:
    import os
    os.environ["AMDI_STORAGE_BACKEND"] = "memory"
    os.environ["AMDI_QUEUE_BACKEND"] = "memory"
    os.environ["AMDI_JWT_SECRET"] = "test-secret-with-enough-entropy-1234"
    from amdi.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app),
                            base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            r = await c.request(method, path)
    assert r.status_code == expected, (method, path, r.text[:120])
