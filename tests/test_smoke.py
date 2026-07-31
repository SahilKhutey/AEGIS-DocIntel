"""Smoke tests — exercise public surface; no engine internals."""

from __future__ import annotations

import importlib

import pytest

from amdi import __version__
from amdi.config import AMDISettings, get_settings


def test_version_is_semver() -> None:
    raw = __version__.replace(".dev", ".").replace("dev", ".")
    parts = [p for p in raw.split(".") if p]
    assert len(parts) >= 2
    assert all(p.isdigit() for p in parts)


def test_settings_load_with_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMDI_API_PORT", "8765")
    get_settings.cache_clear()
    s = AMDISettings()
    assert s.api_port == 8765
    assert s.storage_root.exists()


@pytest.mark.parametrize("module", [
    "amdi",
    "amdi.core",
    "amdi.config",
    "amdi.version",
    "amdi.api.app",
    "amdi.services.container",
])
def test_modules_import(module: str) -> None:
    assert importlib.import_module(module) is not None


def test_app_factory_builds() -> None:
    from amdi.api.app import create_app
    app = create_app()
    # Routes registered
    paths = set()
    for r in app.routes:
        if hasattr(r, "path") and r.path:
            paths.add(r.path)
        if hasattr(r, "original_router"):
            prefix = getattr(r.include_context, "prefix", "")
            for sr in getattr(r.original_router, "routes", []):
                paths.add(f"{prefix}{sr.path}")
            if hasattr(r, "include_context") and r.include_context.prefix:
                paths.add(r.include_context.prefix)
    assert "/healthz" in paths
    assert any(p.startswith("/v1") for p in paths)
