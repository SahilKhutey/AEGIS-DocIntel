"""Observability stack boots and exposes /metrics."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from amdi.api.app import create_app
from amdi.observability.logging import configure, get_logger
from amdi.observability.tracing import span
from amdi.observability.health import readiness


def test_logging_configure() -> None:
    configure()  # should not raise
    assert get_logger("test") is not None


def test_span_noop_safe() -> None:
    with span("noop") as s:
        assert s is None


@pytest.mark.asyncio
async def test_readyz_full(monkeypatch, tmp_path) -> None:
    import os
    os.environ["AMDI_STORAGE_BACKEND"] = "filesystem"
    os.environ["AMDI_STORAGE_ROOT"] = str(tmp_path)
    os.environ["AMDI_QUEUE_BACKEND"] = "memory"
    from amdi.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app),
                            base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            r = await c.get("/readyz")
    assert r.status_code == 200
