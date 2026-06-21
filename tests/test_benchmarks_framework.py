import os
import sys
import tempfile
from pathlib import Path
import numpy as np
import pytest
from unittest.mock import MagicMock

# Configure Python path to find backend.benchmarks
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def test_benchmarks_imports():
    """Verify that all components can be imported from backend.benchmarks."""
    from backend.benchmarks import (
        BenchmarkEngine,
        BenchmarkResult,
        BenchmarkSuite,
        AccuracyBenchmark,
        AccuracyResult,
        PrecisionRecallBenchmark,
        PrecisionRecallResult,
        F1Result,
        LatencyBenchmark,
        LatencyResult,
        LatencyStats,
        MemoryTracker,
        MemoryResult,
        TokenUsageBenchmark,
        TokenResult,
        CostBenchmark,
        CostResult,
        CostModel,
        GroundTruth,
        GroundTruthEntry,
        DatasetLoader,
        BenchmarkDataset,
        MetricsAggregator,
        AggregatedMetrics,
        ReportGenerator,
        BenchmarkReport,
        BaselineComparator,
        BaselineResult,
        StatisticalTests,
        SignificanceResult,
        BenchmarkError,
        DatasetMissingError,
        MetricComputationError,
    )
    assert True


def test_exceptions():
    """Verify exceptions raise and catch properly."""
    from backend.benchmarks.exceptions import (
        BenchmarkError,
        DatasetMissingError,
        MetricComputationError,
        BaselineMismatchError,
        GroundTruthError,
    )
    
    with pytest.raises(DatasetMissingError):
        raise DatasetMissingError("Missing dataset")
    
    with pytest.raises(BenchmarkError):
        raise GroundTruthError("Ground truth error")


def test_ground_truth():
    """Verify GroundTruthEntry serialization and file operations."""
    from backend.benchmarks.ground_truth import GroundTruth, GroundTruthEntry

    entry = GroundTruthEntry(
        question="What is gravity?",
        expected_answer="An attractive force.",
        expected_pages=[1, 2],
        category="physics",
        difficulty="easy"
    )
    
    gt = GroundTruth(
        document_id="doc-123",
        document_path="path/to/doc.pdf",
        document_type="scientific_papers",
        entries=[entry]
    )
    
    assert gt.entries[0].question == "What is gravity?"
    assert len(gt.get_by_category("physics")) == 1
    assert len(gt.get_by_difficulty("easy")) == 1
    
    # Save and Load check
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_name = tmp.name
    try:
        gt.to_file(tmp_name)
        loaded = GroundTruth.from_file(tmp_name)
        assert loaded.document_id == "doc-123"
        assert loaded.entries[0].question == "What is gravity?"
    finally:
        os.remove(tmp_name)


def test_dataset_loader():
    """Verify DatasetLoader Synthetic generation."""
    from backend.benchmarks.dataset_loader import DatasetLoader

    loader = DatasetLoader()
    # Test synthetic load
    ds = loader.load_synthetic("scientific_papers", n_documents=2, questions_per_doc=3)
    assert ds.name == "synthetic_scientific_papers"
    assert len(ds.document_paths) == 2
    assert len(ds.ground_truths) == 2
    assert ds.total_questions() == 6


def test_accuracy_metrics():
    """Verify AccuracyBenchmark calculations for exact, token, and cosine similarities."""
    from backend.benchmarks.accuracy import AccuracyBenchmark, AccuracyResult
    from backend.benchmarks.ground_truth import GroundTruthEntry

    gt = [
        GroundTruthEntry("Q1", "The quick brown fox", category="test", difficulty="easy"),
        GroundTruthEntry("Q2", "Jumped over the dog", category="test", difficulty="medium")
    ]
    
    # Exact Match
    bench_exact = AccuracyBenchmark(method="exact")
    res_exact = bench_exact.evaluate(["the quick brown fox", "Jumped over the dog"], gt)
    assert res_exact.accuracy == 1.0
    
    res_exact_fail = bench_exact.evaluate(["quick brown fox", "Jumped over"], gt)
    assert res_exact_fail.accuracy == 0.0

    # Token F1
    bench_token = AccuracyBenchmark(method="token_f1", threshold=0.5)
    res_token = bench_token.evaluate(["quick brown fox", "Jumped over the dog"], gt)
    # Fox overlap: prediction is 3 tokens, expected is 4. Overlap tokens: "quick", "brown", "fox". 
    # Precision = 3/3 = 1.0, Recall = 3/4 = 0.75, F1 = 2 * 1 * 0.75 / 1.75 = 1.5 / 1.75 = 0.857 >= 0.5 (True)
    # Dog overlap: prediction is 4 tokens, expected is 4. F1 = 1.0 >= 0.5 (True)
    assert res_token.accuracy == 1.0

    # Semantic similarity mock
    mock_embed = MagicMock(return_value=np.array([1.0, 0.0]))
    bench_semantic = AccuracyBenchmark(method="semantic", threshold=0.8, embedding_fn=mock_embed)
    res_sem = bench_semantic.evaluate(["quick brown", "dog"], gt)
    # cosine similarity of mock vectors will be 1.0 >= 0.8
    assert res_sem.accuracy == 1.0


