"""Examples of using the graph engine."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

from src.engines.graph import (
    GraphEngine, DocumentGraph,
    EDGE_FOLLOWS, EDGE_CONTAINS, EDGE_REFERENCES, EDGE_BELONGS_TO,
)
from src.engines.geometry.element import GeometricElement, ElementType


def main():
    print("=== Graph Engine Usage ===")
    
    # 1. Initialize engine
    engine = GraphEngine(alpha=0.85, pagerank_max_iter=100)
    print("GraphEngine initialized.")
    
    # 2. Build mock elements representing a document layout
    # We will simulate a document with 2 pages and sections
    elements = [
        GeometricElement(
            element_id="el-header-p1",
            page=1,
            type=ElementType.HEADER,
            content="AEGIS DocIntel Annual Report",
        ),
        GeometricElement(
            element_id="el-h1",
            page=1,
            type=ElementType.HEADING,
            section="sec-intro",
            content="1. Introduction",
        ),
        GeometricElement(
            element_id="el-p1",
            page=1,
            type=ElementType.PARAGRAPH,
            section="sec-intro",
            content="This report describes our performance in FY2026. For details on revenue, see page 2.",
        ),
        GeometricElement(
            element_id="el-p2",
            page=1,
            type=ElementType.PARAGRAPH,
            section="sec-intro",
            content="We observed significant expansion across all sectors.",
        ),
        GeometricElement(
            element_id="el-h2",
            page=2,
            type=ElementType.HEADING,
            section="sec-finance",
            content="2. Financial Results",
        ),
        GeometricElement(
            element_id="el-table1",
            page=2,
            type=ElementType.TABLE,
            section="sec-finance",
            content="Table of financial stats: Revenue $5M, Net margin 20%.",
        ),
    ]
    
    # 3. Build graph structure
    print("\nBuilding document graph...")
    dg = engine.build(elements)
    print(f"Graph built successfully: {dg}")
    
    # 4. View PageRank scores
    print("\nPageRank scores (importance weight) written back to metadata:")
    for el in elements:
        pr = el.metadata.get("pagerank", 0.0)
        print(f"  - Node {el.element_id} ({el.type.value}): {pr:.4f}")
        
    # 5. BFS Neighbors Traversal
    print("\nBFS neighbors traversal (bidirectional):")
    # Neighbors of introduction paragraph el-p1 up to depth 2
    neighbors = engine.bfs_neighbors("el-p1", depth=2)
    print(f"  - Neighbors of 'el-p1' within 2 hops: {neighbors}")
    
    # 6. Graph Proximity Scoring
    print("\nGraph Proximity / Structural scores:")
    # If the user searches for "revenue", the semantic engine hits "el-p1" and "el-table1"
    seed_ids = ["el-p1"]
    print(f"  Proximity scores relative to seed {seed_ids}:")
    for el in elements:
        score = engine.structural_score(el.element_id, seed_ids=seed_ids)
        print(f"    - {el.element_id}: proximity score = {score}")
        
    # 7. Print overall statistics
    print("\nRetrieving overall graph statistics:")
    stats = engine.statistics()
    print(f"  - Total nodes: {stats['nodes']}")
    print(f"  - Total edges: {stats['edges']}")
    print(f"  - Density: {stats['density']}")
    print(f"  - Avg Degree: {stats['avg_degree']}")
    print(f"  - Edge type distribution: {stats['edge_type_counts']}")
    print(f"  - NetworkX Available: {stats['nx_available']}")


if __name__ == "__main__":
    main()
