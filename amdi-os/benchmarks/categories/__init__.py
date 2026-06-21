'''
AEGIS-AMDI-OS — Benchmark Categories
=====================================
Modular benchmark categories wrapping the pipelines.
'''
from __future__ import annotations

from benchmarks.categories.accuracy_bench import AccuracyBenchmark
from benchmarks.categories.compression_bench import CompressionBenchmark
from benchmarks.categories.latency_bench import LatencyBenchmark
from benchmarks.categories.retrieval_bench import RetrievalBenchmark
from benchmarks.categories.hallucination_bench import HallucinationBenchmark

__all__ = [
    'AccuracyBenchmark',
    'CompressionBenchmark',
    'LatencyBenchmark',
    'RetrievalBenchmark',
    'HallucinationBenchmark',
]
