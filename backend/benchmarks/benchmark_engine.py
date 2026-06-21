"""
Benchmark Engine
================

Main orchestrator for AMDI-OS benchmarks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .accuracy import AccuracyBenchmark, AccuracyResult
from .precision_recall import PrecisionRecallBenchmark, PrecisionRecallResult
from .latency import LatencyBenchmark, LatencyResult
from .memory_tracker import MemoryTracker, MemoryResult
from .token_usage import TokenUsageBenchmark, TokenResult
from .cost import CostBenchmark, CostResult, CostModel
from .dataset_loader import BenchmarkDataset
from .metrics_aggregator import MetricsAggregator, AggregatedMetrics
from .report_generator import ReportGenerator, BenchmarkReport


@dataclass
class BenchmarkResult:
    """Results for a single document benchmark."""

    accuracy: AccuracyResult
    precision_recall: PrecisionRecallResult
    latency: LatencyResult
    memory: MemoryResult
    tokens: TokenResult
    cost: CostResult
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "accuracy": self.accuracy.to_dict(),
            "precision_recall": self.precision_recall.to_dict(),
            "latency": self.latency.to_dict(),
            "memory": self.memory.to_dict(),
            "tokens": self.tokens.to_dict(),
            "cost": self.cost.to_dict(),
            "metadata": self.metadata,
        }


@dataclass
class BenchmarkSuite:
    """A suite of benchmarks composed of datasets."""

    name: str
    datasets: List[BenchmarkDataset] = field(default_factory=list)
    results: Dict[str, BenchmarkResult] = field(default_factory=dict)

    def add_dataset(self, dataset: BenchmarkDataset) -> None:
        self.datasets.append(dataset)


class BenchmarkEngine:
    """Evaluates query pipeline correctness, speed, resources and cost."""

    def __init__(self, cost_model: Optional[CostModel] = None) -> None:
        self.accuracy_bench = AccuracyBenchmark()
        self.pr_bench = PrecisionRecallBenchmark()
        self.latency_bench = LatencyBenchmark(num_runs=3, warmup_runs=0)
        self.memory_tracker = MemoryTracker()
        self.token_bench = TokenUsageBenchmark()
        self.cost_bench = CostBenchmark(cost_model=cost_model)
        self.report_generator = ReportGenerator()

    def run_suite(
        self,
        suite: BenchmarkSuite,
        pipeline: Callable[[str], str],
        token_estimator: Optional[Callable[[str, str], tuple[int, int]]] = None,
    ) -> BenchmarkReport:
        """Execute benchmarking suite against a pipeline callable."""
        aggregator = MetricsAggregator()
        
        for dataset in suite.datasets:
            for gt in dataset.ground_truths:
                predictions = []
                expected_entries = gt.entries
                
                # Execute predictions
                def run_all_queries():
                    for entry in expected_entries:
                        ans = pipeline(entry.question)
                        predictions.append(ans)
                
                # Profile memory
                _, mem_res = self.memory_tracker.track(
                    f"run_{gt.document_id}",
                    run_all_queries
                )

                # Profile latency
                lat_res = self.latency_bench.benchmark(
                    lambda: [pipeline(entry.question) for entry in expected_entries],
                    operation_name=f"latency_{gt.document_id}"
                )

                # Profile accuracy
                acc_res = self.accuracy_bench.evaluate(predictions, expected_entries)

                # Profile precision/recall
                pred_sets = [set(p.split()) for p in predictions]
                exp_sets = [set(e.expected_answer.split()) for e in expected_entries]
                pr_res = self.pr_bench.evaluate(pred_sets, exp_sets)

                # Profile tokens & cost
                self.token_bench.reset()
                self.cost_bench.reset()
                for i, entry in enumerate(expected_entries):
                    pred = predictions[i]
                    in_t, out_t = (100, 50)  # default estimate
                    if token_estimator:
                        try:
                            in_t, out_t = token_estimator(entry.question, pred)
                        except Exception:
                            pass
                    self.token_bench.record(in_t, out_t)
                    self.cost_bench.record_query(in_t, out_t, compute_seconds=lat_res.stats.mean_ms / 1000.0)

                tok_res = self.token_bench.result()
                cost_res = self.cost_bench.compute()

                doc_result = BenchmarkResult(
                    accuracy=acc_res,
                    precision_recall=pr_res,
                    latency=lat_res,
                    memory=mem_res,
                    tokens=tok_res,
                    cost=cost_res,
                    metadata={"document_id": gt.document_id}
                )
                suite.results[gt.document_id] = doc_result
                aggregator.add_result(doc_result)

        aggregated = aggregator.aggregate()
        return self.report_generator.generate(suite.name, aggregated)
