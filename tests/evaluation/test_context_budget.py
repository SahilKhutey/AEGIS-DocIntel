"""
tests/evaluation/test_context_budget.py
=======================================
Phase 3.4 Evaluation Quality Suite — Context Budget and Packing:
Verifies context window calculations and submodular knapsack packing constraints,
ensuring strict adherence to token limits and mathematical approximation bounds.
"""
from __future__ import annotations

import pytest

from src.engines.retrieval.submodular_packer import (
    ContextChunk,
    SubmodularKnapsackPacker,
    calculate_available_context_budget,
)


def test_calculate_available_context_budget_arithmetic():
    """Verify exact formula: B = W - T_inst - T_query - T_reserved_output - T_overhead."""
    budget = calculate_available_context_budget(
        context_window=4096,
        instructions_tokens=500,
        query_tokens=100,
        reserved_output_tokens=500,
        overhead_tokens=50,
    )
    assert budget == 2946

    # Test with default overhead_tokens = 0
    budget_no_overhead = calculate_available_context_budget(
        context_window=8192,
        instructions_tokens=1000,
        query_tokens=200,
        reserved_output_tokens=1000,
    )
    assert budget_no_overhead == 5992


def test_packer_strictly_respects_token_budget():
    """Packer must never exceed max_budget under any chunk combination."""
    packer = SubmodularKnapsackPacker()
    chunks = [
        ContextChunk(chunk_id=f"chunk_{i}", text=f"Evidence text {i}", relevance_score=0.1 * i, token_cost=150)
        for i in range(1, 10)
    ]
    budget = 400
    res = packer.pack_context(chunks, max_budget=budget)

    assert res.total_tokens <= budget
    assert sum(c.token_cost for c in res.selected_chunks) == res.total_tokens
    assert len(res.selected_chunks) == 2  # 150 + 150 = 300 <= 400


def test_packer_empty_input():
    """Packer handles empty candidate list cleanly without errors."""
    packer = SubmodularKnapsackPacker()
    res = packer.pack_context([], max_budget=1000)
    assert res.total_tokens == 0
    assert len(res.selected_chunks) == 0
    assert res.total_score == 0.0


def test_packer_chunks_exceeding_budget_are_skipped():
    """Chunks with token cost strictly greater than max_budget are ignored."""
    packer = SubmodularKnapsackPacker()
    chunks = [
        ContextChunk(chunk_id="oversized_1", text="Too big", relevance_score=0.99, token_cost=1200),
        ContextChunk(chunk_id="oversized_2", text="Also too big", relevance_score=0.95, token_cost=1500),
        ContextChunk(chunk_id="fitting", text="Fits well", relevance_score=0.80, token_cost=400),
    ]
    res = packer.pack_context(chunks, max_budget=500)

    assert res.total_tokens == 400
    assert len(res.selected_chunks) == 1
    assert res.selected_chunks[0].chunk_id == "fitting"


def test_packer_guarantee_single_item_fallback():
    """
    Submodular knapsack packer must guarantee at least (1 - 1/e) / 2 ~= 0.316
    of the optimum value on density-adversarial knapsack instances.
    """
    budget = 100
    # Adversarial instance where density greedy would prefer cheap over big
    cheap = ContextChunk(chunk_id="cheap", text="low value", relevance_score=0.02, token_cost=1)
    big = ContextChunk(chunk_id="big", text="high value", relevance_score=1.00, token_cost=budget)

    packer = SubmodularKnapsackPacker(alpha=0.0, beta=1.0)
    res = packer.pack_context([cheap, big], max_budget=budget)

    assert res.total_tokens <= budget
    total_val = sum(c.relevance_score for c in res.selected_chunks)
    optimal_val = 1.00
    assert total_val >= 0.316 * optimal_val
    assert "big" in [c.chunk_id for c in res.selected_chunks]
