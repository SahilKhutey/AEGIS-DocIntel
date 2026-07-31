"""Rate limiter returns 429 after the configured limit."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

import amdi.api.middleware.rate_limit as rl_mod
from amdi.api.app import create_app
from amdi.config import get_settings


@pytest.mark.asyncio
async def test_rate_limit_kicks_in(monkeypatch) -> None:
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("AMDI_QUEUE_BACKEND", "memory")
    monkeypatch.setenv("AMDI_RATE_LIMIT_PER_MINUTE", "3")
    get_settings.cache_clear()
    rl_mod._LIMITER = None

    app = create_app()

    @app.get("/test-rate-limit")
    async def _test():
        return {"ok": True}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            responses = [await c.get("/test-rate-limit") for _ in range(5)]
    statuses = [r.status_code for r in responses]
    assert 429 in statuses
