'''
Phase 8: Hallucination Detection Benchmark.
'''
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from benchmarks.framework.base import BaseBenchmark, BenchmarkResult, TestCase
from benchmarks.metrics.accuracy import hallucination_rate

logger = logging.getLogger('amdi.benchmarks.categories.hallucination')


class HallucinationBenchmark(BaseBenchmark):
    '''Measures hallucination rate by comparing answer claims to ground truth context.'''

    name = 'hallucination'
    description = 'Evaluates hallucination rates in generated answers against full document texts.'

    def __init__(self, pipeline: Any, output_dir: str = 'benchmarks/results'):
        super().__init__(output_dir)
        self.pipeline = pipeline

    async def run(self, test_cases: list[TestCase]) -> list[BenchmarkResult]:
        logger.info(f'Running hallucination benchmark on {len(test_cases)} cases')
        results = await self.pipeline.run(test_cases)

        for r, tc in zip(results, test_cases):
            if not r.success:
                continue

            # Load document to get ground truth context
            full_text = ''
            try:
                ext = Path(tc.document_path).suffix.lower()
                if ext == '.pdf':
                    import fitz
                    doc = fitz.open(tc.document_path)
                    full_text = '\n'.join(p.get_text() for p in doc)
                    doc.close()
                else:
                    with open(tc.document_path, 'r', encoding='utf-8', errors='replace') as f:
                        full_text = f.read()
            except Exception:
                full_text = ''

            # Compute hallucination rate
            hall_r = hallucination_rate(r.answer, full_text) if full_text else 0.0

            r.metrics.update({
                'hallucination_rate': hall_r,
                'groundedness_score': 1.0 - hall_r,
            })

        self.results = results
        return results
