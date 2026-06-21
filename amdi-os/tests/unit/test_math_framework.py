"""
AEGIS-AMDI-OS — Math Framework Unit Tests
==========================================
Tests coordinate, entropy, hierarchical, density, routing, and optimization engines.
"""
from __future__ import annotations

import pytest
import numpy as np

# Core Engines
from src.engines.coordinate.coordinate_engine import CoordinateEngine, NormalizedCoordinate, BoundingBox, ElementType
from src.engines.entropy.entropy_engine import EntropyEngine, EntropyProfile
from src.engines.hierarchy.hierarchical_engine import HierarchicalEngine, HierarchicalCoordinate
from src.engines.density.density_engine import DensityEngine, DensityMetric
from src.engines.dynamic_router.dynamic_router import DynamicRouter
from src.engines.optimization.optimization_engine import OptimizationEngine


def test_coordinate_engine():
    # Setup test coordinates
    box_a = BoundingBox(x0=100.0, y0=200.0, x1=300.0, y1=250.0)
    box_b = BoundingBox(x0=150.0, y0=200.0, x1=350.0, y1=250.0)
    
    # Scale width=1000, height=1000
    coord_a = CoordinateEngine.normalize(box_a, 1000.0, 1000.0, page=1, theta=0.0, content="Block Alpha")
    coord_b = CoordinateEngine.normalize(box_b, 1000.0, 1000.0, page=1, theta=0.0, content="Block Beta")

    # Scale invariance test
    assert coord_a.x == pytest.approx(0.1)
    assert coord_a.y == pytest.approx(0.2)
    assert coord_a.w == pytest.approx(0.2)
    assert coord_a.h == pytest.approx(0.05)

    # Distance calculation (same page)
    # distance = sqrt((0.1-0.15)^2 + (0.2-0.2)^2) = sqrt(0.0025 + 0) = 0.05
    dist = CoordinateEngine.distance(coord_a, coord_b)
    assert dist == pytest.approx(0.05)

    # Cross-page distance (should apply 1.5 page penalty)
    coord_c = CoordinateEngine.normalize(box_b, 1000.0, 1000.0, page=2)
    dist_cross = CoordinateEngine.distance(coord_a, coord_c)
    assert dist_cross == pytest.approx(0.05 + 1.5)

    # Alignment scores
    h_align = CoordinateEngine.alignment_horizontal(coord_a, coord_b)
    assert h_align == pytest.approx(1.0 - 0.05)
    
    v_align = CoordinateEngine.alignment_vertical(coord_a, coord_b)
    assert v_align == pytest.approx(1.0)

    align = CoordinateEngine.alignment(coord_a, coord_b)
    assert align == pytest.approx(0.975)

    # Area Ratio
    assert CoordinateEngine.area_importance(coord_a) == pytest.approx(0.01)

    # Reading order sorting
    coord_first = CoordinateEngine.normalize(BoundingBox(0.0, 0.0, 1.0, 1.0), 10.0, 10.0, 1) # y=0.0, x=0.0
    coord_second = CoordinateEngine.normalize(BoundingBox(5.0, 0.0, 6.0, 1.0), 10.0, 10.0, 1) # y=0.0, x=0.5
    coord_third = CoordinateEngine.normalize(BoundingBox(0.0, 5.0, 1.0, 6.0), 10.0, 10.0, 1) # y=0.5, x=0.0
    
    sorted_res = CoordinateEngine.reading_order([coord_third, coord_first, coord_second])
    assert sorted_res[0] == coord_first
    assert sorted_res[1] == coord_second
    assert sorted_res[2] == coord_third


def test_entropy_engine():
    entropy_engine = EntropyEngine(threshold=1.0)
    
    # Highly repetitive vs diverse text
    rep_text = "test test test test test test test"
    diverse_text = "The quick brown fox jumps over a lazy dog"
    
    h_rep = entropy_engine.shannon_entropy(rep_text)
    h_div = entropy_engine.shannon_entropy(diverse_text)
    
    assert h_rep == pytest.approx(0.0) # only one unique token, log2(1) = 0
    assert h_div > 3.0 # many unique tokens
    
    # Check max entropy
    assert entropy_engine.max_entropy(rep_text) == 0.0
    assert entropy_engine.max_entropy(diverse_text) > 3.0

    # Profile sorting & filtering
    coord_rep = NormalizedCoordinate(0.0, 0.0, 0.5, 0.5, 1, 0.0, ElementType.TEXT, rep_text, "rep")
    coord_div = NormalizedCoordinate(0.0, 0.0, 0.5, 0.5, 1, 0.0, ElementType.TEXT, diverse_text, "div")
    
    profiles = entropy_engine.profile([coord_rep, coord_div])
    assert len(profiles) == 2
    
    # Diverse text should be higher priority due to larger entropy density
    assert profiles[0].element_id == "div"
    assert profiles[1].element_id == "rep"
    
    # Filtering
    inf, non_inf = entropy_engine.filter_informative([coord_rep, coord_div], profiles)
    assert len(inf) == 1
    assert inf[0].element_id == "div"
    assert len(non_inf) == 1
    assert non_inf[0].element_id == "rep"


