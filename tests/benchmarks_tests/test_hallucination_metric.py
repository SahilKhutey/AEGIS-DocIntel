"""Unsupported-claim detection."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.metrics.hallucination import evaluate




def test_all_supported() -> None:
    out = evaluate(
        answers=["Einstein proposed relativity in 1915."],
        retrieved_evidence=[["Albert Einstein proposed general relativity in 1915."]],
    )
    assert out["unsupported_claim_rate"] == 0.0


def test_all_unsupported() -> None:
    out = evaluate(
        answers=["Quantum unicorns roam the lunar surface on Tuesdays."],
        retrieved_evidence=[["Albert Einstein proposed general relativity."]],
    )
    assert out["unsupported_claim_rate"] > 0.5


def test_empty_inputs() -> None:
    out = evaluate(answers=[], retrieved_evidence=[])
    assert out["unsupported_claim_rate"] == 0.0
