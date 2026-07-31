"""RRF correctness: top-K by raw RRF rank, ties broken by sum of inverse ranks."""

from __future__ import annotations

from amdi.retrieval.fusion import rrf_fuse
from amdi.retrieval.schemas import Evidence


def _ev(uid: str, **scores) -> Evidence:
    e = Evidence(text=f"text for {uid}", **scores)
    e.metadata["unit_id"] = uid
    return e


def test_rrf_orders_top_rank_first() -> None:
    a = _ev("A", score_bm25=0.9)
    b = _ev("B", score_bm25=0.7)
    bm25 = [a, b]
    c = _ev("A", score_dense=0.95)
    d = _ev("C", score_dense=0.50)
    dense = [c, d]

    fused = rrf_fuse({"bm25": bm25, "dense": dense}, k=60)
    keys = [e.metadata["unit_id"] for e in fused]
    assert keys[0] == "A"
    assert "B" in keys and "C" in keys


def test_rrf_weight_changes_order() -> None:
    a = _ev("A", score_bm25=0.9)
    b = _ev("B", score_bm25=0.7)
    bm25 = [a, b]
    c = _ev("A", score_dense=0.30)
    d = _ev("C", score_dense=0.95)
    dense = [d, c]

    # dense weighted much higher than bm25 so dense rank 1 (C) beats multi-list hit A
    fused = rrf_fuse(
        {"bm25": bm25, "dense": dense},
        k=60, weights={"bm25": 0.01, "dense": 1.0},
    )
    keys = [e.metadata["unit_id"] for e in fused]
    assert keys[0] == "C"


def test_rrf_handles_missing_method() -> None:
    fused = rrf_fuse({"bm25": [_ev("X", score_bm25=0.5)]}, k=60)
    assert len(fused) == 1
    assert fused[0].metadata["unit_id"] == "X"
