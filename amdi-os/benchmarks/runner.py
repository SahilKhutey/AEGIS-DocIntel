'''
Master benchmark execution runner.
'''
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from benchmarks.framework.base import TestCase, GroundTruth
from benchmarks.framework.runner import BenchmarkRunner
from benchmarks.baseline.token_rag import TokenRAGBaseline
from benchmarks.amdi.amdi_pipeline import AMDIPipeline
from benchmarks.categories.accuracy_bench import AccuracyBenchmark
from benchmarks.categories.compression_bench import CompressionBenchmark
from benchmarks.categories.latency_bench import LatencyBenchmark
from benchmarks.categories.retrieval_bench import RetrievalBenchmark
from benchmarks.categories.hallucination_bench import HallucinationBenchmark
from benchmarks.ablation.engine_ablation import EngineAblation

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('amdi.benchmarks.runner_script')


def ensure_mock_datasets(base_dir: Path) -> list[TestCase]:
    '''Generates mock documents and returns a list of TestCases.'''
    dataset_dir = base_dir / 'datasets'
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # 1. Scientific Paper
    paper_path = dataset_dir / 'scientific_paper.txt'
    if not paper_path.exists():
        paper_text = (
            'Page 1: Introduction to Quantum Error Correction\n'
            'Quantum computing promises exponential speedup. However, qubits are prone to decoherence.\n\n'
            'Page 2: Shor\'s Algorithm and Methods\n'
            'Shor\'s algorithm is a quantum algorithm for integer factorization in polynomial time.\n'
            'It finds prime factors of an integer N in O((log N)^3) operations.\n\n'
            'Page 3: Experimental Results\n'
            'We demonstrated the layout in a superconducting loop showing 99.8% fidelity.\n'
        )
        paper_path.write_text(paper_text, encoding='utf-8')

    # 2. Invoice
    invoice_path = dataset_dir / 'invoice_acme.txt'
    if not invoice_path.exists():
        invoice_text = (
            'ACME Corporation\n'
            'Bill To: AEGIS Research Lab\n'
            'Invoice Date: 2026-06-19\n\n'
            'Items:\n'
            '1. Standard License - $5,000.00\n'
            '2. Support Package  - $2,500.00\n'
            '3. Custom Integration - $5,000.00\n\n'
            'Total Amount Due: $12,500.00\n'
            'Please pay within 30 days.\n'
        )
        invoice_path.write_text(invoice_text, encoding='utf-8')

    # 3. Operations Manual
    manual_path = dataset_dir / 'router_manual.txt'
    if not manual_path.exists():
        manual_text = (
            'AEGIS-Router v10 User Guide\n'
            'Page 1: Installation\n'
            'Connect the WAN port to your modem. Use the yellow LAN ports for local devices.\n\n'
            'Page 2: Default Configuration\n'
            'Open http://192.168.1.1 in your browser.\n'
            'The default username is admin.\n'
            'The default password is admin123.\n'
        )
        manual_path.write_text(manual_text, encoding='utf-8')

    test_cases = [
        TestCase(
            test_id='test_paper_01',
            document_path=str(paper_path),
            document_type='scientific_paper',
            ground_truth=GroundTruth(
                question='What is Shor\'s algorithm used for?',
                expected_answer='integer factorization',
                expected_pages=[2],
                difficulty='easy',
                category='semantic',
            )
        ),
        TestCase(
            test_id='test_invoice_01',
            document_path=str(invoice_path),
            document_type='invoice',
            ground_truth=GroundTruth(
                question='What is the total amount due on the invoice?',
                expected_answer='$12,500.00',
                expected_pages=[1],
                expected_tables=['$12,500.00'],
                difficulty='easy',
                category='numerical',
            )
        ),
        TestCase(
            test_id='test_manual_01',
            document_path=str(manual_path),
            document_type='manual',
            ground_truth=GroundTruth(
                question='What is the default password for the router?',
                expected_answer='admin123',
                expected_pages=[2],
                difficulty='medium',
                category='entity',
            )
        ),
    ]

    return test_cases


