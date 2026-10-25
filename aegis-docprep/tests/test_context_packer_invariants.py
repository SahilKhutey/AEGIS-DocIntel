"""
tests/test_context_packer_invariants.py
========================================
P2.2 Mathematical Correctness, Token Accounting & Approximation Invariants:
1. Hard token budget calculation and prompt limit enforcement.
2. Boundary input validation (types, costs, dimensions, non-negativity).
3. Non-negative cosine similarity transformations (clipped vs affine).
4. Zero-norm and malformed embedding resilience.
5. Deterministic tie-breaking under equal marginal utility.
6. Empirical knapsack approximation bound comparison against exhaustive search (Theorem 9.1).
"""
from __future__ import annotations

import itertools
import math
import numpy as np
import pytest

from aegis_docprep.context_packer import (
    ContextChunk,
    SubmodularKnapsackPacker,
    calculate_available_context_budget,
    validate_packing_inputs,
)


def test_calculate_available_context_budget_invariants():
    """P2.2: Hard context budget accounts for instructions, query, reserved output, and overhead."""
    # Context window: 4096, instructions: 300, query: 50, reserved output: 512, overhead: 34
    # Expected: 4096 - 300 - 50 - 512 - 34 = 3200
    b = calculate_available_context_budget(
        context_window=4096,
        instructions_tokens=300,
        query_tokens=50,
        reserved_output_tokens=512,
        overhead_tokens=34,
    )
    assert b == 3200

    # Oversized overhead returns 0 (clamped non-negative)
    b_zero = calculate_available_context_budget(
        context_window=1000,
        instructions_tokens=800,
        query_tokens=300,
        reserved_output_tokens=200,
    )
    assert b_zero == 0

    # Invalid input validations
    with pytest.raises(ValueError, match="context_window must be a positive integer"):
        calculate_available_context_budget(0, 10, 10, 10)
    with pytest.raises(ValueError, match="query_tokens must be a non-negative integer"):
        calculate_available_context_budget(1000, 10, -5, 10)


def test_validate_packing_inputs_boundary_cases():
    """P2.2: Boundary validation strictly checks types, dimensions, and finite values."""
    embs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    costs = [10, 15]

    # Valid call succeeds
    validate_packing_inputs(0.6, 0.4, 20, embs, costs)

    # Invalid alpha / beta
    with pytest.raises(ValueError, match="alpha must be finite and non-negative"):
        validate_packing_inputs(-0.1, 0.4, 20, embs, costs)
    with pytest.raises(ValueError, match="alpha must be finite and non-negative"):
        validate_packing_inputs(float("nan"), 0.4, 20, embs, costs)
    with pytest.raises(ValueError, match="beta must be finite and non-negative"):
        validate_packing_inputs(0.6, float("inf"), 20, embs, costs)

    # Invalid budget
    with pytest.raises(ValueError, match="budget must be a non-negative integer"):
        validate_packing_inputs(0.6, 0.4, -5, embs, costs)
    with pytest.raises(ValueError, match="budget must be a non-negative integer"):
        validate_packing_inputs(0.6, 0.4, True, embs, costs)  # bool is not allowed

    # Cost validations
    with pytest.raises(ValueError, match="All item costs must be positive integers"):
        validate_packing_inputs(0.6, 0.4, 20, embs, [10, 0])  # zero cost disallowed
    with pytest.raises(ValueError, match="All item costs must be positive integers"):
        validate_packing_inputs(0.6, 0.4, 20, embs, [10, -2])  # negative cost disallowed
    with pytest.raises(ValueError, match="Each item must have one cost"):
        validate_packing_inputs(0.6, 0.4, 20, embs, [10])  # length mismatch

    # Embedding validations
    with pytest.raises(ValueError, match="Embeddings must be a two-dimensional array"):
        validate_packing_inputs(0.6, 0.4, 20, np.array([1.0, 2.0]), [10])
    with pytest.raises(ValueError, match="Embeddings must contain only finite values"):
        validate_packing_inputs(0.6, 0.4, 20, np.array([[1.0, np.nan], [0.0, 1.0]]), costs)


def test_zero_budget_and_empty_inputs():
    """P2.2: Zero budget or empty candidates return safe empty results."""
    packer = SubmodularKnapsackPacker()
    res1 = packer.pack_context([], max_budget=100)
    assert res1.selected_chunks == []
    assert res1.total_tokens == 0
    assert res1.total_score == 0.0

    chunk = ContextChunk(chunk_id="c1", text="Sample", relevance_score=0.9, token_cost=5)
    res2 = packer.pack_context([chunk], max_budget=0)
    assert res2.selected_chunks == []
    assert res2.total_tokens == 0


def test_oversized_item_cannot_be_selected():
    """P2.2: An item with cost > budget can never be selected even if relevance is 1.0."""
    packer = SubmodularKnapsackPacker()
    c_huge = ContextChunk(chunk_id="huge", text="Massive high relevance", relevance_score=1.0, token_cost=50)
    c_small = ContextChunk(chunk_id="small", text="Modest relevance", relevance_score=0.5, token_cost=10)

    res = packer.pack_context([c_huge, c_small], max_budget=20)
    assert len(res.selected_chunks) == 1
    assert res.selected_chunks[0].chunk_id == "small"
    assert res.total_tokens == 10


