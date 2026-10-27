"""tests/test_mvp2_rank_fusion.py
================================
MVP 2 regression tests for the rank-fusion implementation.
"""

from __future__ import annotations

import math
import pytest
from src.engines.retrieval.ranker import HybridRanker


def test_rrf_promotes_consensus_across_ranked_lists() -> None:
    ranker = HybridRanker(
        method="rrf",
        rrf_k=60,
        weights={"lexical": 1.0, "semantic": 1.0},
    )
    ranking = ranker.fuse(
        {
            "lexical": [
                ("chunk-a", 10.0),
                ("chunk-b", 9.0),
                ("chunk-c", 8.0),
            ],
            "semantic": [
                ("chunk-b", 0.95),
                ("chunk-a", 0.90),
                ("chunk-d", 0.80),
            ],
        },
        top_k=4,
    )
    ids = [item.doc_id for item in ranking.ranked_docs]
    # A and B appear near the top in both methods.
    assert set(ids[:2]) == {"chunk-a", "chunk-b"}
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("top_k", [0, -1, True, False])
def test_invalid_top_k_in_ranker(top_k: int) -> None:
    ranker = HybridRanker(method="rrf")
    with pytest.raises(ValueError):
        ranker.fuse({"s1": [("doc1", 1.0)]}, top_k=top_k)


def test_duplicate_ids_in_single_source_are_deduplicated() -> None:
    ranker = HybridRanker(method="rrf", rrf_k=60)
    ranking = ranker.fuse(
        {
            "s1": [("doc1", 10.0), ("doc1", 5.0), ("doc2", 8.0)],
        }
    )
    ids = [d.doc_id for d in ranking.ranked_docs]
    assert ids == ["doc1", "doc2"]
    assert ranking.num_docs == 2


def test_non_finite_scores_rejected() -> None:
    ranker = HybridRanker(method="rrf")
    with pytest.raises(ValueError, match="Non-finite score encountered"):
        ranker.fuse({"s1": [("doc1", float("nan"))]})

    with pytest.raises(ValueError, match="Non-finite score encountered"):
        ranker.fuse({"s1": [("doc1", float("inf"))]})


def test_negative_weights_rejected() -> None:
    ranker = HybridRanker(method="rrf")
    with pytest.raises(ValueError, match="Weights must be non-negative"):
        ranker.fuse(
            {"s1": [("doc1", 1.0)], "s2": [("doc2", 1.0)]},
            weights={"s1": -1.0, "s2": 1.0},
        )


def test_zero_total_weights_rejected() -> None:
    ranker = HybridRanker(method="rrf")
    with pytest.raises(ValueError, match="Sum of weights must be positive"):
        ranker.fuse(
            {"s1": [("doc1", 1.0)]},
            weights={"s1": 0.0},
        )


def test_deterministic_tie_breaking() -> None:
    ranker = HybridRanker(method="rrf", rrf_k=60)
    # Both doc-z and doc-a have identical scores and ranks in s1
    # Tied doc_ids should break deterministically by doc_id ascending
    ranking = ranker.fuse(
        {
            "s1": [("doc-z", 10.0)],
            "s2": [("doc-a", 10.0)],
        }
    )
    ids = [d.doc_id for d in ranking.ranked_docs]
    assert ids == ["doc-a", "doc-z"]


def test_empty_candidate_source_results() -> None:
    ranker = HybridRanker(method="rrf")
    ranking = ranker.fuse({"s1": [], "s2": []})
    assert ranking.num_docs == 0
    assert ranking.ranked_docs == []
