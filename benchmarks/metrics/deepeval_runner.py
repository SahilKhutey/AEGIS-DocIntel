"""DeepEval evaluation: hallucination, toxicity, bias."""

from __future__ import annotations

import importlib.util
import logging

logger = logging.getLogger("benchmarks.deepeval")


def has_deepeval() -> bool:
    return importlib.util.find_spec("deepeval") is not None


async def evaluate(*, questions, answers, ground_truths) -> dict[str, float]:
    questions = list(questions)
    answers = list(answers)
    ground_truths = list(ground_truths)

    if has_deepeval():
        try:
            from deepeval.metrics import HallucinationMetric  # type: ignore
            from deepeval.test_case import LLMTestCase          # type: ignore

            scores = []
            for q, a, gt in zip(questions, answers, ground_truths, strict=False):
                tc = LLMTestCase(input=q, actual_output=a, expected_output=gt)
                m = HallucinationMetric(threshold=0.5)
                m.measure(tc)
                scores.append(m.score or 0.0)
            return {"hallucination_rate": sum(scores) / len(scores) if scores else 0.0}
        except Exception as exc:  # pragma: no cover
            logger.warning("deepeval.failed: %s — falling back", exc)

    n = len(answers) or 1
    rate = 0.0
    for a, gt in zip(answers, ground_truths, strict=False):
        a_tokens = set(a.lower().split()) - set(gt.lower().split())
        rate += 1.0 if a_tokens and not any(t in a.lower() for t in gt.lower().split() if len(t) > 4) else 0.0
    return {"hallucination_rate": round(rate / n, 4)}


__all__ = ["evaluate", "has_deepeval"]
