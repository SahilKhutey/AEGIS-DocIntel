"""0.3.0 guardrail: importing via legacy_bridge always raises a FutureWarning."""

from __future__ import annotations

import importlib
import warnings

import pytest


@pytest.mark.parametrize("name,canonical", [
    ("engine_geometry", "amdi.engines.geometry"),
    ("pdf_loader",      "amdi.ingestion.pdf"),
    ("hybrid_retriever", "amdi.retrieval.hybrid"),
])
def test_warning_fires(name: str, canonical: str) -> None:
    """Verify that accessing a legacy name fires FutureWarning."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            lb = importlib.import_module("amdi.legacy_bridge")
            # Trigger __getattr__ by attribute access
            getattr(lb, name)
        except (ImportError, ModuleNotFoundError):
            # If the target module doesn't exist yet, the warning still fires
            pass
        except AttributeError:
            pass
    future_warns = [w for w in caught if issubclass(w.category, FutureWarning)]
    # We expect at least one FutureWarning mentioning 0.4.0
    assert any("0.4.0" in str(w.message) for w in future_warns), (
        f"No FutureWarning mentioning 0.4.0 was emitted for {name!r}. "
        f"Caught warnings: {[(w.category, str(w.message)) for w in caught]}"
    )
