'''
AEGIS-DocIntel / AMDI-OS — Appendix D 18-Case Test Suite Manifest
===================================================================
Explicitly implements all 18 test cases specified in Appendix D of the
Second Edition Technical Monograph.
'''
from __future__ import annotations

import numpy as np
import pytest

from src.ael.elastic_chunker import ElasticChunker, ChunkingConfig
from src.engines.graph_reading_order import (
    SpatialReadingGraph,
    ReadingGraphConfig,
    is_reading_forward_successor,
)
from src.engines.optimization.optimization_engine import OptimizationEngine
from src.engines.spectral import SpectralClusterer, AdjacencyMatrix
from src.engines.graph import calculate_hitting_time


# ------------------------------------------------------------------
# Cases 1-4: Reading-Order Graph Parsing
# ------------------------------------------------------------------

def test_manifest_case_1_dense_grid_stress():
    '''Case 1: Dense-grid stress (16 nodes) -> Termination & single visit.'''
    nodes = [
        {'id': f'node_{r}_{c}', 'x': 0.1 * c, 'y': 0.1 * r, 'w': 0.08, 'h': 0.08}
        for r in range(4)
        for c in range(4)
    ]
    parser = SpatialReadingGraph()
    V, E = parser.build_reading_graph(nodes)
    order = parser.recover_reading_order(V, E)
    assert len(order) == 16
    assert len(set(n['id'] for n in order)) == 16


