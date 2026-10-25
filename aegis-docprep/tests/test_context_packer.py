"""
Tests for aegis_docprep.context_packer.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from aegis_docprep.context_packer import (
    ContextChunk,
    SubmodularKnapsackPacker,
    SubmodularPackingResult,
)


def test_packer_prefers_high_relevance_within_budget():
    chunks = [
        ContextChunk(chunk_id="c1", text="Revenue grew 12% year over year.", relevance_score=0.9, token_cost=8),
        ContextChunk(chunk_id="c2", text="The cafeteria menu changed on Tuesday.", relevance_score=0.1, token_cost=8),
        ContextChunk(chunk_id="c3", text="Net income doubled due to cost cuts.", relevance_score=0.85, token_cost=8),
    ]
    result = SubmodularKnapsackPacker().pack_context(chunks, max_budget=16)
    selected_ids = {c.chunk_id for c in result.selected_chunks}
    assert selected_ids == {"c1", "c3"}  # Exact verified behavior
    assert result.total_tokens <= 16


def test_packer_respects_budget_strictly():
    chunks = [ContextChunk(chunk_id=f"c{i}", text="x", relevance_score=1.0, token_cost=100) for i in range(5)]
    result = SubmodularKnapsackPacker().pack_context(chunks, max_budget=250)
    assert result.total_tokens <= 250
    assert len(result.selected_chunks) == 2


def test_submodular_packer_respects_embedding_similarity():
    packer = SubmodularKnapsackPacker(alpha=0.8, beta=0.2)
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.99, 0.01, 0.0])  # Near duplicate of v1
    v3 = np.array([0.0, 1.0, 0.0])    # Diverse vs v1

    chunks = [
        ContextChunk(chunk_id="c1", text="Topic A", relevance_score=0.8, token_cost=100, embedding=v1),
        ContextChunk(chunk_id="c2", text="Topic A dup", relevance_score=0.85, token_cost=100, embedding=v2),
        ContextChunk(chunk_id="c3", text="Topic B diverse", relevance_score=0.75, token_cost=100, embedding=v3),
    ]

    res = packer.pack_context(chunks, max_budget=200)
    selected_ids = {c.chunk_id for c in res.selected_chunks}
    assert ("c1" in selected_ids or "c2" in selected_ids)
    assert "c3" in selected_ids  # Diverse item selected over redundant near-duplicate


def test_submodular_packer_empty_input():
    packer = SubmodularKnapsackPacker()
    res = packer.pack_context([], max_budget=1000)
    assert res.total_tokens == 0
    assert len(res.selected_chunks) == 0


def test_convenience_alias_pack_and_token_count():
    packer = SubmodularKnapsackPacker()
    chunks = [
        ContextChunk(chunk_id="c1", text="Alpha", relevance_score=0.9, token_count=5),
        ContextChunk(chunk_id="c2", text="Beta", relevance_score=0.5, token_count=5),
    ]
    # Verify token_count property works as alias for token_cost
    assert chunks[0].token_cost == 5
    assert chunks[0].token_count == 5

    res = packer.pack(chunks, max_budget=5)
    assert len(res.selected_chunks) == 1
    assert res.selected_chunks[0].chunk_id == "c1"


# ============================================================================
# Theorem 9.1 & Submodular Monotonicity Property Tests
# ============================================================================

@given(
    st.lists(
        st.tuples(
            st.floats(min_value=0.1, max_value=1.0),
            st.integers(min_value=1, max_value=50),
        ),
        min_size=2,
        max_size=15,
    ),
    st.integers(min_value=10, max_value=200),
)
@settings(max_examples=40, deadline=None)
def test_theorem_9_1_budget_adherence_and_non_negativity(item_tuples, budget):
    """
    Property-based verification of SubmodularKnapsackPacker:
    - Never exceeds max_budget
    - Total score is strictly non-negative
    - Monotone accumulation: selected chunks all fit within budget
    """
    chunks = [
        ContextChunk(
            chunk_id=f"chunk_{i}",
            text=f"Sample text content for chunk {i}",
            relevance_score=score,
            token_cost=cost,
        )
        for i, (score, cost) in enumerate(item_tuples)
    ]
    packer = SubmodularKnapsackPacker(alpha=0.5, beta=0.5)
    result = packer.pack_context(chunks, max_budget=budget)

    assert result.total_tokens <= budget
    assert result.total_score >= 0.0
    assert len(result.selected_chunks) <= len(chunks)
    actual_tokens = sum(c.token_cost for c in result.selected_chunks)
    assert result.total_tokens == actual_tokens


def test_negative_cosine_similarity_clamped_to_zero():
    """
    Facility location submodular coverage requires non-negative similarity.
    Opposite vectors (cosine = -1.0) must be clamped to 0.0 to prevent
    violating monotonicity and non-negativity.
    """
    packer = SubmodularKnapsackPacker(alpha=1.0, beta=0.0)
    v1 = np.array([1.0, 0.0])
    v2 = np.array([-1.0, 0.0])  # Opposite direction, cosine = -1.0

    raw_sim = packer._cosine_similarity(v1, v2)
    assert raw_sim == 0.0  # Clamped to 0.0, never negative

    chunks = [
        ContextChunk(chunk_id="c1", text="Opposite A", relevance_score=0.5, token_cost=10, embedding=v1),
        ContextChunk(chunk_id="c2", text="Opposite B", relevance_score=0.5, token_cost=10, embedding=v2),
    ]
    res = packer.pack_context(chunks, max_budget=20)
    assert res.coverage_score >= 0.0
    assert res.total_score >= 0.0


def test_packer_input_validation():
    with pytest.raises(ValueError, match="alpha must be finite and non-negative"):
        SubmodularKnapsackPacker(alpha=-0.1, beta=0.5)

    with pytest.raises(ValueError, match="beta must be finite and non-negative"):
        SubmodularKnapsackPacker(alpha=0.5, beta=-0.1)

    packer = SubmodularKnapsackPacker()
    with pytest.raises(ValueError, match="max_budget must be non-negative"):
        packer.pack_context([], max_budget=-5)

    with pytest.raises(ValueError, match="token_cost must be non-negative"):
        packer.pack_context([ContextChunk(chunk_id="c1", text="t", relevance_score=0.5, token_cost=-1)], max_budget=10)

    with pytest.raises(ValueError, match="relevance_score must be non-negative"):
        packer.pack_context([ContextChunk(chunk_id="c1", text="t", relevance_score=-0.5, token_cost=5)], max_budget=10)
