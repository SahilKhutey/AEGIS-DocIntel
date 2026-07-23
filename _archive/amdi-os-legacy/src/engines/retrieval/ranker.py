"""
Hybrid Ranker
=============

Combines ranked lists from multiple search strategies using:
- Reciprocal Rank Fusion (RRF)
- Borda count
- Weighted sum of normalized scores
- Condorcet fusion
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .exceptions import RankFusionError


@dataclass
class RankedDocument:
    """A document in the hybrid ranking."""

    doc_id: Any
    fused_score: float
    per_method_score: Dict[str, float] = field(default_factory=dict)
    per_method_rank: Dict[str, int] = field(default_factory=dict)
    methods_found: List[str] = field(default_factory=list)
    final_rank: int = 0

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "fused_score": round(self.fused_score, 6),
            "per_method_score": {k: round(v, 6) for k, v in self.per_method_score.items()},
            "per_method_rank": dict(self.per_method_rank),
            "methods_found": self.methods_found,
            "final_rank": self.final_rank,
        }


@dataclass
class HybridRanking:
    """Result of hybrid ranking."""

    ranked_docs: List[RankedDocument]
    method: str
    num_docs: int
    num_sources: int

    def top(self, k: int = 10) -> List[RankedDocument]:
        return self.ranked_docs[:k]

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "num_docs": self.num_docs,
            "num_sources": self.num_sources,
            "docs": [d.to_dict() for d in self.ranked_docs],
        }


class HybridRanker:
    """
    Combines results from multiple search methods.
    """

    METHODS = ("rrf", "borda", "weighted_sum", "condorcet")

    def __init__(
        self,
        method: str = "rrf",
        rrf_k: int = 60,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        if method not in self.METHODS:
            raise ValueError(f"Unknown method: {method}")
        self.method = method
        self.rrf_k = rrf_k
        self.weights = weights or {}

    def fuse(
        self,
        method_results: Dict[str, List[Tuple[Any, float]]],
        weights: Optional[Dict[str, float]] = None,
        top_k: Optional[int] = None,
    ) -> HybridRanking:
        """
        Fuse ranked lists from multiple search methods.

        Parameters
        ----------
        method_results : Dict[str, List[Tuple[Any, float]]]
            Method name → list of (doc_id, score).
        weights : Optional[Dict[str, float]]
            Per-method weights.
        top_k : Optional[int]
        """
        if not method_results:
            raise RankFusionError("No method results provided.")
        w = weights or self.weights
        # normalize weights
        w_total = sum(w.get(m, 1.0) for m in method_results)
        if w_total <= 0:
            w_total = 1.0
        norm_w = {m: w.get(m, 1.0) / w_total for m in method_results}

        if self.method == "rrf":
            fused_scores = self._rrf(method_results, norm_w)
        elif self.method == "borda":
            fused_scores = self._borda(method_results, norm_w)
        elif self.method == "weighted_sum":
            fused_scores = self._weighted_sum(method_results, norm_w)
        elif self.method == "condorcet":
            fused_scores = self._condorcet(method_results, norm_w)
        else:
            raise RankFusionError(f"Unknown method: {self.method}")

        # sort
        sorted_docs = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        if top_k is not None:
            sorted_docs = sorted_docs[:top_k]

        # build per-method rank map
        per_method_ranks: Dict[str, Dict[Any, int]] = {}
        for method, results in method_results.items():
            per_method_ranks[method] = {}
            sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
            for rank, (did, _) in enumerate(sorted_results, start=1):
                per_method_ranks[method][did] = rank

        ranked_docs: List[RankedDocument] = []
        for final_rank, (did, score) in enumerate(sorted_docs, start=1):
            per_method_score = {}
            per_method_rank = {}
            methods_found = []
            for method, results in method_results.items():
                for d, s in results:
                    if d == did:
                        per_method_score[method] = float(s)
                        per_method_rank[method] = per_method_ranks[method][did]
                        methods_found.append(method)
                        break
            ranked_docs.append(
                RankedDocument(
                    doc_id=did,
                    fused_score=float(score),
                    per_method_score=per_method_score,
                    per_method_rank=per_method_rank,
                    methods_found=methods_found,
                    final_rank=final_rank,
                )
            )

        return HybridRanking(
            ranked_docs=ranked_docs,
            method=self.method,
            num_docs=len(ranked_docs),
            num_sources=len(method_results),
        )

    def _rrf(self, method_results: Dict[str, List[Tuple[Any, float]]], norm_w: Dict[str, float]) -> Dict[Any, float]:
        fused: Dict[Any, float] = {}
        for method, results in method_results.items():
            weight = norm_w.get(method, 1.0)
            sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
            for rank, (did, _) in enumerate(sorted_results, start=1):
                fused[did] = fused.get(did, 0.0) + weight / (self.rrf_k + rank)
        return fused

    def _borda(self, method_results: Dict[str, List[Tuple[Any, float]]], norm_w: Dict[str, float]) -> Dict[Any, float]:
        all_docs = set()
        for results in method_results.values():
            for did, _ in results:
                all_docs.add(did)
        N = len(all_docs)

        fused: Dict[Any, float] = {}
        for method, results in method_results.items():
            weight = norm_w.get(method, 1.0)
            sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
            for rank, (did, _) in enumerate(sorted_results, start=1):
                points = N - rank
                fused[did] = fused.get(did, 0.0) + weight * max(points, 0)
        return fused

    def _weighted_sum(self, method_results: Dict[str, List[Tuple[Any, float]]], norm_w: Dict[str, float]) -> Dict[Any, float]:
        fused: Dict[Any, float] = {}
        for method, results in method_results.items():
            if not results:
                continue
            weight = norm_w.get(method, 1.0)
            scores = [s for _, s in results]
            min_s = min(scores)
            max_s = max(scores)
            diff = max_s - min_s
            if diff < 1e-12:
                diff = 1.0
            for did, s in results:
                norm_s = (s - min_s) / diff
                fused[did] = fused.get(did, 0.0) + weight * norm_s
        return fused

    def _condorcet(self, method_results: Dict[str, List[Tuple[Any, float]]], norm_w: Dict[str, float]) -> Dict[Any, float]:
        all_docs = list({did for results in method_results.values() for did, _ in results})
        n = len(all_docs)
        if n == 0:
            return {}

        ranks: Dict[str, Dict[Any, int]] = {}
        for method, results in method_results.items():
            ranks[method] = {}
            sorted_res = sorted(results, key=lambda x: x[1], reverse=True)
            for r, (did, _) in enumerate(sorted_res, start=1):
                ranks[method][did] = r

        copeland_scores = {did: 0.0 for did in all_docs}
        for i in range(n):
            for j in range(i + 1, n):
                doc_a = all_docs[i]
                doc_b = all_docs[j]

                pref_a = 0.0
                pref_b = 0.0
                for method in method_results:
                    w_m = norm_w.get(method, 1.0)
                    rank_a = ranks[method].get(doc_a, 999999)
                    rank_b = ranks[method].get(doc_b, 999999)
                    if rank_a < rank_b:
                        pref_a += w_m
                    elif rank_b < rank_a:
                        pref_b += w_m

                if pref_a > pref_b:
                    copeland_scores[doc_a] += 1.0
                    copeland_scores[doc_b] -= 1.0
                elif pref_b > pref_a:
                    copeland_scores[doc_b] += 1.0
                    copeland_scores[doc_a] -= 1.0

        if all_docs:
            min_score = min(copeland_scores.values())
            max_score = max(copeland_scores.values())
            diff = max_score - min_score
            if diff < 1e-12:
                diff = 1.0
            return {did: (score - min_score) / diff for did, score in copeland_scores.items()}
        return {}
