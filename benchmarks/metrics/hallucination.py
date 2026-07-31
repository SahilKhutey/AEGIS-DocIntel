"""Unsupported-claim rate (custom, deterministic stub)."""

from __future__ import annotations

import re
from typing import Iterable


def evaluate(
    *,
    answers: Iterable[str],
    retrieved_evidence: Iterable[list[str]],
) -> dict[str, float]:
    answers = list(answers)
    evidence_text = list(retrieved_evidence)

    total_claims = 0
    unsupported = 0
    for ans, evs in zip(answers, evidence_text, strict=False):
        ev_blob = " ".join(evs).lower()
        for sent in re.split(r"(?<=[.!?])\s+", ans.strip()):
            sent = sent.strip()
            if not sent:
                continue
            tokens = [t for t in re.findall(r"\b\w+\b", sent.lower()) if len(t) > 3]
            if not tokens:
                continue
            total_claims += 1
            overlap = sum(1 for t in tokens if t in ev_blob)
            if overlap / len(tokens) < 0.5:
                unsupported += 1

    rate = unsupported / total_claims if total_claims else 0.0
    return {"unsupported_claim_rate": round(rate, 4)}


__all__ = ["evaluate"]
