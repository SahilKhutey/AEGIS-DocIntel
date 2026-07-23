"""
AEGIS-AMDI — Adaptive Fusion Engine (Core Layer)
===================================================
THE KEY INNOVATION: Dynamic query routing to the cheapest,
most informative representation layer(s).

    R_final = α·S + β·G + γ·R + δ·F + ε·M + ζ·T + η·X
    W = (α, β, γ, δ, ε, ζ, η),   ΣW = 1

    W(q) = route(classify(q))   — query-type-dependent weights

Architecture:
    1. QueryClassifier → QueryType + confidence
    2. WeightRouter    → FusionWeights (7D simplex)
    3. Scorer          → per-element composite score
    4. Ranker          → top-k with MMR deduplication
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np

from AMDI.engines.geometry.element import Element, ElementType

log = logging.getLogger("amdi.fusion")


# ─────────────────────────────────────────────────────────────────
# Query Classification
# ─────────────────────────────────────────────────────────────────

class QueryType(str, Enum):
    NUMERICAL   = "numerical"    # total revenue, sum, count
    AGGREGATION = "aggregation"  # max, min, average, growth
    STRUCTURAL  = "structural"   # page X, section Y, chapter
    LAYOUT      = "layout"       # figure, diagram, chart position
    SEMANTIC    = "semantic"     # explain, why, how, conclude
    TEMPLATE    = "template"     # pattern, similar pages, layout type
    RECURRENCE  = "recurrence"   # headers, footers, repeated
    ENTITY      = "entity"       # who, author, date, where
    GRAPH       = "graph"        # references, citations, links
    TEMPORAL    = "temporal"     # version, update, change, v2
    UNKNOWN     = "unknown"


_PATTERNS: dict[QueryType, list[str]] = {
    QueryType.AGGREGATION:  [r"\btotal\b", r"\bsum\b", r"\bavg\b", r"\baverage\b",
                             r"\bgrowth\b", r"\bcount\b", r"\bmax\b", r"\bmin\b"],
    QueryType.NUMERICAL:    [r"\brevenue\b", r"\bprofit\b", r"\bcost\b", r"\bamount\b",
                             r"\bvalue\b", r"\bprice\b", r"\d[\d,]+"],
    QueryType.STRUCTURAL:   [r"\bpage\s+\d+", r"\bsection\b", r"\bchapter\b",
                             r"\bparagraph\b", r"\blocation\b"],
    QueryType.LAYOUT:       [r"\bdiagram\b", r"\bchart\b", r"\bfigure\b",
                             r"\bimage\b", r"\billustration\b", r"\blayout\b"],
    QueryType.TEMPLATE:     [r"\btemplate\b", r"\bpattern\b", r"\bsimilar\s+page",
                             r"\blayout\s+type\b"],
    QueryType.RECURRENCE:   [r"\bheader\b", r"\bfooter\b", r"\brepeated\b",
                             r"\bcommon\s+element", r"\beverywhere\b"],
    QueryType.GRAPH:        [r"\breferences?\b", r"\bcites?\b", r"\blinks?\s+to\b",
                             r"\brelates?\s+to\b", r"\bconnected\b"],
    QueryType.ENTITY:       [r"\bwho\b", r"\bauthor\b", r"\bwhen\b", r"\bwhere\b",
                             r"\bfounded\b", r"\bwritten\s+by\b"],
    QueryType.SEMANTIC:     [r"\bexplain\b", r"\bwhy\b", r"\bhow\b",
                             r"\bconclusion\b", r"\bsummary\b", r"\bmeaning\b"],
    QueryType.TEMPORAL:     [r"\bv\d+\b", r"\bversion\b", r"\bupdated?\b",
                             r"\bchanged?\b", r"\brevision\b"],
}


@dataclass
class FusionWeights:
    """
    W = (w_s, w_g, w_r, w_f, w_m, w_t, w_x),  ΣW = 1

    s = semantic      g = geometry   r = recurrence
    f = frequency     m = matrix     t = template
    x = graph/hypergraph
    """
    w_s: float = 0.50
    w_g: float = 0.15
    w_r: float = 0.08
    w_f: float = 0.10
    w_m: float = 0.05
    w_t: float = 0.07
    w_x: float = 0.05

    def normalized(self) -> "FusionWeights":
        arr = self._arr()
        s = arr.sum()
        arr = arr / s if s > 0 else arr
        return FusionWeights(*arr.tolist())

    def _arr(self) -> np.ndarray:
        return np.array([self.w_s, self.w_g, self.w_r,
                         self.w_f, self.w_m, self.w_t, self.w_x], dtype=np.float64)

    def dominant(self) -> str:
        names = ["semantic","geometry","recurrence","frequency","matrix","template","graph"]
        return names[int(np.argmax(self._arr()))]

    def to_dict(self) -> dict:
        return {"semantic":self.w_s,"geometry":self.w_g,"recurrence":self.w_r,
                "frequency":self.w_f,"matrix":self.w_m,"template":self.w_t,"graph":self.w_x}


# Tuned default weights per query type
_WEIGHT_TABLE: dict[QueryType, FusionWeights] = {
    QueryType.AGGREGATION:  FusionWeights(0.15, 0.03, 0.03, 0.08, 0.65, 0.02, 0.04),
    QueryType.NUMERICAL:    FusionWeights(0.20, 0.05, 0.03, 0.10, 0.55, 0.02, 0.05),
    QueryType.STRUCTURAL:   FusionWeights(0.15, 0.50, 0.08, 0.08, 0.05, 0.08, 0.06),
    QueryType.LAYOUT:       FusionWeights(0.10, 0.55, 0.05, 0.05, 0.05, 0.12, 0.08),
    QueryType.SEMANTIC:     FusionWeights(0.75, 0.05, 0.04, 0.05, 0.02, 0.02, 0.07),
    QueryType.TEMPLATE:     FusionWeights(0.12, 0.18, 0.10, 0.10, 0.03, 0.38, 0.09),
    QueryType.RECURRENCE:   FusionWeights(0.08, 0.12, 0.58, 0.10, 0.02, 0.05, 0.05),
    QueryType.ENTITY:       FusionWeights(0.68, 0.05, 0.04, 0.05, 0.05, 0.02, 0.11),
    QueryType.GRAPH:        FusionWeights(0.18, 0.08, 0.08, 0.05, 0.08, 0.03, 0.50),
    QueryType.TEMPORAL:     FusionWeights(0.25, 0.08, 0.22, 0.10, 0.12, 0.13, 0.10),
    QueryType.UNKNOWN:      FusionWeights(0.50, 0.15, 0.08, 0.10, 0.05, 0.07, 0.05),
}


# ─────────────────────────────────────────────────────────────────
# Fusion Result
# ─────────────────────────────────────────────────────────────────

@dataclass
class FusionResult:
    element:        Element
    final_score:    float
    layer_scores:   dict[str, float]
    rank:           int = 0

    def explain(self) -> str:
        ls = " | ".join(f"{k}={v:.2f}" for k, v in self.layer_scores.items())
        return (
            f"[{self.rank}] R={self.final_score:.3f} "
            f"({ls}) "
            f"type={self.element.type.value} p={self.element.page} "
            f"'{self.element.content[:50]}'"
        )


@dataclass
class FusionContext:
    query:        str
    query_type:   QueryType
    confidence:   float
    weights:      FusionWeights
    results:      list[FusionResult]
    table_answers: list[str]  = field(default_factory=list)
    latency_ms:   float       = 0.0


# ─────────────────────────────────────────────────────────────────
# Query Classifier
# ─────────────────────────────────────────────────────────────────

class QueryClassifier:

    def classify(self, query: str) -> tuple[QueryType, float]:
        q = query.lower()
        votes: dict[QueryType, int] = {}
        for qt, pats in _PATTERNS.items():
            hits = sum(1 for p in pats if re.search(p, q))
            if hits:
                votes[qt] = hits
        if not votes:
            return QueryType.UNKNOWN, 0.0
        best   = max(votes, key=votes.get)
        total  = sum(votes.values())
        conf   = votes[best] / total
        return best, conf

    def route(self, query: str) -> tuple[FusionWeights, QueryType, float]:
        qt, conf = self.classify(query)
        base = _WEIGHT_TABLE[qt]
        if conf < 0.4:
            unk  = _WEIGHT_TABLE[QueryType.UNKNOWN]
            mixed = FusionWeights(
                *(0.55 * b + 0.45 * u for b, u in
                  zip(base._arr().tolist(), unk._arr().tolist()))
            )
            return mixed.normalized(), qt, conf
        return base.normalized(), qt, conf


# ─────────────────────────────────────────────────────────────────
# Adaptive Fusion Engine
# ─────────────────────────────────────────────────────────────────

class AdaptiveFusionEngine:
    """
    Multi-signal adaptive fusion:

        R_final(q, e) = Σ_i w_i(q) · layer_i(q, e)

    Layer callbacks are injected at construction or overridden per-query.
    """

    def __init__(self):
        self.classifier = QueryClassifier()

    # ──────────────────────────────────────────────────────────────
    # Score all elements
    # ──────────────────────────────────────────────────────────────

    def fuse(
        self,
        query:           str,
        elements:        list[Element],
        *,
        s_scores:        Optional[dict[str, float]] = None,   # element_id → score
        g_scores:        Optional[dict[str, float]] = None,
        r_scores:        Optional[dict[str, float]] = None,
        f_scores:        Optional[dict[str, float]] = None,
        m_scores:        Optional[dict[str, float]] = None,
        t_scores:        Optional[dict[str, float]] = None,
        x_scores:        Optional[dict[str, float]] = None,
        table_answers:   Optional[list[str]] = None,
        top_k:           int = 12,
        use_mmr:         bool = True,
        mmr_lambda:      float = 0.70,
    ) -> FusionContext:
        import time
        t0 = time.perf_counter()

        weights, qt, conf = self.classifier.route(query)
        log.info(
            "Query classified: %s (conf=%.2f) → dominant=%s",
            qt.value, conf, weights.dominant(),
        )

        results: list[FusionResult] = []
        for e in elements:
            eid = e.element_id
            ls = {
                "semantic":   (s_scores or {}).get(eid, 0.0),
                "geometry":   (g_scores or {}).get(eid, 0.0),
                "recurrence": (r_scores or {}).get(eid, 0.0),
                "frequency":  (f_scores or {}).get(eid, 0.0),
                "matrix":     (m_scores or {}).get(eid, 0.0),
                "template":   (t_scores or {}).get(eid, 0.0),
                "graph":      (x_scores or {}).get(eid, 0.0),
            }
            composite = (
                weights.w_s * ls["semantic"]   +
                weights.w_g * ls["geometry"]   +
                weights.w_r * ls["recurrence"] +
                weights.w_f * ls["frequency"]  +
                weights.w_m * ls["matrix"]     +
                weights.w_t * ls["template"]   +
                weights.w_x * ls["graph"]
            )
            results.append(FusionResult(element=e, final_score=composite, layer_scores=ls))

        results.sort(key=lambda r: r.final_score, reverse=True)
        top = results[:top_k]

        if use_mmr:
            top = self._mmr(top, lambda_=mmr_lambda, top_k=top_k)

        for i, r in enumerate(top):
            r.rank = i + 1

        return FusionContext(
            query=query,
            query_type=qt,
            confidence=conf,
            weights=weights,
            results=top,
            table_answers=table_answers or [],
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
        )

    # ──────────────────────────────────────────────────────────────
    # MMR deduplication
    # ──────────────────────────────────────────────────────────────

    def _mmr(
        self,
        results: list[FusionResult],
        lambda_: float = 0.7,
        top_k: int = 10,
    ) -> list[FusionResult]:
        """
        MMR = argmax [ λ·R(q,e) - (1-λ)·max_sim(e, selected) ]
        Uses token-overlap similarity when embeddings absent.
        """
        if not results:
            return []
        selected: list[FusionResult] = []
        remaining = list(results)

        def _sim(r1: FusionResult, r2: FusionResult) -> float:
            # Cosine if both have embeddings
            e1, e2 = r1.element, r2.element
            if e1.embedding and e2.embedding:
                a = np.asarray(e1.embedding, dtype=np.float32)
                b = np.asarray(e2.embedding, dtype=np.float32)
                denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
                return float(np.dot(a, b) / denom)
            # Token-Jaccard fallback
            t1 = set(e1.content.lower().split())
            t2 = set(e2.content.lower().split())
            return len(t1 & t2) / max(1, len(t1 | t2))

        while remaining and len(selected) < top_k:
            if not selected:
                best = max(remaining, key=lambda r: r.final_score)
            else:
                best, best_score = None, -float("inf")
                for r in remaining:
                    max_sim = max(_sim(r, s) for s in selected)
                    score = lambda_ * r.final_score - (1 - lambda_) * max_sim
                    if score > best_score:
                        best_score = score
                        best = r
            selected.append(best)
            remaining.remove(best)

        return selected

    # ──────────────────────────────────────────────────────────────
    # Introspection
    # ──────────────────────────────────────────────────────────────

    def explain_routing(self, query: str) -> str:
        weights, qt, conf = self.classifier.route(query)
        lines = [
            f"Query:    '{query}'",
            f"Type:     {qt.value} (confidence={conf:.2f})",
            f"Dominant: {weights.dominant()}",
            "Weights:",
        ]
        for k, v in weights.to_dict().items():
            bar = "█" * int(v * 30)
            lines.append(f"  {k:<12} {v:.3f}  {bar}")
        return "\n".join(lines)
