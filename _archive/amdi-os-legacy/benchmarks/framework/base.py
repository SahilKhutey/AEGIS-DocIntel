'''
Base classes and schemas for benchmarks.
'''
from __future__ import annotations

import abc
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BenchmarkStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'


@dataclass
class GroundTruth:
    '''Ground truth for a single test case.'''
    question: str
    expected_answer: str
    expected_pages: list[int] = field(default_factory=list)
    expected_tables: list[str] = field(default_factory=list)
    expected_citations: list[dict] = field(default_factory=list)
    expected_relations: list[tuple[str, str]] = field(default_factory=list)
    difficulty: str = 'medium'  # easy, medium, hard
    category: str = 'general'   # numerical, semantic, structural, etc.
    metadata: dict = field(default_factory=dict)


@dataclass
class TestCase:
    '''A single test case with document + ground truth.'''
    test_id: str
    document_path: str
    document_type: str  # invoice, paper, manual, etc.
    ground_truth: GroundTruth
    metadata: dict = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    '''Result of a single benchmark run.'''
    test_id: str
    pipeline: str  # 'baseline' or 'amdi'
    success: bool
    answer: str = ''
    metrics: dict = field(default_factory=dict)
    latency_s: float = 0.0
    tokens_used: int = 0
    cost_usd: float = 0.0
    error: str | None = None
    timestamp: float = field(default_factory=time.time)
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'test_id': self.test_id,
            'pipeline': self.pipeline,
            'success': self.success,
            'answer': self.answer[:500],
            'metrics': self.metrics,
            'latency_s': self.latency_s,
            'tokens_used': self.tokens_used,
            'cost_usd': self.cost_usd,
            'error': self.error,
            'timestamp': self.timestamp,
        }


@dataclass
class BenchmarkReport:
    '''Aggregated report for a benchmark category.'''
    name: str
    n_tests: int
    n_successful: int
    metrics_summary: dict
    baseline_results: list[BenchmarkResult]
    amdi_results: list[BenchmarkResult]
    statistical_tests: dict = field(default_factory=dict)
    improvement: dict = field(default_factory=dict)
    generated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'n_tests': self.n_tests,
            'n_successful': self.n_successful,
            'metrics_summary': self.metrics_summary,
            'statistical_tests': self.statistical_tests,
            'improvement': self.improvement,
            'baseline_n': len(self.baseline_results),
            'amdi_n': len(self.amdi_results),
            'generated_at': self.generated_at,
        }


class BaseBenchmark(abc.ABC):
    '''Abstract base for all benchmark categories.'''

    name: str = 'base'
    description: str = ''

    def __init__(self, output_dir: str = 'benchmarks/results'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: list[BenchmarkResult] = []

    @abc.abstractmethod
    async def run(self, test_cases: list[TestCase]) -> list[BenchmarkResult]:
        '''Run the benchmark on test cases.'''
        raise NotImplementedError

    def save_results(self, results: list[BenchmarkResult] | None = None):
        results = results or self.results
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = self.output_dir / f'{self.name}_{ts}.jsonl'
        with open(path, 'w') as f:
            for r in results:
                f.write(json.dumps(r.to_dict()) + '\n')
        logger.info(f'Saved {len(results)} results to {path}')
        return path
