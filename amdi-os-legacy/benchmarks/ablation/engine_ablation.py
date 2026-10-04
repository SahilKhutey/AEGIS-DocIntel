'''
Phase 9: Engine Ablation Studies.
'''
from __future__ import annotations

import logging
from typing import Any

from benchmarks.framework.base import BenchmarkResult, TestCase
from benchmarks.amdi.amdi_pipeline import AMDIPipeline
from src.core.orchestrator import AMDIOrchestrator
from benchmarks.metrics.accuracy import answer_accuracy

logger = logging.getLogger('amdi.benchmarks.ablation')


def create_ablated_orchestrator(ablate_engine: str | None) -> type[AMDIOrchestrator]:
    '''Creates an orchestrator subclass with the specified engine disabled.'''
    class AblatedOrchestrator(AMDIOrchestrator):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            if not ablate_engine:
                return

            if ablate_engine == 'geometry':
                self._geometry = None
                if self._retriever:
                    self._retriever._geometry = None
            elif ablate_engine == 'recurrence':
                self._recurrence = None
                if self._retriever:
                    self._retriever._recurrence = None
            elif ablate_engine == 'frequency':
                self._frequency = None
                if self._retriever:
                    self._retriever._frequency = None
            elif ablate_engine == 'matrix':
                self._matrix = None
                if self._retriever:
                    self._retriever._matrix = None
            elif ablate_engine == 'template':
                self._template = None
                if self._retriever:
                    self._retriever._template = None
            elif ablate_engine == 'semantic':
                self._semantic = None
                if self._retriever:
                    self._retriever._semantic = None
            elif ablate_engine == 'graph':
                self._graph_eng = None
                if self._retriever:
                    self._retriever._graph = None

    return AblatedOrchestrator


class EngineAblation:
    '''Tests impact of each engine by disabling it during execution.'''

    ENGINES = [
        'geometry', 'recurrence', 'frequency', 'matrix',
        'template', 'graph', 'semantic'
    ]

    def __init__(self, pipeline: AMDIPipeline):
        self.pipeline = pipeline

    async def run(self, test_cases: list[TestCase]) -> dict[str, list[BenchmarkResult]]:
        '''Run ablation studies for all engines, returns dict mapping condition -> results.'''
        logger.info(f'Running engine ablation studies on {len(test_cases)} cases')
        ablation_results = {}

        # 1. Full System (AMDI baseline)
        logger.info('Running ablation: Full System (Control)')
        control_pipeline = AMDIPipeline(
            agent=self.pipeline.agent,
            model=self.pipeline.model,
            api_key=self.pipeline.api_key,
            **self.pipeline.kwargs
        )
        control_pipeline.orchestrator_class = create_ablated_orchestrator(None)
        control_results = await control_pipeline.run(test_cases)
        for r in control_results:
            r.pipeline = 'amdi_full'
            r.metrics['accuracy'] = answer_accuracy(r.answer, next(tc.ground_truth.expected_answer for tc in test_cases if tc.test_id == r.test_id))
        ablation_results['full'] = control_results

        # 2. Ablate each engine one by one
        for engine in self.ENGINES:
            logger.info(f'Running ablation: No {engine}')
            ablated_pipeline = AMDIPipeline(
                agent=self.pipeline.agent,
                model=self.pipeline.model,
                api_key=self.pipeline.api_key,
                **self.pipeline.kwargs
            )
            ablated_pipeline.orchestrator_class = create_ablated_orchestrator(engine)
            results = await ablated_pipeline.run(test_cases)
            
            for r in results:
                r.pipeline = f'amdi_no_{engine}'
                tc = next(t for t in test_cases if t.test_id == r.test_id)
                ans_acc = answer_accuracy(r.answer, tc.ground_truth.expected_answer)
                r.metrics['accuracy'] = ans_acc
                
            ablation_results[f'no_{engine}'] = results

        return ablation_results
