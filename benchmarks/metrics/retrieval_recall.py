"""Retrieval quality metrics."""

from __future__ import annotations

import statistics
from typing import Iterable


def evaluate(
    *,
    gold_unit_ids: Iterable[list[str]],
    retrieved_unit_ids: Iterable[list[str]],
    k_values: tuple[int, ...] = (1, 5, 10),
) -> dict[str, float]:
    gold = list(gold_unit_ids)
    ret = list(retrieved_unit_ids)
    if not gold:
        return {"recall_at_1": 0.0, "recall_at_5": 0.0, "recall_at_10": 0.0, "mrr": 0.0, "map": 0.0}

    metrics = {f"recall_at_{k}": 0.0 for k in k_values}
    mrr_total = 0.0
    map_total = 0.0

    for gold_ids, r_ids in zip(gold, ret, strict=False):
        gold_set = set(gold_ids)
        if not gold_set:
            continue
        for k in k_values:
            topk = set(r_ids[:k])
            metrics[f"recall_at_{k}"] += len(gold_set & topk) / len(gold_set)

        for rank, uid in enumerate(r_ids, start=1):
            if uid in gold_set:
                mrr_total += 1.0 / rank
                break

        hits = 0
        ap = 0.0
        for rank, uid in enumerate(r_ids, start=1):
            if uid in gold_set:
                hits += 1
                ap += hits / rank
        map_total += ap / len(gold_set) if gold_set else 0.0

    n = len(gold)
    out = {k: round(v / n, 4) for k, v in metrics.items()}
    out["mrr"] = round(mrr_total / n, 4)
    out["map"] = round(map_total / n, 4)
    return out


__all__ = ["evaluate"]