def test_similarity_metric_clipped_vs_affine():
    """P2.2: Clipped cosine similarity preserves 0 for orthogonal/negative vectors; affine maps to [0, 1]."""
    packer_clipped = SubmodularKnapsackPacker(similarity_metric="clipped_cosine")
    packer_affine = SubmodularKnapsackPacker(similarity_metric="affine_cosine")

    # Antipodal vectors: cos = -1.0
    v1 = np.array([1.0, 0.0])
    v2 = np.array([-1.0, 0.0])
    assert packer_clipped._cosine_similarity(v1, v2) == 0.0
    assert packer_affine._cosine_similarity(v1, v2) == 0.0

    # Orthogonal vectors: cos = 0.0
    v3 = np.array([0.0, 1.0])
    assert packer_clipped._cosine_similarity(v1, v3) == 0.0
    assert abs(packer_affine._cosine_similarity(v1, v3) - 0.5) < 1e-6

    # Zero-norm vector
    v_zero = np.array([0.0, 0.0])
    assert packer_clipped._cosine_similarity(v1, v_zero) == 0.0
    assert packer_affine._cosine_similarity(v1, v_zero) == 0.0


def test_deterministic_tie_breaking():
    """P2.2: Identical scores and costs break ties deterministically on chunk_id."""
    packer = SubmodularKnapsackPacker()
    # Identical relevance and cost, different chunk_ids
    c_b = ContextChunk(chunk_id="b_item", text="Same content", relevance_score=0.8, token_cost=5)
    c_a = ContextChunk(chunk_id="a_item", text="Same content", relevance_score=0.8, token_cost=5)

    # In either candidate input order, the tie-breaking must yield deterministic output
    res1 = packer.pack_context([c_b, c_a], max_budget=5)
    res2 = packer.pack_context([c_a, c_b], max_budget=5)

    assert len(res1.selected_chunks) == 1
    assert len(res2.selected_chunks) == 1
    assert res1.selected_chunks[0].chunk_id == "a_item"
    assert res2.selected_chunks[0].chunk_id == "a_item"


def test_submodular_knapsack_guarantee_against_exhaustive_search():
    """
    P2.2 Theorem 9.1: Compare greedy + best-single-item against exhaustive knapsack search S*.
    Verifies: F(S_greedy) >= ((1 - 1/e) / 2) * F(S*) ~= 0.316 * F(S*).
    """
    dim = 4
    np.random.seed(42)

    # Generate 8 synthetic candidate chunks
    chunks: list[ContextChunk] = []
    costs = [3, 4, 2, 5, 3, 6, 2, 4]
    rels = [0.9, 0.7, 0.4, 0.85, 0.5, 0.95, 0.3, 0.6]

    for i in range(8):
        vec = np.random.randn(dim).astype(np.float32)
        chunks.append(
            ContextChunk(
                chunk_id=f"chk_{i}",
                text=f"Candidate document element {i}",
                relevance_score=rels[i],
                token_cost=costs[i],
                embedding=vec,
            )
        )

    budget = 10
    alpha = 0.6
    beta = 0.4
    packer = SubmodularKnapsackPacker(alpha=alpha, beta=beta)

    # 1. Run algorithm
    alg_result = packer.pack_context(chunks, max_budget=budget)
    f_alg = alg_result.total_score
    assert alg_result.total_tokens <= budget

    # 2. Run exhaustive search over all 2^8 = 256 subsets
    n = len(chunks)
    sim_mat = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            sim_mat[i, j] = packer._cosine_similarity(chunks[i].embedding, chunks[j].embedding)

    def eval_subset(subset_indices: tuple[int, ...]) -> float:
        if not subset_indices:
            return 0.0
        cov = sum(max(sim_mat[i, s] for s in subset_indices) for i in range(n)) / float(n)
        rel = sum(chunks[s].relevance_score for s in subset_indices)
        return alpha * cov + beta * rel

    opt_score = -1.0
    best_subset = ()

    for r in range(1, n + 1):
        for subset in itertools.combinations(range(n), r):
            tot_cost = sum(chunks[i].token_cost for i in subset)
            if tot_cost <= budget:
                score = eval_subset(subset)
                if score > opt_score:
                    opt_score = score
                    best_subset = subset

    assert opt_score > 0.0

    # 3. Check theoretical bound: (1 - 1/e) / 2 ~= 0.31606
    theoretical_bound = (1.0 - 1.0 / math.e) / 2.0
    ratio = f_alg / opt_score

    assert ratio >= theoretical_bound, f"Approximation guarantee violated: ratio {ratio:.4f} < {theoretical_bound:.4f}"
    # In practice greedy density achieves > 75% of optimum
    assert ratio >= 0.75