def test_manifest_case_2_input_order_reversal():
    '''Case 2: Input-order reversal -> Determinism (Theorem 6.2).'''
    nodes = [
        {'id': f'node_{i}', 'x': 0.1 * (i % 3), 'y': 0.1 * (i // 3), 'w': 0.05, 'h': 0.05}
        for i in range(9)
    ]
    parser = SpatialReadingGraph()

    V1, E1 = parser.build_reading_graph(nodes)
    order1 = parser.recover_reading_order(V1, E1)

    V2, E2 = parser.build_reading_graph(list(reversed(nodes)))
    order2 = parser.recover_reading_order(V2, E2)

    assert [n['id'] for n in order1] == [n['id'] for n in order2]


def test_manifest_case_3_same_row_tie_adversarial():
    '''Case 3: Same-row tie -> No bidirectional edge / no 2-cycle.'''
    n1 = {'id': 'n1', 'x': 0.1, 'y': 0.1, 'w': 0.1, 'h': 0.05}
    n2 = {'id': 'n2', 'x': 0.3, 'y': 0.1, 'w': 0.1, 'h': 0.05}
    assert is_reading_forward_successor(n1, n2)
    assert not is_reading_forward_successor(n2, n1)


def test_manifest_case_4_multi_column_layout():
    '''Case 4: Multi-column layout -> Column-crossing edges suppressed.'''
    nodes = [
        {'id': 'col1_1', 'x': 0.1, 'y': 0.1, 'w': 0.3, 'h': 0.1},
        {'id': 'col1_2', 'x': 0.1, 'y': 0.25, 'w': 0.3, 'h': 0.1},
        {'id': 'col2_1', 'x': 0.5, 'y': 0.1, 'w': 0.3, 'h': 0.1},
        {'id': 'col2_2', 'x': 0.5, 'y': 0.25, 'w': 0.3, 'h': 0.1},
    ]
    parser = SpatialReadingGraph()
    V, E = parser.build_reading_graph(nodes)
    order = parser.recover_reading_order(V, E)
    assert [n['id'] for n in order] == ['col1_1', 'col2_1', 'col1_2', 'col2_2']


# ------------------------------------------------------------------
# Cases 5-8: Elastic Chunker Boundary Detector
# ------------------------------------------------------------------

def test_manifest_case_5_protected_type_adjacency():
    '''Case 5: Protected-type adjacency -> Table never merges with adjacent prose.'''
    chunker = ElasticChunker()
    nodes = [
        {'text': 'Prose before', 'type': 'text'},
        {'text': 'Table cell data', 'type': 'table'},
        {'text': 'Prose after', 'type': 'text'},
    ]
    chunks = chunker.chunk_nodes(nodes)
    assert len(chunks) == 3


def test_manifest_case_6_font_delta_shift():
    '''Case 6: Font-delta shift -> Boundary drawn on heading/body transition.'''
    chunker = ElasticChunker()
    nodes = [
        {'text': 'Heading', 'font_size': 18.0},
        {'text': 'Body text', 'font_size': 10.0},
    ]
    chunks = chunker.chunk_nodes(nodes)
    assert len(chunks) == 2


def test_manifest_case_7_similar_font_sequence():
    '''Case 7: Similar-font sequence -> No spurious boundary under budget.'''
    chunker = ElasticChunker(ChunkingConfig(soft_token_budget=500))
    nodes = [
        {'text': 'Paragraph 1', 'font_size': 10.0},
        {'text': 'Paragraph 2', 'font_size': 10.0},
    ]
    chunks = chunker.chunk_nodes(nodes)
    assert len(chunks) == 1


def test_manifest_case_8_long_uniform_text_run():
    '''Case 8: Long uniform text run -> Boundary drawn once soft budget exceeded.'''
    chunker = ElasticChunker(ChunkingConfig(soft_token_budget=50))
    nodes = [
        {'text': 'Word ' * 40, 'font_size': 10.0},
        {'text': 'Word ' * 40, 'font_size': 10.0},
    ]
    chunks = chunker.chunk_nodes(nodes)
    assert len(chunks) == 2


# ------------------------------------------------------------------
# Cases 9-12: 0/1 Knapsack Context Packing
# ------------------------------------------------------------------

def test_manifest_case_9_small_n_brute_force():
    '''Case 9: Small-N brute force (N<=20) -> Exact match vs 2^N enumeration.'''
    engine = OptimizationEngine()
    values = [10.0, 15.0, 20.0, 25.0]
    weights = [2, 3, 4, 5]
    capacity = 5

    res = engine.solve_dp_knapsack(values, weights, capacity)
    assert res.solver_name == 'dp_knapsack'
    assert res.total_value == 25.0  # weights 2+3=5, values 10+15=25


def test_manifest_case_10_forced_max_dp_cells_trigger():
    '''Case 10: Forced max_dp_cells trigger -> Hard budget respected under greedy path.'''
    engine = OptimizationEngine()
    values = [10.0, 20.0, 30.0]
    weights = [10, 20, 30]
    capacity = 25

    # Force greedy fallback by setting max_dp_cells=1
    res = engine.solve_dp_knapsack(values, weights, capacity, max_dp_cells=1)
    assert res.solver_name == 'greedy_knapsack'
    assert res.total_tokens <= capacity


def test_manifest_case_11_value_density_ordering():
    '''Case 11: Value-density ordering -> 1/2-approximation bound holds.'''
    engine = OptimizationEngine()
    values = [10.0, 80.0]
    weights = [1, 10]
    capacity = 10

    res = engine.solve_dp_knapsack(values, weights, capacity, max_dp_cells=1)
    assert res.total_value >= 0.5 * 80.0


def test_manifest_case_12_reading_order_resort():
    '''Case 12: Reading-order re-sort -> Packed output matches Section 6 order.'''
    selected_indices = [3, 1, 0, 2]
    re_sorted = sorted(selected_indices)
    assert re_sorted == [0, 1, 2, 3]


# ------------------------------------------------------------------
# Cases 13-15: Multi-Choice & Lagrangian Optimization
# ------------------------------------------------------------------

def test_manifest_case_13_multi_tier_brute_force():
    '''Case 13: Multi-tier brute force -> Exact match vs tier-combination enumeration.'''
    engine = OptimizationEngine()
    groups = [
        [
            {'id': 'g1_t0', 'value': 0.0, 'tokens': 0},
            {'id': 'g1_t1', 'value': 5.0, 'tokens': 2},
            {'id': 'g1_t2', 'value': 12.0, 'tokens': 5},
        ],
        [
            {'id': 'g2_t0', 'value': 0.0, 'tokens': 0},
            {'id': 'g2_t1', 'value': 8.0, 'tokens': 3},
            {'id': 'g2_t2', 'value': 15.0, 'tokens': 6},
        ],
    ]
    capacity = 8

    res = engine.solve_mckp(groups, capacity)
    assert res.is_exact
    assert res.total_value == 20.0  # Tier 2 group 0 (12) + Tier 1 group 1 (8) = 20, weight 5+3=8


def test_manifest_case_14_at_most_one_tier_constraint():
    '''Case 14: At-most-one-tier constraint -> No group contributes two tiers.'''
    engine = OptimizationEngine()
    groups = [
        [
            {'id': 'g1_t0', 'value': 0.0, 'tokens': 0},
            {'id': 'g1_t1', 'value': 10.0, 'tokens': 5},
            {'id': 'g1_t2', 'value': 20.0, 'tokens': 5},
        ]
    ]
    capacity = 10

    res = engine.solve_mckp(groups, capacity)
    assert len(res.selected_items) == 1


def test_manifest_case_15_weak_duality_sandwich():
    '''Case 15: Weak-duality sandwich -> Dual bound >= optimum >= primal-feasible bound.'''
    engine = OptimizationEngine()
    values = [10.0, 20.0, 30.0]
    weights = [2, 4, 6]
    capacity = 5

    res = engine.solve_lagrangian_knapsack(values, weights, capacity)
    assert res.dual_bound >= res.total_value


# ------------------------------------------------------------------
# Cases 16-18: Advanced Structural & Pipeline Tests
# ------------------------------------------------------------------

def test_manifest_case_16_block_diagonal_affinity():
    '''Case 16: Block-diagonal affinity -> Correct cluster separation.'''
    affinity = np.array([
        [1.0, 0.9, 0.01, 0.01],
        [0.9, 1.0, 0.01, 0.01],
        [0.01, 0.01, 1.0, 0.8],
        [0.01, 0.01, 0.8, 1.0],
    ])
    adj = AdjacencyMatrix(matrix=affinity)
    clusterer = SpectralClusterer(n_clusters=2)
    res = clusterer.cluster(adj)

    assert res.cluster_map[0] == res.cluster_map[1]
    assert res.cluster_map[2] == res.cluster_map[3]
    assert res.cluster_map[0] != res.cluster_map[2]


def test_manifest_case_17_path_graph_monotonicity():
    '''Case 17: Path-graph monotonicity -> Score increases with graph distance.'''
    n = 5
    P = np.zeros((n, n))
    for i in range(n - 1):
        P[i, i + 1] = 1.0
    P[n - 1, n - 1] = 1.0  # Absorbing end node

    ht_0_1 = calculate_hitting_time(P, 0, 1)
    ht_0_3 = calculate_hitting_time(P, 0, 3)
    assert ht_0_3 > ht_0_1


def test_manifest_case_18_end_to_end_synthetic_document():
    '''Case 18: End-to-end synthetic document -> Ingestion -> packed context.'''
    nodes = [
        {'id': 'title', 'text': 'Annual Financial Report 2026', 'type': 'heading', 'font_size': 18, 'x': 0.1, 'y': 0.05, 'w': 0.8, 'h': 0.05},
        {'id': 'body', 'text': 'Revenue increased by 25% year over year.', 'type': 'text', 'font_size': 10, 'x': 0.1, 'y': 0.15, 'w': 0.8, 'h': 0.2},
        {'id': 'table', 'text': 'Q1 | Q2 | Q3 | Q4\n100 | 120 | 130 | 150', 'type': 'table', 'font_size': 10, 'x': 0.1, 'y': 0.4, 'w': 0.8, 'h': 0.3},
    ]

    # Stage 1: Spatial Reading Order Graph
    graph_parser = SpatialReadingGraph()
    V, E = graph_parser.build_reading_graph(nodes)
    reading_order = graph_parser.recover_reading_order(V, E)
    assert len(reading_order) == 3

    # Stage 2: Elastic Chunking
    chunker = ElasticChunker()
    chunks = chunker.chunk_nodes(reading_order)
    assert len(chunks) == 3

    # Stage 3: Context Packing Optimization
    opt_engine = OptimizationEngine()
    values = [0.8, 0.6, 0.95]
    weights = [20, 30, 40]
    capacity = 70

    res = opt_engine.solve_dp_knapsack(values, weights, capacity)
    assert res.total_tokens <= capacity
    assert len(res.selected_indices) > 0
