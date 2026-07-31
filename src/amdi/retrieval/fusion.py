"""Reciprocal Rank Fusion (RRF) and weighted-sum fusion over heterogeneous retrievers."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable

from amdi.retrieval.schemas import Citation, Evidence, RetrievalConfig

METHOD_SCORE_KEY = {
    "bm25": "score_bm25",
    "dense": "score_dense",
    "frequency": "score_frequency",
    "geometry": "score_geometry",
    "graph": "score_graph",
    "matrix": "score_matrix",
    "template": "score_template",
}


def rrf_fuse(
    method_results: dict[str, list[Evidence]],
    *,
    k: int = 60,
    weights: dict[str, float] | None = None,
) -> list[Evidence]:
    """Reciprocal Rank Fusion."""
    weights = weights or {}
    fused_scores: dict[str, float] = defaultdict(float)
    primary: dict[str, Evidence] = {}
    citations: dict[str, list] = defaultdict(list)

    for method, items in method_results.items():
        w = weights.get(method, 1.0)
        for rank, ev in enumerate(items, start=1):
            key = ev.metadata.get("unit_id") or ev.evidence_id
            fused_scores[key] += w / (k + rank)
            primary.setdefault(key, ev)
            for c in ev.citations:
                if c not in citations[key]:
                    citations[key].append(c)

    out: list[Evidence] = []
    for key, s in fused_scores.items():
        ev = primary[key].model_copy(deep=True)
        ev.score_fused = float(s)
        ev.citations = [
            Citation(**c) if isinstance(c, dict) else c for c in citations[key]
        ]
        out.append(ev)

    out.sort(key=lambda e: e.score_fused, reverse=True)
    return out


def weighted_sum_fuse(
    method_results: dict[str, list[Evidence]],
    *,
    weights: dict[str, float] | None = None,
) -> list[Evidence]:
    """Simple weighted-sum of normalized scores."""
    weights = weights or {}
    fused_scores: dict[str, float] = defaultdict(float)
    primary: dict[str, Evidence] = {}
    citations: dict[str, list] = defaultdict(list)

    for method, items in method_results.items():
        w = weights.get(method, 1.0)
        for ev in items:
            key = ev.metadata.get("unit_id") or ev.evidence_id
            score_key = METHOD_SCORE_KEY.get(method)
            s = float(getattr(ev, score_key, 0.0)) if score_key else 0.0
            fused_scores[key] += w * s
            primary.setdefault(key, ev)
            for c in ev.citations:
                if c not in citations[key]:
                    citations[key].append(c)

    out: list[Evidence] = []
    for key, s in fused_scores.items():
        ev = primary[key].model_copy(deep=True)
        ev.score_fused = float(s)
        out.append(ev)
    out.sort(key=lambda e: e.score_fused, reverse=True)
    return out


def calibrated_fuse(
    method_results: dict[str, list[Evidence]],
    *,
    cfg: RetrievalConfig,
) -> list[Evidence]:
    """Per-method min-max calibration -> weighted sum -> RRF tie-break."""
    weights = cfg.weights
    calibrated: dict[str, list[Evidence]] = {}
    for method, items in method_results.items():
        if not items:
            continue
        score_key = METHOD_SCORE_KEY.get(method)
        scores = [float(getattr(e, score_key, 0.0)) for e in items] if score_key else [0.0] * len(items)
        if not scores:
            continue
        lo, hi = min(scores), max(scores)
        span = (hi - lo) or 1.0
        new_items = []
        for ev, raw in zip(items, scores, strict=False):
            ev2 = ev.model_copy(deep=True)
            if score_key:
                setattr(ev2, score_key, (raw - lo) / span)
            new_items.append(ev2)
        calibrated[method] = new_items

    ws = weighted_sum_fuse(calibrated, weights=weights)
    rrf_inputs = {m: items for m, items in calibrated.items()}
    rrf = rrf_fuse(rrf_inputs, k=cfg.rrf_k, weights=weights)

    rank1 = {ev.metadata.get("unit_id"): r for r, ev in enumerate(ws)}
    rank2 = {ev.metadata.get("unit_id"): r for r, ev in enumerate(rrf)}
    keys = set(rank1) | set(rank2)
    combined = []
    for key in keys:
        r = (rank1.get(key, 10_000) + 1) * (rank2.get(key, 10_000) + 1)
        ev = next((e for e in ws + rrf if (e.metadata.get("unit_id") == key)), None)
        if ev is None:
            continue
        ev2 = ev.model_copy(deep=True)
        ev2.score_fused = 1.0 / math.sqrt(r)
        combined.append(ev2)
    combined.sort(key=lambda e: e.score_fused, reverse=True)
    return combined


def fuse(
    method_results: dict[str, list[Evidence]],
    cfg: RetrievalConfig,
) -> list[Evidence]:
    if cfg.fusion == "rrf":
        return rrf_fuse(method_results, k=cfg.rrf_k, weights=cfg.weights)
    if cfg.fusion == "weighted":
        return weighted_sum_fuse(method_results, weights=cfg.weights)
    if cfg.fusion == "calibrated":
        return calibrated_fuse(method_results, cfg=cfg)
    raise ValueError(f"unknown fusion strategy: {cfg.fusion}")


__all__ = ["fuse", "rrf_fuse", "weighted_sum_fuse", "calibrated_fuse"]
