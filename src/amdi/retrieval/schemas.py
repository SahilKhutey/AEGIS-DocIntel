"""Canonical retrieval schema. Used by API, methods, fusion, reranker, SSE."""

from __future__ import annotations

import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class QueryExpansion(BaseModel):
    """Reformulations produced by the query preprocessor."""
    original: str
    paraphrases: list[str] = Field(default_factory=list)
    subqueries: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    time_window: tuple[str, str] | None = None


class Query(BaseModel):
    """Top-level user query, post-preprocessing."""
    raw: str
    expanded: QueryExpansion = Field(default_factory=lambda: QueryExpansion(original=""))
    top_k: int = Field(default=20, ge=1, le=200)
    token_budget: int | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = None
    session_id: str | None = None

    @field_validator("raw")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("query.raw must be non-empty")
        return v.strip()


class Citation(BaseModel):
    document_id: str
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None  # (x, y, w, h) normalized
    char_span: tuple[int, int] | None = None
    section: str | None = None
    method_votes: list[str] = Field(default_factory=list)   # which methods found this


class Evidence(BaseModel):
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    score_dense: float = 0.0
    score_bm25: float = 0.0
    score_frequency: float = 0.0
    score_geometry: float = 0.0
    score_graph: float = 0.0
    score_matrix: float = 0.0
    score_template: float = 0.0
    score_fused: float = 0.0
    score_rerank: float | None = None
    citations: list[Citation] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalConfig(BaseModel):
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "bm25": 1.0, "dense": 1.2, "frequency": 0.7,
            "geometry": 0.6, "graph": 0.9,
            "matrix": 0.7, "template": 0.4,
        }
    )
    fusion: Literal["rrf", "weighted", "calibrated"] = "rrf"
    rrf_k: int = 60
    dedup_simhash_threshold: int = 8  # max Hamming distance for dedup
    reranker_top_n: int = 50           # rerank only top-N fused
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_device: str = "cpu"
    reranker_batch_size: int = 16
    enable_reranker: bool = True
    enable_dedup: bool = True
    candidate_pool_size: int = 200      # per-method candidates before fusion


class RetrievalResult(BaseModel):
    query: Query
    evidence: list[Evidence]
    timings_ms: dict[str, float] = Field(default_factory=dict)
    counters: dict[str, int] = Field(default_factory=dict)
    generated_at: float = Field(default_factory=time.time)

    def as_tokens(self, *, budget: int) -> str:
        """Compact serialization with token budget cap."""
        from amdi.retrieval.budget import trim_to_budget
        return trim_to_budget(self.evidence, budget=budget)


__all__ = [
    "Query", "QueryExpansion", "RetrievalConfig",
    "Evidence", "Citation", "RetrievalResult",
]
