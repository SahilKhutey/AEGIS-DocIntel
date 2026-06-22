"""
AEGIS-AMDI-OS — Graph Object Schema
=====================================
G = (V, E) — Document structure as graph.
"""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Optional

import numpy as np
from pydantic import BaseModel, Field, computed_field


class EdgeType(str, Enum):
    """Types of edges in the document graph."""
    FOLLOWS = "follows"
    PRECEDES = "precedes"
    ABOVE = "above"
    BELOW = "below"
    LEFT_OF = "left_of"
    RIGHT_OF = "right_of"
    NEXT_PAGE = "next_page"
    PREVIOUS_PAGE = "previous_page"
    REFERENCES = "references"
    REFERENCED_BY = "referenced_by"
    TABLE_TO_CAPTION = "table_to_caption"
    FIGURE_TO_CAPTION = "figure_to_caption"
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    SIMILAR_TO = "similar_to"
    SAME_SECTION = "same_section"


class NodeType(str, Enum):
    """Types of graph nodes."""
    ELEMENT = "element"
    PAGE = "page"
    SECTION = "section"
    TABLE = "table"
    FIGURE = "figure"
    ENTITY = "entity"
    CONCEPT = "concept"


class GraphNode(BaseModel):
    """A node in the document graph."""
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType = NodeType.ELEMENT
    label: str = ""
    page: int | None = None
    weight: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """An edge in the document graph."""
    edge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    src_id: str
    dst_id: str
    edge_type: EdgeType = EdgeType.FOLLOWS
    weight: float = 1.0
    bidirectional: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphMetrics(BaseModel):
    """Computed graph metrics."""
    n_nodes: int = 0
    n_edges: int = 0
    density: float = 0.0
    n_components: int = 0
    avg_degree: float = 0.0
    max_degree: int = 0
    clustering_coefficient: float = 0.0
    diameter: int = 0

    @computed_field
    @property
    def is_connected(self) -> bool:
        return self.n_components == 1

    @computed_field
    @property
    def is_dense(self) -> bool:
        return self.density > 0.5


class GraphObject(BaseModel):
    """
    G = (V, E) — Heterogeneous document graph.

    Represents document structure as a typed graph.
    """

    # ===== Identity =====
    graph_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str

    # ===== Structure =====
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)

    # ===== Computed metrics =====
    metrics: GraphMetrics = Field(default_factory=GraphMetrics)

    # ===== Metadata =====
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""

    # ===== Computed =====
    @computed_field
    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

    @computed_field
    @property
    def n_edges(self) -> int:
        return len(self.edges)

    @computed_field
    @property
    def density(self) -> float:
        if self.n_nodes < 2:
            return 0.0
        max_edges = self.n_nodes * (self.n_nodes - 1)
        return self.n_edges / max_edges if max_edges > 0 else 0.0

    # ===== Methods =====
    def get_neighbors(self, node_id: str) -> list[GraphNode]:
        """Get all neighbors of a node."""
        neighbor_ids = set()
        for edge in self.edges:
            if edge.src_id == node_id:
                neighbor_ids.add(edge.dst_id)
            elif edge.bidirectional and edge.dst_id == node_id:
                neighbor_ids.add(edge.src_id)
        node_map = {n.node_id: n for n in self.nodes}
        return [node_map[nid] for nid in neighbor_ids if nid in node_map]

    def get_node_degree(self, node_id: str) -> int:
        """Get degree of a node."""
        degree = 0
        for edge in self.edges:
            if edge.src_id == node_id:
                degree += 1
            if edge.bidirectional and edge.dst_id == node_id:
                degree += 1
        return degree

    def get_pagerank(self, damping: float = 0.85, n_iter: int = 100) -> dict[str, float]:
        """Compute PageRank for all nodes."""
        if not self.nodes:
            return {}
        node_ids = [n.node_id for n in self.nodes]
        n = len(node_ids)
        idx = {nid: i for i, nid in enumerate(node_ids)}
        # Build transition matrix
        M = np.zeros((n, n))
        for edge in self.edges:
            if edge.src_id in idx and edge.dst_id in idx:
                M[idx[edge.dst_id], idx[edge.src_id]] = edge.weight
        # Normalize columns
        col_sums = M.sum(axis=0)
        for j in range(n):
            if col_sums[j] > 0:
                M[:, j] /= col_sums[j]
        # Power iteration
        pr = np.ones(n) / n
        for _ in range(n_iter):
            pr = (1 - damping) / n + damping * M @ pr
        return {nid: float(pr[i]) for i, nid in enumerate(node_ids)}

    model_config = {"json_schema_extra": {
        "example": {
            "doc_id": "doc-123",
            "nodes": [{"node_id": "n1", "type": "element", "page": 1}],
            "edges": [{"src_id": "n1", "dst_id": "n2", "edge_type": "follows"}],
        }
    }}
