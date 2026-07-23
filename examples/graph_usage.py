"""Examples of using the graph engine.

Repository Audit follow-up: this example previously called an API that does
not exist in src/engines/graph.py (GraphEngine(alpha=..., pagerank_max_iter=...),
engine.build(elements), engine.bfs_neighbors(...), engine.structural_score(...),
a dict-subscriptable statistics() return, and flat EDGE_* constants instead of
the real EdgeType enum) -- confirmed by actually running it, which failed at
import time on the missing EDGE_FOLLOWS et al. constants alone, before any of
the other mismatches would even have been reached. Rewritten below to exercise
the GraphEngine class that is actually implemented, method by method.
"""
import sys
from pathlib import Path
# Repository Audit follow-up: this previously pointed at the now-archived
# amdi-os/ directory, which no import in this file actually used (every
# import below is from src.*) -- the repo root is what these standalone
# scripts actually need on sys.path to resolve src.* imports when run
# directly (e.g. `python examples/matrix_usage.py`) from any working dir.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.engines.graph import GraphEngine, EdgeType
from src.engines.geometry.element import GeometricElement, ElementType
from src.core.normalized_document import BoundingBox


def main():
    print("=== Graph Engine Usage ===")

    # 1. Initialize engine
    engine = GraphEngine(damping=0.85)
    print("GraphEngine initialized.")

    # 2. Build mock elements representing a document layout: 2 pages, 2 sections.
    # bbox values give build_spatial_edges() something real to compare.
    elements = [
        GeometricElement(
            element_id="el-header-p1", page=1, type=ElementType.HEADER,
            content="AEGIS DocIntel Annual Report",
            bbox=BoundingBox(x0=0.05, y0=0.02, x1=0.95, y1=0.08),
        ),
        GeometricElement(
            element_id="el-h1", page=1, type=ElementType.HEADING,
            section="sec-intro", content="1. Introduction",
            bbox=BoundingBox(x0=0.05, y0=0.12, x1=0.50, y1=0.18),
        ),
        GeometricElement(
            element_id="el-p1", page=1, type=ElementType.PARAGRAPH,
            section="sec-intro",
            content="This report describes our performance in FY2026. "
                    "For details on revenue, see page 2.",
            bbox=BoundingBox(x0=0.05, y0=0.20, x1=0.95, y1=0.30),
        ),
        GeometricElement(
            element_id="el-p2", page=1, type=ElementType.PARAGRAPH,
            section="sec-intro",
            content="We observed significant expansion across all sectors.",
            bbox=BoundingBox(x0=0.05, y0=0.32, x1=0.95, y1=0.40),
        ),
        GeometricElement(
            element_id="el-h2", page=2, type=ElementType.HEADING,
            section="sec-finance", content="2. Financial Results",
            bbox=BoundingBox(x0=0.05, y0=0.12, x1=0.50, y1=0.18),
        ),
        GeometricElement(
            element_id="el-table1", page=2, type=ElementType.TABLE,
            section="sec-finance",
            content="Table of financial stats: Revenue $5M, Net margin 20%.",
            bbox=BoundingBox(x0=0.05, y0=0.20, x1=0.95, y1=0.45),
        ),
    ]

    # 3. Build graph structure. Real GraphEngine exposes separate builders
    # rather than one build(elements) call.
    print("\nBuilding document graph...")
    engine.build_nodes(elements)
    engine.build_edges(elements)          # FOLLOWS (reading order) + SAME_SECTION
    engine.build_spatial_edges(elements)  # ABOVE / BELOW
    stats = engine.statistics()
    print(f"Graph built: {stats.n_nodes} nodes, {stats.n_edges} edges "
          f"({stats.n_components} connected component(s))")

    # 4. PageRank scores (a dict keyed by node_id; the real engine does not
    # write these back into element.metadata automatically).
    print("\nPageRank scores (importance weight):")
    pr = engine.pagerank()
    for el in elements:
        print(f"  - Node {el.element_id} ({el.type.value}): {pr.get(el.element_id, 0.0):.4f}")

    # 5. Relationship traversal (BFS up to N hops, grouped by edge type).
    print("\nRelationships within 2 hops of 'el-p1', by edge type:")
    relationships = engine.find_relationships("el-p1", max_hops=2)
    for edge_type, edges in relationships.items():
        print(f"  - {edge_type}: {len(edges)} edge(s)")

    # 6. Degree centrality as a simple structural-importance proxy (the real
    # engine has no structural_score(); degree/betweenness/eigenvector/
    # PageRank centrality are the available structural signals).
    print("\nDegree centrality (structural importance):")
    degree_cent = engine.degree_centrality()
    for el in elements:
        print(f"    - {el.element_id}: degree centrality = {degree_cent.get(el.element_id, 0.0):.4f}")

    # 7. Shortest path between two nodes.
    print("\nShortest path from 'el-p1' to 'el-table1':")
    path = engine.shortest_path("el-p1", "el-table1")
    if path:
        print(f"  - {' -> '.join(path.path)} (length {path.length})")
    else:
        print("  - No path found (expected: FOLLOWS/SAME_SECTION edges don't "
              "cross from sec-intro to sec-finance in this mock layout).")

    # 8. Overall statistics and edge-type distribution.
    print("\nOverall statistics:")
    print(f"  - Total nodes: {stats.n_nodes}")
    print(f"  - Total edges: {stats.n_edges}")
    print(f"  - Density: {stats.density:.4f}")
    print(f"  - Avg degree: {stats.avg_degree:.4f}")
    print(f"  - Connected: {stats.is_connected}")
    print(f"  - Edge type distribution: {engine.edge_type_distribution()}")


if __name__ == "__main__":
    main()
