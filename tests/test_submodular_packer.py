"""
Unit tests for Submodular Knapsack Context Packer (Task C-1).
"""

import numpy as np
import pytest
from src.engines.retrieval.submodular_packer import (
    SubmodularKnapsackPacker, ContextChunk, SubmodularPackingResult
)


def test_submodular_packer_basic_budget():
    packer = SubmodularKnapsackPacker()
    chunks = [
        ContextChunk(chunk_id="c1", text="Alpha report overview", relevance_score=0.9, token_cost=100),
        ContextChunk(chunk_id="c2", text="Beta financial figures", relevance_score=0.8, token_cost=150),
        ContextChunk(chunk_id="c3", text="Gamma security compliance", relevance_score=0.7, token_cost=200),
    ]

    res = packer.pack_context(chunks, max_budget=250)

    assert res.total_tokens <= 250
    assert len(res.selected_chunks) > 0
    assert res.total_score > 0.0


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

    selected_ids = [c.chunk_id for c in res.selected_chunks]
    assert "c1" in selected_ids or "c2" in selected_ids
    assert "c3" in selected_ids  # Diverse item preferred over near-duplicate


def test_submodular_packer_empty_input():
    packer = SubmodularKnapsackPacker()
    res = packer.pack_context([], max_budget=1000)
    assert res.total_tokens == 0
    assert len(res.selected_chunks) == 0
