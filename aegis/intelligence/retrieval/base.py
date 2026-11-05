"""
aegis.intelligence.retrieval.base
=================================
Abstract Base Retriever defining the canonical query and indexing interface.
"""

from __future__ import annotations

import abc
import time
import uuid
from typing import Any, Dict, List, Optional

from aegis.intelligence.models import (
    RetrievalItem,
    RetrievalMode,
    RetrievalResult,
)


class BaseRetriever(abc.ABC):
    """Canonical interface for all isolated retrieval modes."""

    def __init__(self, mode: RetrievalMode):
        self.mode = mode

    @abc.abstractmethod
    def index_document(
        self,
        document_id: str,
        chunk_id: str,
        text: str,
        page_number: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> None:
        """Add a document passage/chunk to the index."""
        raise NotImplementedError

    @abc.abstractmethod
    def _execute_search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalItem]:
        """Core search implementation for the specific retrieval mode."""
        raise NotImplementedError

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        query_id: Optional[str] = None,
    ) -> RetrievalResult:
        """Execute search, measure latency, and format canonical result envelope."""
        q_id = query_id or f"Q-{uuid.uuid4().hex[:8].upper()}"
        filters_dict = filters or {}
        
        t0 = time.perf_counter()
        results = self._execute_search(query=query, top_k=top_k, filters=filters_dict)
        t1 = time.perf_counter()
        
        latency_ms = round((t1 - t0) * 1000.0, 3)
        return RetrievalResult(
            query_id=q_id,
            retrieval_mode=self.mode,
            query=query,
            filters=filters_dict,
            results=results[:top_k],
            latency_ms=latency_ms,
        )
