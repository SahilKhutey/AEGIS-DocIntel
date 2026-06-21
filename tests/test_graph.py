"""Tests for the graph engine."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

import pytest
import numpy as np
import networkx as nx
from src.core.geometric_element import GeometricElement, ElementType
from src.core.normalized_document import BoundingBox
from src.engines.graph import (
    GraphEngine, DocumentGraph, GraphNode, GraphEdge,
    GraphMetrics, EdgeType,
)

# ============================================================

# HELPERS

# ============================================================

def make_element(
    element_id: str = "e1",
    content: str = "Test",
    page: int = 1,
    etype: ElementType = ElementType.TEXT,
    x0: float = 0.1, y0: float = 0.1,
    x1: float = 0.5, y1: float = 0.3,
    section: str = None,
) -> GeometricElement:

    return GeometricElement(
        element_id=element_id, content=content, page=page, type=etype,
        bbox=BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1), section=section,
    )

# ============================================================

# INITIALIZATION

# ============================================================

def test_init():
    engine = GraphEngine()

    assert engine.graph.graph.number_of_nodes() == 0

    assert engine.graph.graph.number_of_edges() == 0

def test_custom_damping():
    engine = GraphEngine(damping=0.9)

    assert engine.damping == 0.9

# ============================================================

# 1. NODE BUILDER

# ============================================================

def test_build_nodes_basic():
    engine = GraphEngine()

    elements = [make_element(f"e{i}") for i in range(5)]

    nodes = engine.build_nodes(elements)

    assert len(nodes) == 5

    assert engine.graph.graph.number_of_nodes() == 5

def test_build_nodes_properties():
    engine = GraphEngine()

    elements = [make_element("e1", content="Hello world", page=3, section="intro")]

    nodes = engine.build_nodes(elements)

    node = nodes[0]

    assert node.page == 3

    assert node.section == "intro"

    assert "Hello world" in node.label

def test_build_section_nodes():
    engine = GraphEngine()

    sections = ["Introduction", "Methods", "Results"]

    nodes = engine.build_section_nodes(sections)

    assert len(nodes) == 3

    assert all(n.node_type == "section" for n in nodes)

def test_build_page_nodes():
    engine = GraphEngine()

    nodes = engine.build_page_nodes(n_pages=5)

    assert len(nodes) == 5

    assert all(n.node_type == "page" for n in nodes)

    assert nodes[2].page == 3

def test_build_entity_nodes():
    from src.engines.semantic import Entity, EntityType

    engine = GraphEngine()

    entities = [
        Entity(text="Apple", type=EntityType.ORGANIZATION),
        Entity(text="Apple", type=EntityType.ORGANIZATION),  # Duplicate

        Entity(text="Microsoft", type=EntityType.ORGANIZATION),
    ]

    nodes = engine.build_entity_nodes(entities, doc_id="d1")

    # Deduplication: 2 unique entities

    assert len(nodes) == 2

def test_get_node():
    engine = GraphEngine()

    elements = [make_element("e1"), make_element("e2")]

    engine.build_nodes(elements)

    node = engine.get_node("e1")

    assert node is not None

    assert node.node_id == "e1"

def test_get_node_not_found():
    engine = GraphEngine()

    assert engine.get_node("nonexistent") is None

def test_get_nodes_by_type():
    engine = GraphEngine()

    elements = [
        make_element("t1", etype=ElementType.TABLE),
        make_element("t2", etype=ElementType.TABLE),
        make_element("tx", etype=ElementType.TEXT),
    ]

    engine.build_nodes(elements)

    tables = engine.get_nodes_by_type("table")

    assert len(tables) == 2

# ============================================================

# 2. EDGE BUILDER

# ============================================================

def test_build_edges_follows():
    engine = GraphEngine()

    elements = [
        make_element("e1", y0=0.1, y1=0.2),
        make_element("e2", y0=0.3, y1=0.4),
        make_element("e3", y0=0.5, y1=0.6),
    ]

    nodes = engine.build_nodes(elements)

    edges = engine.build_edges(elements)

    # Reading order: e1 → e2 → e3

    assert any(e.src_id == "e1" and e.dst_id == "e2" for e in edges)

    assert any(e.src_id == "e2" and e.dst_id == "e3" for e in edges)

def test_build_edges_next_page():
    engine = GraphEngine()

    elements = [
        make_element("e1", page=1, section="intro"),
        make_element("e2", page=2, section="intro"),
    ]

    engine.build_nodes(elements)

    edges = engine.build_edges(elements)

    # Cross-page edge within same section

    next_page = [e for e in edges if e.edge_type == EdgeType.NEXT_PAGE]

    assert len(next_page) >= 1

def test_build_edges_same_section():
    engine = GraphEngine()

    elements = [
        make_element("e1", page=1, section="intro"),
        make_element("e2", page=1, section="intro"),
    ]

    engine.build_nodes(elements)

    edges = engine.build_edges(elements)

    # Same section edges

    same_sec = [e for e in edges if e.edge_type == EdgeType.SAME_SECTION]

    assert len(same_sec) >= 1

def test_build_spatial_edges_above():
    engine = GraphEngine()

    elements = [
        make_element("e1", page=1, x0=0.1, y0=0.1, x1=0.5, y1=0.2),  # Top

        make_element("e2", page=1, x0=0.1, y0=0.3, x1=0.5, y1=0.4),  # Bottom
    ]

    engine.build_nodes(elements)

    edges = engine.build_spatial_edges(elements)

    # e1 should be above e2

    above_edges = [e for e in edges if e.edge_type == EdgeType.ABOVE]

    assert len(above_edges) >= 1

def test_build_reference_edges():
    engine = GraphEngine()

    elements = [make_element("e1"), make_element("e2")]

    engine.build_nodes(elements)

    edges = engine.build_reference_edges(elements, [
        ("e1", "e2", "see page 5"),
    ])

    assert len(edges) == 1

    assert edges[0].edge_type == EdgeType.REFERENCES

def test_build_table_caption_edges():
    engine = GraphEngine()

    elements = [
        make_element("t1", etype=ElementType.TABLE, x0=0.1, y0=0.2),
        make_element("c1", etype=ElementType.CAPTION, x0=0.1, y0=0.15),
    ]

    engine.build_nodes(elements)

    edges = engine.build_table_caption_edges(elements)

    assert len(edges) >= 1

def test_get_edges_by_type():
    engine = GraphEngine()

    elements = [
        make_element("e1", y0=0.1, y1=0.2),
        make_element("e2", y0=0.3, y1=0.4),
        make_element("e3", y0=0.5, y1=0.6),
    ]

    engine.build_nodes(elements)

    engine.build_edges(elements)

    follows = engine.get_edges_by_type(EdgeType.FOLLOWS)

    assert len(follows) >= 2

def test_get_edge():
    engine = GraphEngine()

    elements = [make_element("e1"), make_element("e2")]

    engine.build_nodes(elements)

    engine.build_edges(elements)

    edge = engine.get_edge("e1", "e2")

    assert edge is not None

    assert edge.edge_type == EdgeType.FOLLOWS

# ============================================================

# 3. CENTRALITY

# ============================================================

def test_degree_centrality():
    engine = GraphEngine()

    elements = [
        make_element("hub", page=1),
        make_element("spoke1", page=1),
        make_element("spoke2", page=1),
        make_element("spoke3", page=1),
    ]

    engine.build_nodes(elements)

    # Hub has higher degree

    elements_sorted = sorted(elements, key=lambda e: e.bbox.y0 if e.bbox else 0)

    engine.build_edges(elements_sorted)

    deg_cent = engine.degree_centrality()

    assert "hub" in deg_cent

def test_degree_centrality_empty():
    engine = GraphEngine()

    assert engine.degree_centrality() == {}

def test_betweenness_centrality():
    engine = GraphEngine()

    # Star graph: hub connects all leaves

    elements = [make_element(f"e{i}") for i in range(5)]

    engine.build_nodes(elements)

    # Build star: connect e0 to all others

    for i in range(1, 5):

        engine.graph.add_edge(GraphEdge(
            edge_id=f"e{i}", src_id="e0", dst_id=f"e{i}",
            edge_type=EdgeType.FOLLOWS,
            bidirectional=True,
        ))

    betw = engine.betweenness_centrality()

    # e0 should have highest betweenness (it bridges all paths)

    assert betw.get("e0", 0) > 0

def test_betweenness_empty():
    engine = GraphEngine()

    engine.graph.add_node(GraphNode(node_id="a", node_type="element"))

    betw = engine.betweenness_centrality()

    assert betw == {"a": 0.0}

def test_closeness_centrality():
    engine = GraphEngine()

    elements = [
        make_element("a"), make_element("b"), make_element("c"),
    ]

    engine.build_nodes(elements)

    engine.graph.add_edge(GraphEdge("e1", "a", "b", EdgeType.FOLLOWS))

    engine.graph.add_edge(GraphEdge("e2", "b", "c", EdgeType.FOLLOWS))

    close = engine.closeness_centrality()

    assert "a" in close

    assert "b" in close

    assert "c" in close

def test_eigenvector_centrality():
    engine = GraphEngine()

    elements = [make_element(f"e{i}") for i in range(4)]

    engine.build_nodes(elements)

    # Connected graph

    engine.graph.add_edge(GraphEdge("e1", "e0", "e1", EdgeType.FOLLOWS))

    engine.graph.add_edge(GraphEdge("e2", "e1", "e2", EdgeType.FOLLOWS))

    engine.graph.add_edge(GraphEdge("e3", "e2", "e3", EdgeType.FOLLOWS))

    eigen = engine.eigenvector_centrality()

    assert len(eigen) == 4

def test_compute_all_centralities():
    engine = GraphEngine()

    elements = [make_element(f"e{i}", y0=0.1 * i, y1=0.1 * i + 0.05) for i in range(4)]

    engine.build_nodes(elements)

    engine.build_edges(elements)

    scores = engine.compute_all_centralities(include_eigenvector=False)

    assert len(scores) == 4

    for node_id, score in scores.items():

        assert isinstance(score.degree, float)

        assert isinstance(score.pagerank, float)

# ============================================================

# 4. PAGERANK

# ============================================================

def test_pagerank_basic():
    engine = GraphEngine()

    # V-structure: a → b ← c

    for src, dst in [("a", "b"), ("c", "b")]:

        engine.graph.add_edge(GraphEdge(
            edge_id=f"e-{src}-{dst}", src_id=src, dst_id=dst,
            edge_type=EdgeType.FOLLOWS,
        ))

    pr = engine.pagerank()

    assert abs(sum(pr.values()) - 1.0) < 1e-6

    # 'b' should have highest rank (sink node)

    assert pr["b"] > pr["a"]

    assert pr["b"] > pr["c"]

def test_pagerank_empty():
    engine = GraphEngine()

    assert engine.pagerank() == {}

def test_pagerank_single_node():
    engine = GraphEngine()

    engine.graph.add_node(GraphNode(node_id="a", node_type="element"))

    pr = engine.pagerank()

    assert pr == {"a": 1.0}

def test_pagerank_dangling_node():
    """Node with no outgoing edges should still get a rank."""

    engine = GraphEngine()

    engine.graph.add_edge(GraphEdge("e", "a", "b", EdgeType.FOLLOWS))

    pr = engine.pagerank()

    assert "a" in pr

    assert "b" in pr

def test_pagerank_convergence():
    engine = GraphEngine()

    # Larger graph

    for i in range(10):

        engine.graph.add_edge(GraphEdge(
            edge_id=f"e{i}", src_id=f"n{i}", dst_id=f"n{(i+1) % 10}",
            edge_type=EdgeType.FOLLOWS,
        ))

    pr = engine.pagerank()

    assert abs(sum(pr.values()) - 1.0) < 1e-4

def test_personalized_pagerank():
    engine = GraphEngine()

    for src, dst in [("a", "b"), ("b", "c"), ("c", "a")]:

        engine.graph.add_edge(GraphEdge(
            edge_id=f"e-{src}-{dst}", src_id=src, dst_id=dst,
            edge_type=EdgeType.FOLLOWS,
        ))

    personalization = {"a": 1.0, "b": 0.0, "c": 0.0}

    pr = engine.personalized_pagerank(personalization)

    assert abs(sum(pr.values()) - 1.0) < 1e-6

def test_power_iteration_pagerank():
    engine = GraphEngine()

    for src, dst in [("a", "b"), ("b", "c"), ("c", "a")]:

        engine.graph.add_edge(GraphEdge(
            edge_id=f"e-{src}-{dst}", src_id=src, dst_id=dst,
            edge_type=EdgeType.FOLLOWS,
        ))

    pr = engine.power_iteration_pagerank()

    assert abs(sum(pr.values()) - 1.0) < 1e-3

def test_power_iteration_matches_networkx():
    """Our manual implementation should match NetworkX."""

    engine = GraphEngine()

    for i in range(5):

        engine.graph.add_edge(GraphEdge(
            edge_id=f"e{i}", src_id=f"n{i}", dst_id=f"n{(i+1) % 5}",
            edge_type=EdgeType.FOLLOWS,
        ))

    pr_nx = engine.pagerank(max_iter=200, tol=1e-12)

    pr_custom = engine.power_iteration_pagerank(max_iter=200, tol=1e-12)

    # Should be approximately equal

    for node in pr_nx:

        assert abs(pr_nx[node] - pr_custom[node]) < 1e-2

# ============================================================

# 5. RELATIONSHIP MAPPING

# ============================================================

def test_find_paths_simple():
    engine = GraphEngine()

    # a → b → c → d

    for src, dst in [("a", "b"), ("b", "c"), ("c", "d")]:

        engine.graph.add_edge(GraphEdge(
            edge_id=f"e-{src}-{dst}", src_id=src, dst_id=dst,
            edge_type=EdgeType.FOLLOWS,
        ))

    paths = engine.find_paths("a", "d")

    assert len(paths) >= 1

    # Direct path: a → b → c → d

    assert any(p.path == ["a", "b", "c", "d"] for p in paths)

def test_find_paths_no_path():
    engine = GraphEngine()

    engine.graph.add_node(GraphNode(node_id="a", node_type="element"))

    engine.graph.add_node(GraphNode(node_id="b", node_type="element"))

    paths = engine.find_paths("a", "b")

    assert paths == []

def test_find_paths_self():
    engine = GraphEngine()

    engine.graph.add_node(GraphNode(node_id="a", node_type="element"))

    paths = engine.find_paths("a", "a")

    assert paths == []  # No self-loops

def test_shortest_path():
    engine = GraphEngine()

    for src, dst in [("a", "b"), ("b", "c"), ("a", "c")]:

        engine.graph.add_edge(GraphEdge(
            edge_id=f"e-{src}-{dst}", src_id=src, dst_id=dst,
            edge_type=EdgeType.FOLLOWS,
        ))

    path = engine.shortest_path("a", "c")

    assert path is not None

    assert path.src_id == "a"

    assert path.dst_id == "c"

def test_shortest_path_no_path():
    engine = GraphEngine()

    engine.graph.add_node(GraphNode(node_id="a", node_type="element"))

    engine.graph.add_node(GraphNode(node_id="b", node_type="element"))
    path = engine.shortest_path("a", "b")
    assert path is None

def test_get_neighbors():
    engine = GraphEngine()
    elements = [
        make_element("e1"),
        make_element("e2"),
    ]
    engine.build_nodes(elements)
    engine.build_edges(elements)
    neighbors = engine.get_neighbors("e1")
    assert len(neighbors) == 1
    assert neighbors[0] == "e2"

    # Test with edge type filter
    neighbors_follows = engine.get_neighbors("e1", EdgeType.FOLLOWS)
    assert len(neighbors_follows) == 1

    neighbors_spatial = engine.get_neighbors("e1", EdgeType.ABOVE)
    assert len(neighbors_spatial) == 0

def test_find_relationships():
    engine = GraphEngine()
    elements = [
        make_element("e1"),
        make_element("e2"),
        make_element("e3"),
    ]
    engine.build_nodes(elements)
    engine.build_edges(elements)

    rels = engine.find_relationships("e1", max_hops=2)
    assert "follows" in rels
    assert len(rels["follows"]) == 2

def test_find_similar_nodes():
    engine = GraphEngine()
    elements = [
        make_element("e1"),
        make_element("e2"),
        make_element("e3"),
    ]
    engine.build_nodes(elements)
    engine.build_edges(elements)
    similar = engine.find_similar_nodes("e1", top_k=2)
    assert len(similar) > 0

def test_subgraphs():
    engine = GraphEngine()
    elements = [
        make_element("e1", section="sec1"),
        make_element("e2", section="sec1"),
        make_element("e3", section="sec2"),
    ]
    engine.build_nodes(elements)

    sub_section = engine.get_subgraph_by_section("sec1")
    assert len(sub_section.nodes) == 2

    sub_type = engine.get_subgraph_by_node_type("text")
    assert len(sub_type.nodes) == 3

def test_distributions_and_json():
    engine = GraphEngine()
    elements = [
        make_element("e1", etype=ElementType.TEXT),
        make_element("e2", etype=ElementType.TABLE),
    ]
    engine.build_nodes(elements)
    engine.build_edges(elements)

    node_dist = engine.node_type_distribution()
    edge_dist = engine.edge_type_distribution()

    assert node_dist["text"] == 1
    assert node_dist["table"] == 1
    assert edge_dist["follows"] == 1

    json_data = engine.export_to_json()
    assert len(json_data["nodes"]) == 2
    assert len(json_data["edges"]) == 1

    # Test statistics
    stats = engine.statistics()
    assert stats.n_nodes == 2
    assert stats.n_edges == 1
    assert stats.is_connected is True
    assert stats.is_dense is False

    engine.clear()
    assert engine.graph.graph.number_of_nodes() == 0
