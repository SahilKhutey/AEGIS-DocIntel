"""
AMDI-OS Hybrid Retrieval Engine
================================

Combines 7 retrieval strategies across all AMDI-OS engines:

    Semantic Search    — embedding similarity (cosine / dot)
    Matrix Search      — tabular column / row matching
    Geometry Search    — spatial proximity (k-NN)
    Graph Search       — graph traversal (PageRank, BFS)
    Template Search    — fingerprint / signature matching
    Frequency Search   — TF-IDF / BM25
    Recurrence Search  — LSH / MinHash (near-duplicate)

Each returns a ranked list; results are combined via:
    RRF (Reciprocal Rank Fusion) or weighted Borda count
"""

from __future__ import annotations

from typing import Any

from src.core.geometric_element import ElementType
from src.engines.retrieval.amdi_retriever import (
    AMDIRetriever as BaseAMDIRetriever,
    RetrievalContext,
)
from src.engines.vector_db.faiss_store import FAISSStore as FaissStore

# Import new components
from .exceptions import (
    EmptyIndexError,
    IndexDimensionError,
    InvalidQueryError,
    RankFusionError,
    RetrievalEngineError,
)
from .frequency_search import FrequencyResult, FrequencySearch
from .geometry_search import GeometryResult, GeometrySearch
from .graph_search import GraphResult, GraphSearch
from .hybrid_retrieval import HybridConfig, HybridRetriever as NewHybridRetriever
from .matrix_search import MatrixResult, MatrixSearch
# Promoter import removed as it resides in the memory engine
from .ranker import HybridRanker, HybridRanking, RankedDocument
from .recurrence_search import RecurrenceResult, RecurrenceSearch
from .retrieval_engine import RetrievalEngine, RetrievalReport
from .semantic_search import SemanticResult, SemanticSearch
from .template_search import TemplateResult, TemplateSearch


class UnpackableRetrievalContext(RetrievalContext):
    """Subclass of RetrievalContext supporting 3-tuple unpacking for workflows."""

    def __iter__(self):
        return iter((self.results, self.table_answers, self.query_type))


class LegacyWorkflowHybridRetriever(BaseAMDIRetriever):
    """Legacy multi-engine retrieval orchestrator adapted for standard workflows."""

    def __init__(
        self,
        embedder: Any,
        vector_store: Any,
        geometry: Any,
        recurrence: Any,
        frequency: Any,
        matrix: Any,
        template: Any,
        graph: Any = None,
    ):
        from src.engines.semantic.semantic_engine import SemanticEngine

        semantic_engine = SemanticEngine(embedder)

        super().__init__(
            embedder=embedder,
            geometry_engine=geometry,
            recurrence_engine=recurrence,
            frequency_engine=frequency,
            matrix_engine=matrix,
            template_engine=template,
            semantic_engine=semantic_engine,
            graph_engine=graph,
        )
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        elements: list[Any],
        top_k: int = 12,
        *args: Any,
        **kwargs: Any,
    ) -> UnpackableRetrievalContext:
        """Retrieve relevant elements and answers for a query."""
        tables = [
            e for e in elements if getattr(e, "type", None) == ElementType.TABLE
        ]
        ctx = await super().retrieve(
            query=query,
            elements=elements,
            tables=tables,
            graph=self._graph,
            top_k=top_k,
        )
        return UnpackableRetrievalContext(
            query=ctx.query,
            query_type=ctx.query_type,
            weights=ctx.weights,
            results=ctx.results,
            table_answers=ctx.table_answers,
            latency_ms=ctx.latency_ms,
        )


class HybridRetriever:
    """
    Polymorphic retriever wrapper that supports both:

    1. Legacy instantiation pattern (embedder, vector_store, geometry, etc.)
    2. New multi-index retrieval engine pattern (config: HybridConfig)
    """

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        is_legacy = False
        if len(args) > 1:
            is_legacy = True
        elif kwargs and (
            "embedder" in kwargs
            or "geometry" in kwargs
            or "vector_store" in kwargs
        ):
            is_legacy = True

        if is_legacy:
            instance = object.__new__(LegacyWorkflowHybridRetriever)
            # Python automatically calls __init__ after __new__ if they match class type,
            # but since LegacyWorkflowHybridRetriever is a different subclass, we initialize it manually.
            instance.__init__(*args, **kwargs)
            return instance
        else:
            instance = object.__new__(NewHybridRetriever)
            instance.__init__(*args, **kwargs)
            return instance


__all__ = [
    "RetrievalEngine",
    "RetrievalReport",
    "HybridRetriever",
    "HybridConfig",
    "SemanticSearch",
    "SemanticResult",
    "MatrixSearch",
    "MatrixResult",
    "GeometrySearch",
    "GeometryResult",
    "GraphSearch",
    "GraphResult",
    "TemplateSearch",
    "TemplateResult",
    "FrequencySearch",
    "FrequencyResult",
    "RecurrenceSearch",
    "RecurrenceResult",
    "HybridRanker",
    "HybridRanking",
    "RankedDocument",
    "RetrievalEngineError",
    "EmptyIndexError",
    "InvalidQueryError",
    "RankFusionError",
    "IndexDimensionError",
    "FaissStore",
    "BaseAMDIRetriever",
    "RetrievalContext",
    "UnpackableRetrievalContext",
]

__version__ = "1.0.0"
