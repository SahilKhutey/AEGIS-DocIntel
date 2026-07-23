"""
Hybrid Retriever
================

Combines 7 retrieval strategies: Semantic, Matrix, Geometry, Graph,
Template, Frequency, and Recurrence searches using rank fusion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from .semantic_search import SemanticSearch
from .matrix_search import MatrixSearch
from .geometry_search import GeometrySearch
from .graph_search import GraphSearch
from .template_search import TemplateSearch
from .frequency_search import FrequencySearch
from .recurrence_search import RecurrenceSearch
from .ranker import HybridRanker, HybridRanking


@dataclass
class HybridConfig:
    """Configuration for the Hybrid Retriever."""

    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "semantic": 0.3,
            "matrix": 0.1,
            "geometry": 0.1,
            "graph": 0.1,
            "template": 0.1,
            "frequency": 0.2,
            "recurrence": 0.1,
        }
    )
    fusion_method: str = "rrf"
    rrf_k: int = 60
    top_k: int = 10


class HybridRetriever:
    """
    Multi-index hybrid retriever combining 7 search strategies.
    """

    def __init__(self, config: Optional[HybridConfig] = None) -> None:
        self.config = config or HybridConfig()
        self.semantic = SemanticSearch()
        self.matrix = MatrixSearch()
        self.geometry = GeometrySearch()
        self.graph = GraphSearch()
        self.template = TemplateSearch()
        self.frequency = FrequencySearch()
        self.recurrence = RecurrenceSearch()
        self.ranker = HybridRanker(
            method=self.config.fusion_method,
            rrf_k=self.config.rrf_k,
            weights=self.config.weights,
        )

    def add_semantic(
        self,
        doc_id: Any,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.semantic.add(doc_id, embedding, metadata=metadata)

    def add_matrix(
        self,
        table_id: Any,
        matrix: np.ndarray,
        row_metadata: Optional[Dict[int, Dict[str, Any]]] = None,
        col_metadata: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> None:
        self.matrix.add(
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
        self.geometry.add(item_id, coordinates, metadata=metadata)

    def add_graph_node(
        self, node_id: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self.graph.add_node(node_id, metadata=metadata)

    def add_graph_edge(
        self,
        source: Any,
        target: Any,
        weight: float = 1.0,
        directed: bool = True,
    ) -> None:
        self.graph.add_edge(source, target, weight=weight, directed=directed)

    def add_template(
        self,
        template_id: Any,
        fingerprint: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.template.add(template_id, fingerprint, metadata=metadata)

    def add_frequency(
        self,
        doc_id: Any,
        tokens: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.frequency.add(doc_id, tokens, metadata=metadata)

    def add_recurrence(
        self,
        item_id: Any,
        items: Set[int],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.recurrence.add(item_id, items, metadata=metadata)

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
        """
        Execute parallel queries across the 7 sub-indices and fuse the results.
        """
        method_results: Dict[str, List[Tuple[Any, float]]] = {}
        search_top_k = top_k or self.config.top_k

        # 1. Semantic
        if query_embedding is not None:
            try:
                res = self.semantic.search(query_embedding, top_k=search_top_k)
                method_results["semantic"] = [(r.doc_id, r.score) for r in res]
            except Exception:
                method_results["semantic"] = []

        # 2. Matrix
        if query_matrix_vec is not None:
            try:
                res = self.matrix.search_column(query_matrix_vec, top_k=search_top_k)
                method_results["matrix"] = [(r.item_id, r.score) for r in res]
            except Exception:
                method_results["matrix"] = []

        # 3. Geometry
        if query_coords is not None:
            try:
                res = self.geometry.knn(query_coords, k=search_top_k)
                method_results["geometry"] = [(r.item_id, r.similarity) for r in res]
            except Exception:
                method_results["geometry"] = []

        # 4. Graph
        if query_graph_seeds is not None:
            try:
                res = self.graph.personalized_pagerank(query_graph_seeds, top_k=search_top_k)
                method_results["graph"] = [(r.node_id, r.score) for r in res]
            except Exception:
                method_results["graph"] = []

        # 5. Template
        if query_fingerprint is not None:
            try:
                res = self.template.search(query_fingerprint, top_k=search_top_k)
                method_results["template"] = [(r.template_id, r.similarity) for r in res]
            except Exception:
                method_results["template"] = []

        # 6. Frequency
        if query_tokens is not None:
            try:
                res = self.frequency.search(query_tokens, top_k=search_top_k)
                method_results["frequency"] = [(r.doc_id, r.score) for r in res]
            except Exception:
                method_results["frequency"] = []

        # 7. Recurrence
        if query_set is not None:
            try:
                res = self.recurrence.query(query_set, top_k=search_top_k)
                method_results["recurrence"] = [(r.item_id, r.similarity) for r in res]
            except Exception:
                method_results["recurrence"] = []

        # Filter out empty results to prevent fusion failure
        active_results = {k: v for k, v in method_results.items() if v}
        if not active_results:
            return HybridRanking(
                ranked_docs=[],
                method=self.config.fusion_method,
                num_docs=0,
                num_sources=0,
            )

        return self.ranker.fuse(
            active_results,
            weights=self.config.weights,
            top_k=search_top_k,
        )
