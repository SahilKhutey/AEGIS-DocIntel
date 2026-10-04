'''
Unit tests for the AMDI-OS Benchmarking & Validation Framework.
'''
from __future__ import annotations

import asyncio
from pathlib import Path
import tempfile
import pytest

from benchmarks.metrics.accuracy import (
    answer_accuracy, citation_accuracy, table_accuracy, hallucination_rate,
)
from benchmarks.metrics.retrieval import (
    precision_at_k, recall_at_k, mrr, ndcg_at_k, hit_rate,
)
from benchmarks.metrics.compression import (
    compression_ratio, compression_percentage, token_reduction, information_retention,
)
from benchmarks.statistics.significance import (
    paired_t_test, cohens_d, confidence_interval, calibration_error,
)
from benchmarks.framework.base import TestCase, GroundTruth
from benchmarks.baseline.token_rag import TokenRAGBaseline
from benchmarks.amdi.amdi_pipeline import AMDIPipeline
from benchmarks.categories.accuracy_bench import AccuracyBenchmark
from benchmarks.categories.compression_bench import CompressionBenchmark
from benchmarks.framework.runner import BenchmarkRunner


def test_accuracy_metrics() -> None:
    '''Tests calculations of the answer, citation, and table accuracy metrics.'''
    # Answer accuracy (token-level F1)
    assert answer_accuracy('Hello world', 'Hello world') == 1.0
    assert answer_accuracy('Hello', 'World') == 0.0
    assert round(answer_accuracy('the quantum computing', 'quantum computing'), 1) == 0.8
    
    # Citation accuracy (overlap of cited pages)
    assert citation_accuracy('See page 1 and page 2', [1, 2], []) == 1.0
    assert citation_accuracy('See page 1', [1, 2], []) == 0.5
    assert citation_accuracy('No citations', [1], []) == 0.0

    # Table accuracy (comparison of numeric values found vs expected)
    assert table_accuracy('The total is $125.50 and profit is $50', [125.5, 50.0]) == 1.0
    assert table_accuracy('The total is $50.00', [125.5]) == 0.0
    assert table_accuracy('No numbers', [10.0]) == 0.0


def test_retrieval_metrics() -> None:
    '''Tests retrieval quality metrics (Precision, Recall, MRR, NDCG).'''
    retrieved = ['1', '2', '3', '4', '5']
    relevant = ['2', '5']

    assert precision_at_k(retrieved, relevant, 5) == 0.4
    assert recall_at_k(retrieved, relevant, 5) == 1.0
    assert mrr(retrieved, relevant) == 0.5
    assert ndcg_at_k(retrieved, relevant, 5) > 0.0
    assert hit_rate(retrieved, relevant) == 1.0


def test_compression_metrics() -> None:
    '''Tests document compression and token reduction calculations.'''
    assert compression_ratio(250, 1000) == 0.25
    assert compression_percentage(250, 1000) == 75.0
    assert token_reduction(1000, 300) == 70.0
    assert information_retention(950, 1000) == 0.95


def test_significance_tests() -> None:
    '''Tests statistical significance helpers.'''
    baseline = [0.8, 0.75, 0.85, 0.9, 0.7]
    amdi = [0.95, 0.9, 0.98, 0.96, 0.92]

    t_stat, p_val = paired_t_test(baseline, amdi)
    assert p_val < 0.05  # Should be significant improvement
    assert cohens_d(baseline, amdi) > 1.0  # Large effect size

    ci_low, ci_high = confidence_interval(amdi)
    assert ci_low < ci_high

    # Calibration error
    confs = [0.9, 0.8, 0.7, 0.6]
    accs = [1.0, 1.0, 0.0, 1.0]
    ece = calibration_error(confs, accs, n_bins=2)
    assert 0.0 <= ece <= 1.0


@pytest.mark.asyncio
async def test_benchmark_runner_flow() -> None:
    '''Tests the complete benchmark runner loop with mock pipelines.'''
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        doc_file = temp_path / 'mock_doc.txt'
        doc_file.write_text('Line 1: Quantum decoherence\nLine 2: System fidelity\n', encoding='utf-8')

        tc = TestCase(
            test_id='test_mock_01',
            document_path=str(doc_file),
            document_type='test',
            ground_truth=GroundTruth(
                question='What is the fidelity?',
                expected_answer='System fidelity',
                expected_pages=[1],
            )
        )

        baseline_pipe = TokenRAGBaseline(api_key='EMPTY')
        amdi_pipe = AMDIPipeline(agent='chatgpt', model='mock', api_key='EMPTY')

        runner = BenchmarkRunner(output_dir=str(temp_path / 'results'))

        accuracy_baseline = AccuracyBenchmark(baseline_pipe)
        accuracy_amdi = AccuracyBenchmark(amdi_pipe)

        report = await runner.run_category('accuracy', accuracy_baseline, accuracy_amdi, [tc])
        
        assert report.n_tests == 1
        assert report.name == 'accuracy'
        assert len(report.baseline_results) == 1
        assert len(report.amdi_results) == 1
        assert report.baseline_results[0].success
        assert report.amdi_results[0].success

        # Check report files saved
        report_files = list((temp_path / 'results').glob('report_accuracy_*.json'))
        assert len(report_files) == 1
