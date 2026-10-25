"""
Retrieval Dashboard
====================

Interface for hybrid retrieval queries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RetrievalQueryRequest:
    """User's retrieval query."""

    query_text: str
    semantic_embedding: Optional[List[float]] = None
    graph_seed: Optional[List[str]] = None
    geometry_query: Optional[List[float]] = None
    template_fingerprint: Optional[List[int]] = None
    frequency_tokens: Optional[List[str]] = None
    recurrence_items: Optional[List[int]] = None
    target_levels: Optional[List[int]] = None
    top_k: int = 10
    weights: Optional[Dict[str, float]] = None

    def to_dict(self) -> dict:
        return {
            "query_text": self.query_text,
            "semantic_embedding": self.semantic_embedding,
            "graph_seed": self.graph_seed,
            "geometry_query": self.geometry_query,
            "template_fingerprint": self.template_fingerprint,
            "frequency_tokens": self.frequency_tokens,
            "recurrence_items": self.recurrence_items,
            "target_levels": self.target_levels,
            "top_k": self.top_k,
            "weights": self.weights,
        }


@dataclass
class RetrievalHit:
    """A single retrieval hit."""

    doc_id: str
    fused_score: float
    methods_found: List[str] = field(default_factory=list)
    per_method_score: Dict[str, float] = field(default_factory=dict)
    snippet: str = ""

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "fused_score": round(self.fused_score, 4),
            "methods_found": self.methods_found,
            "per_method_score": {k: round(v, 4) for k, v in self.per_method_score.items()},
            "snippet": self.snippet[:300],
        }


@dataclass
class RetrievalViewData:
    """Data for retrieval dashboard."""

    query: RetrievalQueryRequest
    hits: List[RetrievalHit] = field(default_factory=list)
    per_method_counts: Dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    total_candidates: int = 0

    def to_dict(self) -> dict:
        return {
            "query": self.query.to_dict(),
            "hits": [h.to_dict() for h in self.hits],
            "per_method_counts": self.per_method_counts,
            "latency_ms": round(self.latency_ms, 2),
            "total_candidates": self.total_candidates,
        }


class RetrievalDashboard:
    """Retrieval dashboard backend API."""

    def __init__(self, retrieval_engine: Any) -> None:
        self.engine = retrieval_engine

    def execute(self, request: RetrievalQueryRequest) -> RetrievalViewData:
        """Execute a hybrid retrieval query."""
        import time
        query: Dict[str, Any] = {"query_text": request.query_text}
        if request.semantic_embedding is not None:
            import numpy as np
            query["semantic_embedding"] = np.array(request.semantic_embedding)
        if request.graph_seed is not None:
            query["graph_seed"] = request.graph_seed
        if request.geometry_query is not None:
            import numpy as np
            query["geometry_query"] = np.array(request.geometry_query)
        if request.template_fingerprint is not None:
            query["template_fingerprint"] = request.template_fingerprint
        if request.frequency_tokens is not None:
            query["frequency_tokens"] = request.frequency_tokens
        if request.recurrence_items is not None:
            query["recurrence_items"] = set(request.recurrence_items)

        t0 = time.time()
        report = self.engine.retrieve(
            query,
            top_k=request.top_k,
            weights=request.weights,
        )
        latency = (time.time() - t0) * 1000

        hits: List[RetrievalHit] = []
        for rd in report.ranking.ranked_docs:
            hits.append(
                RetrievalHit(
                    doc_id=str(rd.doc_id),
                    fused_score=rd.fused_score,
                    methods_found=rd.methods_found,
                    per_method_score=rd.per_method_score,
                )
            )
        return RetrievalViewData(
            query=request,
            hits=hits,
            per_method_counts=report.per_method_counts,
            latency_ms=latency,
            total_candidates=report.ranking.num_docs,
        )

    def get_recent_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recent retrieval queries (placeholder)."""
        return []
