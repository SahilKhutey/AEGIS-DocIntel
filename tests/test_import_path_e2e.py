"""Smoke: import every public symbol from its canonical location."""

from __future__ import annotations

import importlib


PUBLIC_SYMBOLS: list[str] = [
    # Core
    "amdi.config.get_settings",
    "amdi.config.AMDISettings",
    # API
    "amdi.api.app.create_app",
    "amdi.api.deps.get_queue",
    "amdi.api.deps.get_ledger",
    "amdi.api.deps.get_bus",
    # Retrieval
    "amdi.retrieval.HybridRetriever",
    "amdi.retrieval.Query",
    "amdi.retrieval.RetrievalConfig",
    "amdi.retrieval.Evidence",
    "amdi.retrieval.Citation",
    "amdi.retrieval.deduplicate",
    "amdi.retrieval.fuse",
    # Jobs
    "amdi.jobs.ledger.make_ledger",
    "amdi.jobs.progress.ProgressBus",
    "amdi.jobs.schemas.JobEnvelope",
    "amdi.jobs.schemas.JobEvent",
    # Services
    "amdi.services.container.ServiceContainer",
    "amdi.services.queue.QueueClient",
    # BC bridge
    "amdi.legacy_bridge._resolve",
]


def test_all_public_symbols_importable() -> None:
    for path in PUBLIC_SYMBOLS:
        module_name, _, attr = path.rpartition(".")
        mod = importlib.import_module(module_name)
        assert hasattr(mod, attr), f"missing: {path}"