def test_hierarchical_engine():
    hier_engine = HierarchicalEngine()
    
    coord_1 = NormalizedCoordinate(0.0, 0.0, 0.5, 0.5, p=1, theta=0.0, type=ElementType.TEXT, content="Hello World", element_id="b1")
    coord_2 = NormalizedCoordinate(0.0, 0.0, 0.5, 0.5, p=1, theta=0.0, type=ElementType.TEXT, content="Mathematical Document Intelligence", element_id="b2")
    
    hier_engine.build_from_coords([coord_1, coord_2], {"b1": "intro", "b2": "method"})
    
    # Statistics
    stats = hier_engine.statistics()
    assert stats["pages"] == 1
    assert stats["sections"] == 2
    assert stats["blocks"] == 2
    assert stats["tokens"] == 5 # "Hello", "World", "Mathematical", "Document", "Intelligence"

    # Querying
    found_tokens = hier_engine.query(page=1, section=1) # "method" section
    assert len([n for n in found_tokens if n.level == 4]) == 3 # 3 tokens

    # Path reconstruction
    coord_to_check = HierarchicalCoordinate(1, 0, 0, 0, 1) # Page 1, Section 0, Block 0, Line 0, Token 1 ("World")
    path = hier_engine.get_path(coord_to_check)
    
    assert len(path) == 5
    assert path[0].content == "Page 1"
    assert path[1].content == "intro"
    assert path[4].content == "World"


def test_density_engine():
    density_engine = DensityEngine()
    
    coord = NormalizedCoordinate(x=0.1, y=0.2, w=0.2, h=0.2, p=1, theta=0.0, type=ElementType.TEXT, content="Information density analysis.", element_id="d1")
    area = coord.area_ratio() # 0.04
    
    # Token Density = 3 words / 0.04 = 75
    assert density_engine.token_density("Information density analysis.", area) == pytest.approx(75.0)

    # Quadrant mapping
    assert density_engine._quadrant(coord) == "TL"
    
    coord_br = NormalizedCoordinate(x=0.7, y=0.8, w=0.1, h=0.1, p=1, theta=0.0, type=ElementType.TEXT, content="Lower right quadrant.", element_id="d2")
    assert density_engine._quadrant(coord_br) == "BR"


def test_dynamic_router():
    router = DynamicRouter()
    
    # Heuristics checks
    w_num, type_num = router.predict("What is the average sum and total value?")
    assert type_num == "aggregate"
    # w_num is 9-dimensional and sums to 1
    assert len(w_num) == 9
    assert pytest.approx(sum(w_num)) == 1.0

    w_sem, type_sem = router.predict("Explain the main concept of the document.")
    assert type_sem == "semantic"
    assert pytest.approx(sum(w_sem)) == 1.0


def test_optimization_engine():
    opt_engine = OptimizationEngine()
    
    # Knapsack problem: items with values and token counts
    values = [0.8, 0.6, 0.4, 0.35]
    tokens = [100, 200, 150, 100]
    budget = 300
    
    # Greedy Solver
    # values/tokens ratio:
    # 0.8/100 = 0.008   (idx 0)
    # 0.6/200 = 0.003   (idx 1)
    # 0.4/150 = 0.00266 (idx 2)
    # 0.35/100 = 0.0035 (idx 3)
    # Greedy order: idx 0 (wt 100), idx 3 (wt 100), idx 1 (wt 200 - over limit)
    res_greedy = opt_engine.solve_greedy_knapsack(values, tokens, budget)
    assert set(res_greedy.selected_indices) == {0, 3}
    assert res_greedy.total_value == pytest.approx(1.15)

    # DP Solver
    # Optimal: idx 0 (wt 100, val 0.8) and idx 1 (wt 200, val 0.6) -> total wt 300, total val 1.4
    res_dp = opt_engine.solve_dp_knapsack(values, tokens, budget)
    assert set(res_dp.selected_indices) == {0, 1}
    assert res_dp.total_value == pytest.approx(1.4)
    
    # Verify greedy is indeed a 1/2 approximation (1.1 >= 1.4 / 2)
    assert res_greedy.total_value >= res_dp.total_value / 2.0

    # Weight mixing convergence
    scores_matrix = np.array([
        [0.8, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1],
        [0.7, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1]
    ], dtype=np.float32)
    target = np.array([0.79, 0.69], dtype=np.float32)
    
    w_opt = opt_engine.optimize_weights_mixing(scores_matrix, target, lr=0.1, iterations=100)
    assert pytest.approx(sum(w_opt)) == 1.0
    # W_0 should be dominant since target is close to column 0 scores
    assert w_opt[0] > 0.5