def test_precision_recall_metrics():
    """Verify PrecisionRecallBenchmark metrics."""
    from backend.benchmarks.precision_recall import PrecisionRecallBenchmark

    bench = PrecisionRecallBenchmark()
    
    preds = [set(["apple", "banana", "orange"])]
    exps = [set(["apple", "banana", "grape"])]
    
    res = bench.evaluate(preds, exps, categories=["fruits"])
    assert res.precision == pytest.approx(2.0 / 3.0)
    assert res.recall == pytest.approx(2.0 / 3.0)
    assert res.f1 == pytest.approx(2.0 / 3.0)
    assert res.per_category["fruits"]["f1"] == pytest.approx(2.0 / 3.0)

    # Multi-class F1
    y_true = ["cat", "dog", "cat", "bird"]
    y_pred = ["cat", "dog", "dog", "bird"]
    f1_res = bench.evaluate_classification(y_true, y_pred)
    assert f1_res.micro_f1 == pytest.approx(0.75)  # 3 correct out of 4


def test_latency_metrics():
    """Verify LatencyBenchmark measurement and distribution statistics."""
    from backend.benchmarks.latency import LatencyBenchmark

    bench = LatencyBenchmark(num_runs=5, warmup_runs=1)
    
    # Run latency test on dummy wait function
    import time
    res = bench.benchmark(lambda: time.sleep(0.01), "sleep_test")
    assert res.operation == "sleep_test"
    assert res.num_runs == 5
    assert res.stats.mean_ms >= 5.0  # sleep should be around 10ms, at least 5ms
    assert res.stats.p50_ms >= 5.0
    assert res.stats.coefficient_of_variation >= 0.0

    # Async timing
    res_async = bench.benchmark_async(lambda: time.sleep(0.005), "async_sleep")
    assert res_async.num_runs == 5


def test_memory_tracker():
    """Verify MemoryTracker snapshots and function profiling."""
    from backend.benchmarks.memory_tracker import MemoryTracker

    tracker = MemoryTracker()
    
    # Snapshot
    snap = tracker.snapshot()
    assert snap.rss_mb >= 0.0
    
    # Track
    ret, mem_res = tracker.track("test_ops", lambda x: x * 2, 5)
    assert ret == 10
    assert mem_res.initial_mb >= 0.0
    assert mem_res.peak_mb >= 0.0
    assert len(mem_res.snapshots) > 0


def test_token_usage_metrics():
    """Verify TokenUsageBenchmark usage recording and pricing calculations."""
    from backend.benchmarks.token_usage import TokenUsageBenchmark

    tracker = TokenUsageBenchmark()
    tracker.record(500, 100, engine="semantic", section="retrieval")
    tracker.record(1000, 400, engine="llm", section="reasoning")
    tracker.set_baseline(3000)

    res = tracker.result()
    assert res.total_input_tokens == 1500
    assert res.total_output_tokens == 500
    assert res.total_tokens == 2000
    assert res.average_per_query == 1000.0
    # savings = 1.0 - 2000 / 3000 = 33.3%
    assert res.savings_vs_baseline == pytest.approx(1.0 / 3.0)

    # Cost estimation helper
    cost_val = TokenUsageBenchmark.estimate_cost(1000, 500, "chatgpt-4o")
    # input = 1000 * 0.005 / 1000 = 0.005. output = 500 * 0.015 / 1000 = 0.0075. total = 0.0125
    assert cost_val == 0.0125


