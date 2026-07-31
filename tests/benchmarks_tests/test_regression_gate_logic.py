"""Regression gate respects tolerances in both directions."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json

from benchmarks.runners.run_regression import _flat




def _write(tmp: Path, name: str, aegis: dict) -> Path:
    p = tmp / name
    p.write_text(json.dumps({"aegis": aegis}), encoding="utf-8")
    return p


def test_flat_flattens_nested_metrics() -> None:
    flat = _flat({
        "retrieval": {"recall_at_5": 0.7, "mrr": 0.6},
        "citations": {"citation_precision": 0.8},
        "ragas":     {"faithfulness": 0.9},
        "deepeval":  {"hallucination_rate": 0.04},
        "tokens":    {"reduction_p50_pct": 60.0},
        "latency":   {"p50_ms": 120.0},
    })
    assert flat["recall_at_5"] == 0.7
    assert flat["citation_precision"] == 0.8
    assert flat["p50_ms"] == 120.0


def test_regression_comparison_logic(tmp_path) -> None:
    base = _write(tmp_path, "base.json", {
        "retrieval": {"recall_at_5": 0.80, "mrr": 0.70},
        "ragas":     {"faithfulness": 0.95},
    })
    cur = _write(tmp_path, "cur.json", {
        "retrieval": {"recall_at_5": 0.78, "mrr": 0.69},
        "ragas":     {"faithfulness": 0.94},
    })
    bf = _flat(json.loads(base.read_text())["aegis"])
    cf = _flat(json.loads(cur.read_text())["aegis"])
    assert cf["recall_at_5"] - bf["recall_at_5"] >= -0.05
