"""
aegis.intelligence.retrieval.evaluator
======================================
Retrieval evaluation metrics: Precision@K, Recall@K, MRR, nDCG@K, MAP, and latency distributions.
"""

from __future__ import annotations

import math
import statistics
from typing import Any, Dict, List, Set
from pydantic import BaseModel, Field

from aegis.intelligence.models import RetrievalResult


class RetrievalMetrics(BaseModel):
    queries_evaluated: int
    precision_at_k: float = Field(ge=0.0, le=1.0)
    recall_at_k: float = Field(ge=0.0, le=1.0)
    mrr: float = Field(ge=0.0, le=1.0)
    ndcg_at_k: float = Field(ge=0.0, le=1.0)
    map_score: float = Field(ge=0.0, le=1.0)
    latency_median_ms: float = Field(ge=0.0)
    latency_p95_ms: float = Field(ge=0.0)
    latency_p99_ms: float = Field(ge=0.0)


class RetrievalEvaluator:
    """Evaluates retrieval results against ground truth relevance annotations."""

    @staticmethod
    def compute_dcg(relevances: List[int], k: int) -> float:
        dcg = 0.0
        for i, rel in enumerate(relevances[:k], start=1):
            dcg += (2**rel - 1) / math.log2(i + 1)
        return dcg

    @classmethod
    def evaluate_query(
        cls,
        result: RetrievalResult,
        relevant_chunks: Set[str],
        graded_relevance: Optional[Dict[str, int]] = None,
        k: int = 5,
    ) -> Dict[str, float]:
        """Compute metrics for a single query."""
        retrieved_chunks = [item.chunk_id for item in result.results[:k]]
        num_relevant_total = len(relevant_chunks)

        if num_relevant_total == 0:
            # Query has no relevant chunks (unanswerable / negative case)
            return {
                "precision": 1.0 if not retrieved_chunks else 0.0,
                "recall": 1.0,
                "reciprocal_rank": 0.0,
                "ndcg": 1.0 if not retrieved_chunks else 0.0,
                "average_precision": 1.0 if not retrieved_chunks else 0.0,
            }

        # Precision@K
        hits = [1 if cid in relevant_chunks else 0 for cid in retrieved_chunks]
        num_hits = sum(hits)
        precision = num_hits / max(1, k)

        # Recall@K
        recall = num_hits / num_relevant_total

        # Reciprocal Rank (MRR)
        rr = 0.0
        for rank, is_hit in enumerate(hits, start=1):
            if is_hit:
                rr = 1.0 / rank
                break

        # Average Precision (MAP)
        running_hits = 0
        prec_sum = 0.0
        for rank, is_hit in enumerate(hits, start=1):
            if is_hit:
                running_hits += 1
                prec_sum += running_hits / rank
        ap = prec_sum / max(1, min(num_relevant_total, k))

        # nDCG@K
        g_rel = graded_relevance or {cid: 1 for cid in relevant_chunks}
        actual_rels = [g_rel.get(cid, 0) for cid in retrieved_chunks]
        ideal_rels = sorted(g_rel.values(), reverse=True)[:k]

        actual_dcg = cls.compute_dcg(actual_rels, k=k)
        ideal_dcg = cls.compute_dcg(ideal_rels, k=k)
        ndcg = min(1.0, actual_dcg / ideal_dcg) if ideal_dcg > 0 else 0.0

        return {
            "precision": precision,
            "recall": recall,
            "reciprocal_rank": rr,
            "ndcg": ndcg,
            "average_precision": ap,
        }

    @classmethod
    def evaluate_batch(
        cls,
        eval_cases: List[Dict[str, Any]],
        k: int = 5,
    ) -> RetrievalMetrics:
        """
        eval_cases format:
        [
            {
                "result": RetrievalResult,
                "relevant_chunks": set[str],
                "graded_relevance": dict[str, int] (optional)
            },
            ...
        ]
        """
        if not eval_cases:
            return RetrievalMetrics(
                queries_evaluated=0,
                precision_at_k=0.0,
                recall_at_k=0.0,
                mrr=0.0,
                ndcg_at_k=0.0,
                map_score=0.0,
                latency_median_ms=0.0,
                latency_p95_ms=0.0,
                latency_p99_ms=0.0,
            )

        precisions: List[float] = []
        recalls: List[float] = []
        rrs: List[float] = []
        ndcgs: List[float] = []
        aps: List[float] = []
        latencies: List[float] = []

        for case in eval_cases:
            res: RetrievalResult = case["result"]
            rel_chunks: Set[str] = set(case["relevant_chunks"])
            g_rel = case.get("graded_relevance")

            m = cls.evaluate_query(result=res, relevant_chunks=rel_chunks, graded_relevance=g_rel, k=k)
            precisions.append(m["precision"])
            recalls.append(m["recall"])
            rrs.append(m["reciprocal_rank"])
            ndcgs.append(m["ndcg"])
            aps.append(m["average_precision"])
            latencies.append(res.latency_ms)

        # Percentiles
        sorted_lat = sorted(latencies)
        n = len(sorted_lat)
        med_lat = statistics.median(sorted_lat)
        p95_lat = sorted_lat[min(int(n * 0.95), n - 1)]
        p99_lat = sorted_lat[min(int(n * 0.99), n - 1)]

        return RetrievalMetrics(
            queries_evaluated=len(eval_cases),
            precision_at_k=round(statistics.mean(precisions), 4),
            recall_at_k=round(statistics.mean(recalls), 4),
            mrr=round(statistics.mean(rrs), 4),
            ndcg_at_k=round(statistics.mean(ndcgs), 4),
            map_score=round(statistics.mean(aps), 4),
            latency_median_ms=round(med_lat, 3),
            latency_p95_ms=round(p95_lat, 3),
            latency_p99_ms=round(p99_lat, 3),
        )
