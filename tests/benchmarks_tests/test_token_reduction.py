"""Token reduction summary."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.metrics.token_reduction import evaluate, summarize




def test_evaluate_returns_ratio() -> None:
    out = evaluate([(1000, 200), (800, 100)])
    assert out.raw_total == 1800
    assert out.aegis_total == 300
    assert 0 < out.ratio < 1


def test_summarize_includes_p95() -> None:
    s = summarize([(100 * i, 10 * i) for i in range(1, 11)])
    assert "reduction_p50_pct" in s
    assert "reduction_p95_pct" in s


def test_zero_safe() -> None:
    out = evaluate([])
    assert out.ratio == 0.0
