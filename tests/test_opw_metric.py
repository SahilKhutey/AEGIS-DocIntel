"""
Unit tests for Order-Preserving Wasserstein (OPW) Reading-Order Metric (Task B-1).
"""

import pytest
from src.engines.graph_opw import OPWMetric, compute_opw_distance


def test_opw_identical_sequences():
    coords = [(0.1, 0.1), (0.1, 0.3), (0.1, 0.5)]
    dist = compute_opw_distance(coords, coords)
    assert dist == 0.0
    
    metric = OPWMetric()
    sim = metric.compute_similarity(coords, coords)
    assert sim == 1.0


def test_opw_reversed_sequences():
    coords_a = [(0.1, 0.1), (0.1, 0.3), (0.1, 0.5)]
    coords_b = [(0.1, 0.5), (0.1, 0.3), (0.1, 0.1)]
    
    dist_same = compute_opw_distance(coords_a, coords_a)
    dist_rev = compute_opw_distance(coords_a, coords_b)
    
    assert dist_rev > dist_same


def test_opw_empty_sequences():
    dist = compute_opw_distance([], [])
    assert dist == 0.0

    dist_one_empty = compute_opw_distance([(0.1, 0.1)], [])
    assert dist_one_empty > 0.0


def test_opw_similarity_range():
    metric = OPWMetric()
    coords_a = [(0.1, 0.1), (0.2, 0.2)]
    coords_b = [(0.9, 0.9), (0.8, 0.8)]
    
    sim = metric.compute_similarity(coords_a, coords_b)
    assert 0.0 <= sim <= 1.0
