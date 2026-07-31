"""Citation precision/recall/nDCG."""

from __future__ import annotations

import math
from typing import Iterable


def evaluate(
    *,
    gold_citations: Iterable[list[tuple[str, int | None]]],
    predicted_citations: Iterable[list[dict]],
) -> dict[str, float]:
    gold_citations = list(gold_citations)
    predicted_citations = list(predicted_citations)

    p_total = r_total = hit_count = 0
    for gold, pred in zip(gold_citations, predicted_citations, strict=False):
        gold_set = {(d, p) for d, p in gold}
        pred_set = {(c.get("document_id"), c.get("page")) for c in pred}
        p_total += len(pred_set)
        r_total += len(gold_set)
        hit_count += len(gold_set & pred_set)

    precision = (hit_count / p_total) if p_total else 0.0
    recall    = (hit_count / r_total) if r_total else 0.0
    return {
        "citation_precision": round(precision, 4),
        "citation_recall":    round(recall, 4),
        "citation_ndcg":      round(_ndcg(gold_citations, predicted_citations), 4),
    }


def _ndcg(gold_citations, predicted_citations, k: int = 10) -> float:
    scores = []
    for gold, pred in zip(gold_citations, predicted_citations, strict=False):
        gold_set = {(d, p) for d, p in gold}
        pred_list = [(c.get("document_id"), c.get("page")) for c in pred][:k]
        dcg = sum(
            (1 if (doc, pg) in gold_set else 0) / math.log2(i + 2)
            for i, (doc, pg) in enumerate(pred_list)
        )
        ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(gold_set), k)))
        scores.append(dcg / ideal if ideal else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


__all__ = ["evaluate"]
