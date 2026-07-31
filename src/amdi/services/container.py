"""Process-wide service container.

Provides lazy access to long-lived engines (retrieval, vector store, etc.)
with deterministic startup/shutdown. Replaces scattered module-level globals.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from amdi.config import AMDISettings

if TYPE_CHECKING:
    from amdi.engines.semantic import SemanticEngine
    from amdi.engines.geometry import GeometryEngine
    from amdi.retrieval.hybrid import HybridRetriever
    from amdi.retrieval.index_store import IndexStore
    from amdi.retrieval.schemas import RetrievalConfig

logger = logging.getLogger("amdi.services")


class ServiceContainer:
    """Async-safe lazy service registry."""

    def __init__(self, settings: AMDISettings) -> None:
        self._settings = settings
        self._started = False
        self._engines: dict[str, object] = {}

    # ── Lifecycle ────────────────────────────────────────────────────────────
    async def startup(self) -> None:
        if self._started:
            return
        logger.info("container.startup backend=%s", self._settings.storage_backend)
        self._started = True

    async def shutdown(self) -> None:
        if not self._started:
            return
        logger.info("container.shutdown")
        self._engines.clear()
        self._started = False

    async def is_ready(self) -> bool:
        return self._started

    # ── Lazy engine accessors ───────────────────────────────────────────────
    def index_store(self) -> "IndexStore":
        if "index_store" not in self._engines:
            from amdi.retrieval.backends.inmemory import InMemoryIndexStore
            self._engines["index_store"] = InMemoryIndexStore()
        return self._engines["index_store"]  # type: ignore[return-value]

    def retriever(self) -> "HybridRetriever":
        if "retriever" not in self._engines:
            from amdi.retrieval.hybrid import HybridRetriever
            from amdi.retrieval.schemas import RetrievalConfig
            store = self.index_store()
            cfg = RetrievalConfig(enable_reranker=self._settings.enable_reranker)
            self._engines["retriever"] = HybridRetriever(store, config=cfg)
        return self._engines["retriever"]  # type: ignore[return-value]

    def retriever_config(self) -> "RetrievalConfig":
        from amdi.retrieval.schemas import RetrievalConfig
        return RetrievalConfig(
            enable_reranker=self._settings.enable_reranker,
        )


__all__ = ["ServiceContainer"]
