"""/metrics endpoint exposes Prometheus text format."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from amdi.api.app import create_app


@pytest.mark.asyncio
async def test_metrics_exposed() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            r = await c.get("/metrics")
    assert r.status_code == 200
    assert "amdi_http_requests_total" in r.text or "amdi_" in r.text
