"""Bearer-required endpoint behavior."""

from __future__ import annotations

import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient

from amdi.api.app import create_app
from amdi.api.middleware.auth import require_jwt
from amdi.config import get_settings
from amdi.security.auth import JWTIssuer


@pytest.fixture
def token(monkeypatch) -> str:
    monkeypatch.setenv("AMDI_JWT_SECRET", "test-secret-with-enough-entropy-1234")
    get_settings.cache_clear()
    return JWTIssuer().issue(user_id="alice", roles=("admin",))


@pytest.mark.asyncio
async def test_missing_token_401(monkeypatch) -> None:
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("AMDI_QUEUE_BACKEND", "memory")
    get_settings.cache_clear()
    app = create_app()

    @app.get("/test-protected", dependencies=[Depends(require_jwt)])
    async def _protected():
        return {"status": "ok"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            r = await c.get("/test-protected")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_valid_token_200(monkeypatch, token) -> None:
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("AMDI_QUEUE_BACKEND", "memory")
    get_settings.cache_clear()
    app = create_app()

    @app.get("/test-protected", dependencies=[Depends(require_jwt)])
    async def _protected():
        return {"status": "ok"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            r = await c.get("/test-protected", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint_public(monkeypatch) -> None:
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("AMDI_QUEUE_BACKEND", "memory")
    get_settings.cache_clear()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            r = await c.get("/healthz")
    assert r.status_code == 200
