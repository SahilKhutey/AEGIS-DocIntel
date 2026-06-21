"""
Graph Dashboard
================

Visualizes graph structure: nodes, edges, PageRank,
centrality, communities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class GraphNode:
    """A node in the graph view."""

    node_id: str
    label: str
    node_type: str
    degree: int = 0
    pagerank: float = 0.0
    centrality: float = 0.0
    cluster_id: int = -1
    x: float = 0.0
    y: float = 0.0

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "node_type": self.node_type,
            "degree": self.degree,
            "pagerank": round(self.pagerank, 6),
            "centrality": round(self.centrality, 6),
            "cluster_id": self.cluster_id,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
        }


@dataclass
class GraphEdge:
    """An edge in the graph view."""

    source: str
    target: str
    weight: float = 1.0
    edge_type: str = "related"

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "weight": round(self.weight, 4),
            "edge_type": self.edge_type,
        }


@dataclass
class GraphViewData:
    """Data for graph dashboard."""

    document_id: str
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    num_clusters: int = 0
    density: float = 0.0
    average_degree: float = 0.0

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "num_clusters": self.num_clusters,
            "density": round(self.density, 4),
            "average_degree": round(self.average_degree, 4),
        }


class GraphDashboard:
    """Graph dashboard backend API."""

    def __init__(self) -> None:
        self.documents: Dict[str, GraphViewData] = {}

    def add_node(self, document_id: str, node: GraphNode) -> None:
        if document_id not in self.documents:
            self.documents[document_id] = GraphViewData(document_id=document_id)
        self.documents[document_id].nodes.append(node)

    def add_edge(self, document_id: str, edge: GraphEdge) -> None:
        if document_id not in self.documents:
            self.documents[document_id] = GraphViewData(document_id=document_id)
        self.documents[document_id].edges.append(edge)

    def compute_layout(self, document_id: str, iterations: int = 100) -> None:
        """Compute simple force-directed layout positions."""
        if document_id not in self.documents:
            return
        view = self.documents[document_id]
        if not view.nodes:
            return
        # initialize random positions
        import random
        rng = random.Random(42)
        for n in view.nodes:
            n.x = rng.uniform(0, 800)
            n.y = rng.uniform(0, 600)
        # simple iterative layout (Fruchterman-Reingold-like)
        for _ in range(iterations):
            for n in view.nodes:
                fx, fy = 0.0, 0.0
                for m in view.nodes:
                    if m.node_id == n.node_id:
                        continue
                    dx = n.x - m.x
                    dy = n.y - m.y
                    dist = max((dx * dx + dy * dy) ** 0.5, 0.01)
                    fx += dx / dist * 10
                    fy += dy / dist * 10
                # edges pull
                for e in view.edges:
                    if e.source == n.node_id:
                        m = next((x for x in view.nodes if x.node_id == e.target), None)
                    elif e.target == n.node_id:
                        m = next((x for x in view.nodes if x.node_id == e.source), None)
                    else:
                        continue
                    if m is None:
                        continue
                    dx = m.x - n.x
                    dy = m.y - n.y
                    dist = max((dx * dx + dy * dy) ** 0.5, 0.01)
                    fx += dx / dist * 5
                    fy += dy / dist * 5
                n.x += fx * 0.01
                n.y += fy * 0.01

    def get_view(self, document_id: str) -> GraphViewData:
        if document_id not in self.documents:
            return GraphViewData(document_id=document_id)
        view = self.documents[document_id]
        # compute density + average degree
        n_nodes = len(view.nodes)
        n_edges = len(view.edges)
        if n_nodes > 1:
            max_edges = n_nodes * (n_nodes - 1)
            view.density = (2 * n_edges) / max_edges if max_edges > 0 else 0
        if n_nodes > 0:
            degrees = [n.degree for n in view.nodes]
            view.average_degree = float(np.mean(degrees)) if degrees else 0.0
        view.num_clusters = len(set(n.cluster_id for n in view.nodes if n.cluster_id >= 0))
        return view
