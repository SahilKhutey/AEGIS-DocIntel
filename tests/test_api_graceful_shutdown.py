"""Shutdown drains running jobs."""

from __future__ import annotations

import pytest

from amdi.jobs.shutdown import wait_for_drain


@pytest.mark.asyncio
async def test_wait_for_drain_returns_zero_when_no_active(monkeypatch, tmp_path):
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "memory")
    from amdi.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]

    rc = await wait_for_drain(deadline_s=0.2)
    assert rc == 0
