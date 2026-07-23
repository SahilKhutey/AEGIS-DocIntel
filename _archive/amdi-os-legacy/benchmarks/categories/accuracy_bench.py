'''
Phase 10: End-to-End Answer Accuracy Benchmark.
'''
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from benchmarks.framework.base import BaseBenchmark, BenchmarkResult, TestCase
from benchmarks.metrics.accuracy import (
    answer_accuracy, citation_accuracy, table_accuracy, hallucination_rate,
)

logger = logging.getLogger('amdi.benchmarks.categories.accuracy')


class AccuracyBenchmark(BaseBenchmark):
    '''Measures answer accuracy, citation accuracy, table accuracy, and F1 score.'''

    name = 'accuracy'
    description = 'Evaluates answer correctness, citation validity, and table extraction.'

    def __init__(self, pipeline: Any, output_dir: str = 'benchmarks/results'):
        super().__init__(output_dir)
        self.pipeline = pipeline

    async def run(self, test_cases: list[TestCase]) -> list[BenchmarkResult]:
        logger.info(f'Running accuracy benchmark on {len(test_cases)} cases')
        results = await self.pipeline.run(test_cases)
        
        for r, tc in zip(results, test_cases):
            if not r.success:
                continue
            
            # Read full document text to compute hallucination rate
            full_text = ''
            ext = Path(tc.document_path).suffix.lower()
            if ext == '.pdf':
                try:
                    import fitz
                    doc = fitz.open(tc.document_path)
                    full_text = '\n'.join(p.get_text() for p in doc)
                    doc.close()
                except ImportError:
                    pass
            
            if not full_text:
                try:
                    with open(tc.document_path, 'r', encoding='utf-8', errors='replace') as f:
                        full_text = f.read()
                except Exception:
                    full_text = ''

            # Answer Accuracy
            ans_acc = answer_accuracy(r.answer, tc.ground_truth.expected_answer)
            
            # Citation Accuracy
            cit_acc = citation_accuracy(
                r.answer, 
                tc.ground_truth.expected_pages, 
                tc.ground_truth.expected_citations
            )
            
            # Table Accuracy (extract expected numbers from expected tables or expected answer)
            expected_numbers = []
            for item in tc.ground_truth.expected_tables + [tc.ground_truth.expected_answer]:
                for m in re.finditer(r'\$?[\d,]+(?:\.\d+)?', item):
                    try:
                        val = float(m.group().replace('$', '').replace(',', ''))
                        expected_numbers.append(val)
                    except ValueError:
                        pass
            
            tab_acc = table_accuracy(r.answer, expected_numbers) if expected_numbers else 1.0
            
            # Hallucination Rate
            hall_r = hallucination_rate(r.answer, full_text) if full_text else 0.0

            # Update metrics
            r.metrics.update({
                'accuracy': ans_acc,
                'citation_accuracy': cit_acc,
                'table_accuracy': tab_acc,
                'hallucination_rate': hall_r,
                'f1': ans_acc,
            })
            
        self.results = results
        return results