def test_cost_metrics():
    """Verify CostBenchmark compute, storage and total cost summaries."""
    from backend.benchmarks.cost import CostBenchmark, CostModel

    model = CostModel(
        input_price_per_1k=0.010,
        output_price_per_1k=0.030,
        compute_price_per_hour=0.50,
        storage_price_per_gb_month=0.10
    )
    
    bench = CostBenchmark(cost_model=model)
    bench.record_query(2000, 500, compute_seconds=36.0)  # 36 sec = 0.01 hours
    bench.set_storage(5.0)  # 5 GB

    res = bench.compute()
    # token cost: (2 * 0.01) + (0.5 * 0.03) = 0.02 + 0.015 = 0.035
    assert res.token_cost_usd == pytest.approx(0.035)
    # compute cost: 36/3600 * 0.50 = 0.01 * 0.50 = 0.005
    assert res.compute_cost_usd == pytest.approx(0.005)
    # storage cost: 5.0 * 0.10 = 0.50
    assert res.storage_cost_usd == pytest.approx(0.50)
    # total cost = 0.035 + 0.005 + 0.50 = 0.54
    assert res.total_cost_usd == pytest.approx(0.54)


def test_baseline_comparator():
    """Verify BaselineComparator calculations."""
    from backend.benchmarks.baseline import BaselineComparator

    comp = BaselineComparator()
    baseline = {"accuracy": 0.60, "latency_ms": 1500.0, "tokens": 5000, "cost_usd": 0.05}
    amdi = {"accuracy": 0.85, "latency_ms": 500.0, "tokens": 1000, "cost_usd": 0.01}

    res = comp.compare("vanilla_rag", baseline, amdi, num_questions=10)
    assert res.accuracy_improvement == pytest.approx(0.25)
    assert res.relative_improvement == pytest.approx(0.25 / 0.60)
    # latency change: (500 - 1500)/1500 * 100 = -66.6%
    assert res.latency_change_pct == pytest.approx(-200.0 / 3.0)
    # token reduction: (5000 - 1000)/5000 * 100 = 80%
    assert res.token_reduction_pct == pytest.approx(80.0)


def test_statistical_tests():
    """Verify StatisticalTests paired t-test and Wilcoxon rankings."""
    from backend.benchmarks.statistical_tests import StatisticalTests

    a = [0.8, 0.9, 0.85, 0.95, 0.9, 0.8, 0.9, 0.85, 0.95, 0.9]
    b = [0.6, 0.7, 0.65, 0.75, 0.7, 0.6, 0.7, 0.65, 0.75, 0.7]

    res_t = StatisticalTests.paired_ttest(a, b)
    assert res_t.test_name == "paired_t_test"
    assert res_t.p_value < 0.05  # highly significant difference
    assert res_t.significant is True

    res_w = StatisticalTests.wilcoxon_signed_rank(a, b)
    assert res_w.test_name == "wilcoxon_signed_rank"
    assert res_w.p_value < 0.05
    assert res_w.significant is True


def test_metrics_aggregator_and_reports():
    """Verify MetricsAggregator combines results and ReportGenerator produces MD."""
    from backend.benchmarks.metrics_aggregator import MetricsAggregator
    from backend.benchmarks.report_generator import ReportGenerator
    
    # Mock some single document result structures
    mock_res = MagicMock()
    mock_res.accuracy.accuracy = 0.80
    mock_res.precision_recall.precision = 0.82
    mock_res.precision_recall.recall = 0.78
    mock_res.precision_recall.f1 = 0.80
    mock_res.latency.stats.mean_ms = 120.0
    mock_res.memory.peak_mb = 150.0
    mock_res.tokens.total_tokens = 1500
    mock_res.cost.total_cost_usd = 0.02
    
    agg = MetricsAggregator()
    agg.add_result(mock_res)
    
    aggregated = agg.aggregate()
    assert aggregated.accuracy == 0.80
    assert aggregated.latency_mean_ms == 120.0
    assert aggregated.memory_peak_mb == 150.0
    assert aggregated.total_tokens == 1500

    # Report Generator
    rep_gen = ReportGenerator()
    report = rep_gen.generate("Standard Suite", aggregated)
    assert report.suite_name == "Standard Suite"
    
    md = report.to_markdown()
    assert "# AMDI-OS Benchmark Report" in md
    assert "Mean Latency" in md


def test_benchmark_engine():
    """Verify BenchmarkEngine runner orchestrator execution."""
    from backend.benchmarks.benchmark_engine import BenchmarkEngine, BenchmarkSuite
    from backend.benchmarks.dataset_loader import DatasetLoader

    loader = DatasetLoader()
    ds = loader.load_synthetic("scientific_papers", n_documents=1, questions_per_doc=2)
    
    suite = BenchmarkSuite(name="Suite A")
    suite.add_dataset(ds)

    engine = BenchmarkEngine()
    
    # Run engine on dummy pipeline callable returning static answer
    report = engine.run_suite(suite, pipeline=lambda q: "Expected answer about quantum gravity.")
    assert report.suite_name == "Suite A"
    assert report.aggregated.num_runs == 1
    assert len(suite.results) == 1
