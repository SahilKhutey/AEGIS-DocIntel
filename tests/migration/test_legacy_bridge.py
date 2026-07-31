"""Verify that legacy_bridge re-exports still load (and warn)."""

from __future__ import annotations

import importlib
import warnings


def test_legacy_geometry_resolves_with_warning() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        mod = importlib.import_module("amdi.legacy_bridge")
        res = getattr(mod, "engine_geometry")
    assert res is not None
    assert any(issubclass(w.category, (DeprecationWarning, FutureWarning)) for w in caught)


def test_legacy_pdf_loader_resolves() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", (DeprecationWarning, FutureWarning))
        mod = importlib.import_module("amdi.legacy_bridge")
        res = getattr(mod, "pdf_loader")
    assert res is not None


def test_legacy_unknown_raises() -> None:
    import pytest
    mod = importlib.import_module("amdi.legacy_bridge")
    with pytest.raises(AttributeError):
        _ = getattr(mod, "engine_banana")
