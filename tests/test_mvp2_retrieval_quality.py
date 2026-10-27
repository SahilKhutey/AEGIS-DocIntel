"""tests/test_mvp2_retrieval_quality.py
=====================================
Small deterministic tests for retrieval evaluation mathematics:
- Reciprocal Rank (RR / MRR)
- Recall@k
- Empty / unanswerable conventions
"""

from __future__ import annotations

import pytest


def reciprocal_rank(ranked_ids: list[str], relevant_ids: set[str]) -> float:
    for rank, item_id in enumerate(ranked_ids, start=1):
        if item_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def recall_at_k(
    ranked_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    if k < 1:
        raise ValueError("k must be >= 1")
    if not relevant_ids:
        return 1.0 if not ranked_ids[:k] else 0.0
    return len(set(ranked_ids[:k]) & relevant_ids) / len(relevant_ids)


def test_first_relevant_result_at_rank_one() -> None:
    assert reciprocal_rank(["relevant", "other"], {"relevant"}) == 1.0


def test_first_relevant_result_at_rank_two() -> None:
    assert reciprocal_rank(
        ["irrelevant", "relevant", "other"],
        {"relevant"},
    ) == 0.5


def test_first_relevant_result_at_rank_three() -> None:
    assert reciprocal_rank(["a", "b", "c"], {"c"}) == pytest.approx(1.0 / 3)


def test_no_relevant_result_has_zero_reciprocal_rank() -> None:
    assert reciprocal_rank(["a", "b"], {"c"}) == 0.0


def test_recall_at_k_perfect() -> None:
    assert recall_at_k(["a", "b", "c"], {"a", "b"}, k=2) == 1.0


def test_recall_at_k_partial() -> None:
    assert recall_at_k(["a", "b", "c"], {"a", "d"}, k=2) == 0.5


def test_recall_at_k_zero() -> None:
    assert recall_at_k(["a", "b", "c"], {"x", "y"}, k=3) == 0.0


def test_recall_at_k_invalid_k_raises() -> None:
    with pytest.raises(ValueError, match="k must be >= 1"):
        recall_at_k(["a"], {"a"}, k=0)


def test_recall_at_k_empty_relevance_convention() -> None:
    assert recall_at_k([], set(), k=5) == 1.0
    assert recall_at_k(["a"], set(), k=5) == 0.0
