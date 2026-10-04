"""
Retrieval Engine
================

Main orchestrator for the Hybrid Retrieval Engine, wrapping HybridRetriever
and adding report generation and metadata snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import numpy as np

from .hybrid_retrieval import HybridConfig, HybridRetriever
from .ranker import HybridRanking


@dataclass
class RetrievalReport:
    """
    Comprehensive report of a hybrid retrieval execution.
    """

    ranking: HybridRanking
    latency_ms: float
    num_sources: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ranking": self.ranking.to_dict(),
            "latency_ms": round(self.latency_ms, 2),
            "num_sources": self.num_sources,
            "metadata": self.metadata,
        }


class RetrievalEngine:
    """
    Orchestrates indexing and multi-strategy retrieval operations.
    """

    def __init__(self, config: Optional[HybridConfig] = None) -> None:
        self.retriever = HybridRetriever(config=config)

    def add_semantic(
        self,
        doc_id: Any,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.retriever.add_semantic(doc_id, embedding, metadata=metadata)

    def add_matrix(
        self,
        table_id: Any,
        matrix: np.ndarray,
        row_metadata: Optional[Dict[int, Dict[str, Any]]] = None,
        col_metadata: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> None:
        self.retriever.add_matrix(
            table_id,
            matrix,
            row_metadata=row_metadata,
            col_metadata=col_metadata,
        )

    def add_geometry(
        self,
        item_id: Any,
        coordinates: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.retriever.add_geometry(item_id, coordinates, metadata=metadata)

    def add_graph_node(
        self, node_id: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self.retriever.add_graph_node(node_id, metadata=metadata)

    def add_graph_edge(
        self,
        source: Any,
        target: Any,
        weight: float = 1.0,
        directed: bool = True,
    ) -> None:
        self.retriever.add_graph_edge(
            source, target, weight=weight, directed=directed
        )

    def add_template(
        self,
        template_id: Any,
        fingerprint: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.retriever.add_template(template_id, fingerprint, metadata=metadata)

    def add_frequency(
        self,
        doc_id: Any,
        tokens: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.retriever.add_frequency(doc_id, tokens, metadata=metadata)

    def add_recurrence(
        self,
        item_id: Any,
        items: Set[int],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.retriever.add_recurrence(item_id, items, metadata=metadata)

    def retrieve(
        self,
        query_embedding: Optional[np.ndarray] = None,
        query_matrix_vec: Optional[np.ndarray] = None,
        query_coords: Optional[np.ndarray] = None,
        query_graph_seeds: Optional[List[Any]] = None,
        query_fingerprint: Optional[Any] = None,
        query_tokens: Optional[List[str]] = None,
        query_set: Optional[Set[int]] = None,
        top_k: Optional[int] = None,
    ) -> HybridRanking:
        return self.retriever.retrieve(
            query_embedding=query_embedding,
            query_matrix_vec=query_matrix_vec,
            query_coords=query_coords,
            query_graph_seeds=query_graph_seeds,
            query_fingerprint=query_fingerprint,
            query_tokens=query_tokens,
            query_set=query_set,
            top_k=top_k,
        )

    def generate_report(
        self,
        ranking: HybridRanking,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RetrievalReport:
        return RetrievalReport(
            ranking=ranking,
            latency_ms=latency_ms,
            num_sources=ranking.num_sources,
            metadata=metadata or {},
        )
