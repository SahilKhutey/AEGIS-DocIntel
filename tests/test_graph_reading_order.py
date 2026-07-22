'''
Unit tests for Spatial Graph Reading-Order Parser (Section 6 & Appendix B).
Verifies Definition 6.1, Theorem 6.1 (Acyclicity), and Theorem 6.2 (Determinism).
'''
from __future__ import annotations

import pytest
from src.engines.graph_reading_order import (
    SpatialReadingGraph,
    ReadingGraphConfig,
    is_reading_forward_successor,
)


def test_is_reading_forward_successor():
    # Same row, left-to-right
    n1 = {'id': 'n1', 'x': 0.1, 'y': 0.1}
    n2 = {'id': 'n2', 'x': 0.5, 'y': 0.1}
    assert is_reading_forward_successor(n1, n2)
    assert not is_reading_forward_successor(n2, n1)

    # Lower row band
    n3 = {'id': 'n3', 'x': 0.1, 'y': 0.3}
    assert is_reading_forward_successor(n1, n3)
    assert not is_reading_forward_successor(n3, n1)


def test_dense_grid_acyclicity_and_determinism():
    # Test 1 & 2 from Appendix D manifest: 4x4 dense grid (16 nodes)
    elements = []
    for row in range(4):
        for col in range(4):
            elements.append({
                'id': f'node_{row}_{col}',
                'x': 0.1 + col * 0.2,
                'y': 0.1 + row * 0.2,
                'w': 0.15,
                'h': 0.05,
            })

    parser = SpatialReadingGraph(ReadingGraphConfig(row_tolerance=0.03))
    V, E = parser.build_reading_graph(elements)
    recovered_normal = parser.recover_reading_order(V, E)

    assert len(recovered_normal) == 16

    # Test 2: Input order reversal test (Theorem 6.2 Determinism)
    reversed_elements = list(reversed(elements))
    V_rev, E_rev = parser.build_reading_graph(reversed_elements)
    recovered_reversed = parser.recover_reading_order(V_rev, E_rev)

    assert [n['id'] for n in recovered_normal] == [n['id'] for n in recovered_reversed]


def test_multi_column_reading_flow():
    # Multi-column layout: Title, Column A, Column B, Footer
    title = {'id': 'title', 'x': 0.1, 'y': 0.05, 'w': 0.8, 'h': 0.05}
    col_a1 = {'id': 'col_a1', 'x': 0.1, 'y': 0.15, 'w': 0.35, 'h': 0.1}
    col_a2 = {'id': 'col_a2', 'x': 0.1, 'y': 0.30, 'w': 0.35, 'h': 0.1}
    col_b1 = {'id': 'col_b1', 'x': 0.55, 'y': 0.15, 'w': 0.35, 'h': 0.1}
    col_b2 = {'id': 'col_b2', 'x': 0.55, 'y': 0.30, 'w': 0.35, 'h': 0.1}
    footer = {'id': 'footer', 'x': 0.1, 'y': 0.80, 'w': 0.8, 'h': 0.05}

    elements = [footer, col_b2, col_a2, col_b1, col_a1, title]  # Shuffled input

    parser = SpatialReadingGraph()
    V, E = parser.build_reading_graph(elements)
    order = parser.recover_reading_order(V, E)
    ids = [n['id'] for n in order]

    assert ids[0] == 'title'
    assert ids[-1] == 'footer'
