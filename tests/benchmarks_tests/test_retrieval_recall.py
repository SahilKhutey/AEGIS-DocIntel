"""Recall@K, MRR, MAP edge cases."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from benchmarks.metrics.retrieval_recall import evaluate




@pytest.mark.parametrize(
    "gold,ret,expected",
    [
        ([["a"]],     [["a", "b", "c"]], {"recall_at_1": 1.0, "mrr": 1.0}),
        ([["a"]],     [["b", "a", "c"]], {"recall_at_1": 0.0, "recall_at_5": 1.0, "mrr": 0.5}),
        ([["a","b"]], [["b", "a"]],     {"recall_at_5": 1.0, "mrr": 1.0}),
        ([],          [],               {"recall_at_5": 0.0, "mrr": 0.0}),
    ],
)

def test_metric(gold, ret, expected) -> None:
    out = evaluate(gold_unit_ids=gold, retrieved_unit_ids=ret)
    for k, v in expected.items():
        assert out[k] == v
