'''
Master benchmark runner.
'''
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from benchmarks.framework.base import (
    BaseBenchmark, BenchmarkResult, BenchmarkReport, TestCase,
)
from benchmarks.statistics.significance import paired_t_test, cohens_d

logger = logging.getLogger('amdi.benchmarks.runner')


class BenchmarkRunner:
    '''Orchestrates benchmark execution and comparison.'''

    def __init__(self, output_dir: str = 'benchmarks/results'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reports: list[BenchmarkReport] = []

    async def run_category(
        self,
        name: str,
        baseline_benchmark: BaseBenchmark,
        amdi_benchmark: BaseBenchmark,
        test_cases: list[TestCase],
    ) -> BenchmarkReport:
        '''Run both baseline and AMDI on a category, compare.'''
        logger.info(f'Running benchmark category: {name}')
        # Run baseline
        logger.info('  Running baseline...')
        baseline_results = await baseline_benchmark.run(test_cases)
        baseline_benchmark.save_results(baseline_results)
        # Run AMDI
        logger.info('  Running AMDI-OS...')
        amdi_results = await amdi_benchmark.run(test_cases)
        amdi_benchmark.save_results(amdi_results)
        # Aggregate
        report = self._build_report(name, baseline_results, amdi_results)
        self._save_report(report)
        self.reports.append(report)
        return report

    def _build_report(
        self, name: str,
        baseline: list[BenchmarkResult],
        amdi: list[BenchmarkResult],
    ) -> BenchmarkReport:
        # Compute aggregate metrics per pipeline
        all_metrics = set()
        for r in baseline + amdi:
            all_metrics.update(r.metrics.keys())
        metrics_summary = {}
        for m in all_metrics:
            base_vals = [r.metrics[m] for r in baseline if m in r.metrics and isinstance(r.metrics[m], (int, float))]
            amdi_vals = [r.metrics[m] for r in amdi if m in r.metrics and isinstance(r.metrics[m], (int, float))]
            metrics_summary[m] = {
                'baseline': {
                    'mean': float(sum(base_vals) / len(base_vals)) if base_vals else 0.0,
                    'std': float(__import__('numpy').std(base_vals)) if base_vals else 0.0,
                    'n': len(base_vals),
                },
                'amdi': {
                    'mean': float(sum(amdi_vals) / len(amdi_vals)) if amdi_vals else 0.0,
                    'std': float(__import__('numpy').std(amdi_vals)) if amdi_vals else 0.0,
                    'n': len(amdi_vals),
                },
            }
        # Statistical tests
        stat_tests = {}
        improvement = {}
        for m in all_metrics:
            base_vals = [r.metrics[m] for r in baseline if m in r.metrics and isinstance(r.metrics[m], (int, float))]
            amdi_vals = [r.metrics[m] for r in amdi if m in r.metrics and isinstance(r.metrics[m], (int, float))]
            if len(base_vals) >= 3 and len(amdi_vals) >= 3 and len(base_vals) == len(amdi_vals):
                t_stat, p_value = paired_t_test(base_vals, amdi_vals)
                d = cohens_d(base_vals, amdi_vals)
                stat_tests[m] = {'t_stat': t_stat, 'p_value': p_value, 'cohens_d': d}
            if base_vals and amdi_vals:
                base_mean = sum(base_vals) / len(base_vals)
                amdi_mean = sum(amdi_vals) / len(amdi_vals)
                if base_mean != 0:
                    imp = (base_mean - amdi_mean) / abs(base_mean) * 100
                    improvement[m] = {
                        'baseline_mean': base_mean,
                        'amdi_mean': amdi_mean,
                        'improvement_pct': round(imp, 2),
                    }
        n_succ = sum(1 for r in amdi if r.success)
        return BenchmarkReport(
            name=name, n_tests=len(baseline), n_successful=n_succ,
            metrics_summary=metrics_summary,
            baseline_results=baseline, amdi_results=amdi,
            statistical_tests=stat_tests, improvement=improvement,
        )

    def _save_report(self, report: BenchmarkReport):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = self.output_dir / f'report_{report.name}_{ts}.json'
        with open(path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2, default=str)
        logger.info(f'Saved report: {path}')

    async def run_all(
        self,
        categories: list[tuple[str, BaseBenchmark, BaseBenchmark, list[TestCase]]],
    ) -> list[BenchmarkReport]:
        '''Run all benchmark categories sequentially.'''
        reports = []
        for name, baseline_bm, amdi_bm, tests in categories:
            try:
                report = await self.run_category(name, baseline_bm, amdi_bm, tests)
                reports.append(report)
            except Exception as e:
                logger.exception(f'Category {name} failed: {e}')
        # Final summary
        self._print_summary(reports)
        return reports

    def _print_summary(self, reports: list[BenchmarkReport]):
        print('\n' + '=' * 80)
        print(' AEGIS-AMDI-OS v1.0 — BENCHMARK SUMMARY')
        print('=' * 80)
        for r in reports:
            print(f'\n📊 {r.name.upper()}')
            for metric, data in r.metrics_summary.items():
                imp = r.improvement.get(metric, {})
                pct = imp.get('improvement_pct', 0.0)
                direction = '↓' if pct > 0 and metric not in ['accuracy', 'f1', 'precision', 'recall', 'citation_accuracy'] else '↑'
                print(f'   {metric:25} | Baseline: {data["baseline"]["mean"]:.3f}  →  AMDI: {data["amdi"]["mean"]:.3f}  ({direction} {abs(pct):.1f}%)')
            if r.statistical_tests:
                for m, t in list(r.statistical_tests.items())[:3]:
                    sig = '✓' if t['p_value'] < 0.05 else '✗'
                    print(f'      {sig} {m}: p={t["p_value"]:.4f}, d={t["cohens_d"]:.2f}')
        print('=' * 80)
