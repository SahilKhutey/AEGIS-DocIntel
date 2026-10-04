'''
Retrieval quality metrics (P@K, R@K, MRR, NDCG).
'''
from __future__ import annotations

import math
from typing import Sequence


def precision_at_k(retrieved: Sequence[str], relevant: Sequence[str], k: int = 10) -> float:
    '''Precision@K.'''
    if k == 0:
        return 0.0
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    rel_set = set(relevant)
    hits = sum(1 for x in top_k if x in rel_set)
    return hits / k


def recall_at_k(retrieved: Sequence[str], relevant: Sequence[str], k: int = 10) -> float:
    '''Recall@K.'''
    if not relevant:
        return 1.0
    rel_set = set(relevant)
    top_k = retrieved[:k]
    hits = sum(1 for x in top_k if x in rel_set)
    return hits / len(rel_set)


def mrr(retrieved: Sequence[str], relevant: Sequence[str]) -> float:
    '''Mean Reciprocal Rank.'''
    rel_set = set(relevant)
    for i, r in enumerate(retrieved, start=1):
        if r in rel_set:
            return 1.0 / i
    return 0.0


def ndcg_at_k(retrieved: Sequence[str], relevant: Sequence[str], k: int = 10) -> float:
    '''Normalized Discounted Cumulative Gain.'''
    rel_set = set(relevant)
    dcg = 0.0
    for i, r in enumerate(retrieved[:k], start=1):
        if r in rel_set:
            dcg += 1.0 / math.log2(i + 1)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(relevant), k) + 1))
    return dcg / idcg if idcg > 0 else 0.0


def hit_rate(retrieved: Sequence[str], relevant: Sequence[str]) -> float:
    '''Whether any relevant item is in retrieved.'''
    rel_set = set(relevant)
    return 1.0 if any(r in rel_set for r in retrieved) else 0.0
