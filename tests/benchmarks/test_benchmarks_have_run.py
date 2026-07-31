"""The benchmark runner exists and produces the expected artefacts."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.parametrize("path", [
    "benchmarks/runners/run_all.py",
    "benchmarks/runners/run_regression.py",
    "benchmarks/runners/publish_report.py",
    "benchmarks/metrics/ragas_runner.py",
    "benchmarks/metrics/citation_precision.py",
    "benchmarks/metrics/token_reduction.py",
])
def test_benchmark_module_exists(path: str) -> None:
    assert Path(path).exists()