async def run_suite(api_key: str, model: str, run_ablation: bool) -> int:
    '''Runs the full validation suite and returns exit code.'''
    t_start = time.perf_counter()
    bench_dir = Path(__file__).resolve().parent
    test_cases = ensure_mock_datasets(bench_dir)

    logger.info('Initializing Baseline and AMDI pipelines...')
    baseline_pipe = TokenRAGBaseline(api_key=api_key, model=model)
    amdi_pipe = AMDIPipeline(agent='chatgpt', model=model, api_key=api_key)

    runner = BenchmarkRunner(output_dir=str(bench_dir / 'results'))

    # Category 1: Accuracy
    logger.info('Starting Category: Accuracy')
    accuracy_baseline = AccuracyBenchmark(baseline_pipe)
    accuracy_amdi = AccuracyBenchmark(amdi_pipe)
    await runner.run_category('accuracy', accuracy_baseline, accuracy_amdi, test_cases)

    # Category 2: Compression
    logger.info('Starting Category: Compression')
    comp_baseline = CompressionBenchmark(baseline_pipe)
    comp_amdi = CompressionBenchmark(amdi_pipe)
    await runner.run_category('compression', comp_baseline, comp_amdi, test_cases)

    # Category 3: Latency
    logger.info('Starting Category: Latency')
    lat_baseline = LatencyBenchmark(baseline_pipe)
    lat_amdi = LatencyBenchmark(amdi_pipe)
    await runner.run_category('latency', lat_baseline, lat_amdi, test_cases)

    # Category 4: Retrieval
    logger.info('Starting Category: Retrieval')
    ret_baseline = RetrievalBenchmark(baseline_pipe)
    ret_amdi = RetrievalBenchmark(amdi_pipe)
    await runner.run_category('retrieval', ret_baseline, ret_amdi, test_cases)

    # Category 5: Hallucination
    logger.info('Starting Category: Hallucination')
    hall_baseline = HallucinationBenchmark(baseline_pipe)
    hall_amdi = HallucinationBenchmark(amdi_pipe)
    await runner.run_category('hallucination', hall_baseline, hall_amdi, test_cases)

    # Option: Run ablation studies
    if run_ablation:
        logger.info('Starting Ablation Studies...')
        ablation = EngineAblation(amdi_pipe)
        ablation_results = await ablation.run(test_cases)
        
        # Save ablation results
        ablation_dir = bench_dir / 'results'
        ablation_dir.mkdir(parents=True, exist_ok=True)
        import json
        ablation_path = ablation_dir / 'ablation_report.json'
        serializable_ablation = {}
        for cond, res_list in ablation_results.items():
            serializable_ablation[cond] = [r.to_dict() for r in res_list]
            
        with open(ablation_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_ablation, f, indent=2)
        logger.info(f'Saved ablation report to {ablation_path}')

        # Print ablation summary
        print('\n' + '=' * 80)
        print(' AEGIS-AMDI-OS v1.0 — ABLATION SUMMARY')
        print('=' * 80)
        for cond, res_list in ablation_results.items():
            avg_acc = np.mean([r.metrics.get('accuracy', 0.0) for r in res_list])
            print(f'   {cond:15} | Average Answer Accuracy: {avg_acc:.3f}')
        print('=' * 80)

    elapsed = time.perf_counter() - t_start
    logger.info(f'Benchmark suite completed in {elapsed:.2f} seconds')
    return 0


def main() -> None:
    '''CLI entry point.'''
    parser = argparse.ArgumentParser(description='AMDI-OS Benchmark Suite')
    parser.add_argument('--api-key', type=str, default='', help='LLM Provider API Key (default: empty for mocks)')
    parser.add_argument('--model', type=str, default='gpt-4o-mini', help='LLM model name')
    parser.add_argument('--ablation', action='store_true', help='Run engine ablation studies')

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    sys.exit(loop.run_until_complete(run_suite(args.api_key, args.model, args.ablation)))


if __name__ == '__main__':
    main()
