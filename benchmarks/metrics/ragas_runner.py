"""RAGAS evaluation: faithfulness, answer relevancy, context recall/precision."""

from __future__ import annotations

import importlib.util
import logging
from typing import Iterable

logger = logging.getLogger("benchmarks.ragas")


def has_ragas() -> bool:
    return importlib.util.find_spec("ragas") is not None


async def evaluate(
    *,
    questions: Iterable[str],
    answers: Iterable[str],
    contexts: Iterable[list[str]],
    ground_truths: Iterable[str],
) -> dict[str, float]:
    """Run RAGAS if available; else return deterministic proxies."""
    questions = list(questions)
    answers = list(answers)
    contexts = list(contexts)
    ground_truths = list(ground_truths)

    if has_ragas():
        try:
            from datasets import Dataset  # type: ignore
            from ragas import evaluate as ragas_eval  # type: ignore
            from ragas.metrics import (  # type: ignore
                faithfulness, answer_relevancy,
                context_precision, context_recall,
            )
            ds = Dataset.from_dict({
                "question": questions, "answer": answers,
                "contexts": contexts, "ground_truth": ground_truths,
            })
            result = ragas_eval(
                ds, metrics=[faithfulness, answer_relevancy,
                             context_precision, context_recall],
            )
            return {k: float(v) for k, v in result.items()}
        except Exception as exc:  # pragma: no cover
            logger.warning("ragas.failed: %s — falling back to proxy", exc)

    proxies = {"faithfulness": 0.0, "answer_relevancy": 0.0,
               "context_precision": 0.0, "context_recall": 0.0}
    for q, a, ctx, gt in zip(questions, answers, contexts, ground_truths, strict=False):
        a_tokens = set(a.lower().split())
        gt_tokens = set(gt.lower().split())
        if gt_tokens and a_tokens:
            proxies["answer_relevancy"] += len(a_tokens & gt_tokens) / len(a_tokens | gt_tokens)
        ctx_tokens = set(" ".join(ctx).lower().split())
        if gt_tokens:
            proxies["context_recall"] += len(ctx_tokens & gt_tokens) / max(len(gt_tokens), 1)
        proxies["context_precision"] += (
            1.0 if any(gt_tokens & set(c.lower().split()) for c in ctx) else 0.0
        )
        proxies["faithfulness"] += 1.0 if a_tokens & gt_tokens else 0.0

    n = max(len(questions), 1)
    return {k: round(v / n, 4) for k, v in proxies.items()}


__all__ = ["evaluate", "has_ragas"]
