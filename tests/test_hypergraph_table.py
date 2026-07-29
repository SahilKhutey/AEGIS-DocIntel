"""
Unit tests for Hypergraph Table Representation Engine (Task C-3).
"""

import numpy as np
import pytest
from src.engines.matrix.hypergraph import (
    TableHypergraphEngine, TableHypergraph, HyperCell, HyperEdge
)


def test_table_hypergraph_construction():
    engine = TableHypergraphEngine()
    grid = [
        ["Quarter", "Revenue", "Margin"],
        ["Q1", "$10M", "20%"],
        ["Q2", "$12M", "22%"],
    ]

    hg = engine.build_hypergraph(grid, table_id="t1", header_rows=1)

    assert len(hg.cells) == 9
    assert "edge_row_0" in hg.hyperedges
    assert "edge_col_1" in hg.hyperedges
    assert "edge_hdr_bind_0_0" in hg.hyperedges


def test_table_hypergraph_incidence_matrix():
    engine = TableHypergraphEngine()
    grid = [
        ["Header A", "Header B"],
        ["Val A", "Val B"],
    ]
    hg = engine.build_hypergraph(grid, table_id="t2")
    H = hg.get_incidence_matrix()

    assert H.shape[0] == 4  # 4 vertices
    assert H.shape[1] > 0   # > 0 hyperedges
    assert np.all((H == 0) | (H == 1))


def test_dual_hypergraph():
    engine = TableHypergraphEngine()
    grid = [
        ["H1", "H2"],
        ["D1", "D2"],
    ]
    hg = engine.build_hypergraph(grid)
    dual = hg.get_dual_hypergraph()

    assert len(dual.cells) == len(hg.hyperedges)
    assert len(dual.hyperedges) == len(hg.cells)
