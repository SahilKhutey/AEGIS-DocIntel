"""
aegis.evaluation.metrics.registry
=================================
Central registry of evaluation metrics, standard formulas, and verifiers.
"""
from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Tuple


class MetricRegistry:
    """Registry of mathematical metric calculations for document intelligence."""

    _registry: Dict[str, Callable[..., float]] = {}

    @classmethod
    def register(cls, name: str) -> Callable:
        def decorator(fn: Callable[..., float]) -> Callable[..., float]:
            cls._registry[name] = fn
            return fn
        return decorator

    @classmethod
    def compute(cls, name: str, *args, **kwargs) -> float:
        if name not in cls._registry:
            raise KeyError(f"Metric '{name}' not found in MetricRegistry")
        return cls._registry[name](*args, **kwargs)

    @classmethod
    def list_metrics(cls) -> List[str]:
        return sorted(cls._registry.keys())


@MetricRegistry.register("precision")
def compute_precision(tp: int, fp: int) -> float:
    return tp / (tp + fp) if (tp + fp) > 0 else 1.0


@MetricRegistry.register("recall")
def compute_recall(tp: int, fn: int) -> float:
    return tp / (tp + fn) if (tp + fn) > 0 else 1.0


@MetricRegistry.register("f1")
def compute_f1(tp: int, fp: int, fn: int) -> float:
    p = compute_precision(tp, fp)
    r = compute_recall(tp, fn)
    return (2 * p * r) / (p + r) if (p + r) > 0 else 0.0


@MetricRegistry.register("grounding_fidelity")
def compute_grounding_fidelity(verified_quotes: int, total_quotes: int) -> float:
    return verified_quotes / total_quotes if total_quotes > 0 else 1.0


@MetricRegistry.register("reciprocal_rank")
def compute_reciprocal_rank(ranked_ids: List[str], gold_id: str) -> float:
    for rank_idx, doc_id in enumerate(ranked_ids, start=1):
        if doc_id == gold_id:
            return 1.0 / rank_idx
    return 0.0
