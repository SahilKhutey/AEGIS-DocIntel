"""REST ↔ gRPC bridge: FastAPI surface continues to work unchanged."""

from __future__ import annotations

import sys
from pathlib import Path

root = str(Path(__file__).resolve().parents[2])
if root not in sys.path:
    sys.path.insert(0, root)

import pytest
from httpx import ASGITransport, AsyncClient

from amdi.api.app import create_app


@pytest.mark.asyncio
async def test_health_endpoint_via_bridge() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        async with app.router.lifespan_context(app):
            r = await c.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
