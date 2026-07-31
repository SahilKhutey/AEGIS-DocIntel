"""Calibrated fusion is robust when one method has very different scale."""

from __future__ import annotations

from amdi.retrieval.fusion import calibrated_fuse
from amdi.retrieval.schemas import Evidence, RetrievalConfig


def _ev(uid: str, **scores) -> Evidence:
    e = Evidence(text=f"text {uid}", **scores)
    e.metadata["unit_id"] = uid
    return e


def test_calibration_normalizes_scores() -> None:
    cfg = RetrievalConfig()
    bm25 = [_ev("A", score_bm25=100.0), _ev("B", score_bm25=10.0)]
    dense = [_ev("A", score_dense=0.9),  _ev("B", score_dense=0.1)]

    fused = calibrated_fuse({"bm25": bm25, "dense": dense}, cfg=cfg)
    assert fused[0].metadata["unit_id"] == "A"


def test_calibration_handles_one_empty_method() -> None:
    cfg = RetrievalConfig()
    fused = calibrated_fuse(
        {"bm25": [_ev("A", score_bm25=0.5)], "dense": []},
        cfg=cfg,
    )
    assert fused and fused[0].metadata["unit_id"] == "A"
