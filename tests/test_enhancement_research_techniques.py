'''
AEGIS-DocIntel / AMDI-OS — Mathematical & Enhancement Research Test Suite
===========================================================================
Implements verification tests for July 2026 Enhancement Research Report:
  - Section 2: Monotone Submodular Knapsack Optimization ((1 - 1/e) bound)
  - Section 3: Persistent Laplacian Spectral Filtration across scale parameters
  - Section 4: Order-Preserving Wasserstein (OPW) distance for reading order
  - Section 5: Information Bottleneck (IB) value function
  - Section 7: Hypergraph table representation for multi-cell header spans
'''
from __future__ import annotations

import numpy as np
import pytest

from src.engines.optimization.optimization_engine import OptimizationEngine
from src.engines.topology.topology_engine import TopologyEngine
from src.engines.graph_reading_order import order_preserving_wasserstein_distance
from src.engines.matrix.matrix_engine import HypergraphTableRepresentation, Hyperedge


def test_section_2_submodular_knapsack_optimization():
    '''Section 2: Monotone Submodular Knapsack Optimization ((1 - 1/e) bound).'''
    opt = OptimizationEngine()

    item_concepts = [
        {'revenue', 'growth'},
        {'growth', 'q3_financials'},
        {'table_data', 'revenue'},
        {'footnote', 'disclaimer'},
    ]
    concept_weights = {
        'revenue': 5.0,
        'growth': 4.0,
        'q3_financials': 6.0,
        'table_data': 7.0,
        'footnote': 1.0,
        'disclaimer': 1.0,
    }
    item_weights = [100, 150, 200, 50]
    capacity = 300

    res = opt.solve_submodular_knapsack(item_concepts, concept_weights, item_weights, capacity)
    assert res.solver_name == 'submodular_knapsack_greedy'
    assert res.total_tokens <= capacity
    assert res.total_value > 0.0


def test_section_3_persistent_laplacian_spectral_filtration():
    '''Section 3: Persistent Laplacian Spectral Filtration across distance scales.'''
    engine = TopologyEngine()
    positions = {
        'node_0': (0.1, 0.1),
        'node_1': (0.12, 0.12),
        'node_2': (0.5, 0.5),
        'node_3': (0.52, 0.52),
    }

    res_lap = engine.compute_persistent_laplacian(positions, tau_dist_scales=[0.05, 0.15, 0.6])
    assert 0.05 in res_lap
    assert 0.15 in res_lap
    assert 0.6 in res_lap
    assert len(res_lap[0.05]) == 4
    # At large scale 0.6, graph is connected so smallest eigenvalue is 0.0
    assert abs(res_lap[0.6][0]) < 1e-5


def test_section_4_order_preserving_wasserstein_distance():
    '''Section 4: Order-Preserving Wasserstein (OPW) distance for reading order.'''
    seq_gt = ['header', 'para1', 'table1', 'para2', 'footer']
    seq_perfect = ['header', 'para1', 'table1', 'para2', 'footer']
    seq_transposed = ['header', 'table1', 'para1', 'para2', 'footer']

    dist_perfect = order_preserving_wasserstein_distance(seq_perfect, seq_gt)
    dist_transposed = order_preserving_wasserstein_distance(seq_transposed, seq_gt)

    assert dist_perfect == 0.0
    assert dist_transposed > 0.0


def test_section_5_information_bottleneck_value_scoring():
    '''Section 5: Information Bottleneck value scoring I(Z;Y) - beta * I(X;Z).'''
    opt = OptimizationEngine()

    val = opt.calculate_information_bottleneck_value(relevance_score=0.9, compression_cost=0.4, beta=0.5)
    assert abs(val - 0.7) < 1e-5


def test_section_7_hypergraph_table_representation():
    '''Section 7: Hypergraph table representation for multi-cell header spans.'''
    htable = HypergraphTableRepresentation(table_id='tab_001', num_rows=5, num_cols=4)
    htable.add_merged_header(row=0, col_start=0, col_end=2, label='Q1-Q3 Consolidated')

    assert len(htable.hyperedges) == 1
    assert htable.hyperedges[0].edge_type == 'merged_header'
    assert len(htable.hyperedges[0].cell_coords) == 3
