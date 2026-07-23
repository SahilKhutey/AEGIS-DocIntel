'''Query Workflow - End-to-end adaptive retrieval + reasoning.'''

from __future__ import annotations

import time
from typing import AsyncIterator

from src.engines.context import ContextBuilder
from src.engines.fusion import FusionEngine, QueryType
from src.engines.llm import LLMInterface
from src.engines.retrieval import HybridRetriever
from src.workflows.ingest_workflow import IngestWorkflow


class QueryWorkflow:
    '''
    Query pipeline with adaptive multi-layer retrieval.

    Flow:
    1. Receive query
    2. Classify query type (FusionEngine)
    3. Compute optimal layer weights
    4. Multi-signal retrieval (semantic + geometry + matrix + graph + ...)
    5. Adaptive fusion
    6. Token-budget aware context building
    7. LLM reasoning with citations
    8. Return answer with metadata
    '''

    def __init__(
        self,
        ingest: IngestWorkflow,
        llm_provider: str = 'openai',
        llm_model: str = 'gpt-4o-mini',
        llm_api_key: str = '',
        max_context_tokens: int = 6000,
    ):
        self.ingest = ingest
        self.llm = LLMInterface(
            llm_provider=llm_provider, model=llm_model, api_key=llm_api_key,
        )
        self.context_builder = ContextBuilder(max_tokens=max_context_tokens)
        self.fusion = FusionEngine()

    async def query(
        self,
        question: str,
        top_k: int = 8,
        stream: bool = False,
    ) -> dict:
        '''Run query pipeline.'''
        t0 = time.perf_counter()
        if not self.ingest._elements:
            raise RuntimeError('No document ingested. Call ingest first.')
        state = self.ingest.get_state()
        elements = state['elements']
        tables = state['tables']
        graph = state['graph']

        # Build retriever on-demand (allows state refresh)
        retriever = HybridRetriever(
            embedder=state['embedder'],
            vector_store=state['vector_store'],
            geometry=state['geometry'],
            recurrence=state['recurrence'],
            frequency=state['frequency'],
            matrix=state['matrix'],
            template=state['template'],
            graph=graph,
        )

        # Retrieve
        hits, _, query_type_str = await retriever.retrieve(question, elements, top_k)

        # Map query_type
        try:
            query_type = QueryType(query_type_str)
        except ValueError:
            query_type = QueryType.UNKNOWN

        # Get weights
        weights, _, _ = self.fusion.compute_weights(question)

        # Build context
        context = self.context_builder.build(
            question=question,
            hits=hits,
            elements=elements,
            tables=tables,
            graph=graph,
        )

        # LLM
        if stream:
            return await self._stream_response(context, hits, weights, query_type, t0)
        else:
            llm_out = await self.llm.reason(context)
            elapsed = time.perf_counter() - t0
            return {
                'question': question,
                'answer': llm_out['answer'],
                'query_type': query_type.value,
                'dominant_layer': weights.dominant(),
                'weights': weights.to_dict(),
                'input_tokens': llm_out['input_tokens'],
                'output_tokens': llm_out['output_tokens'],
                'context_tokens': context['tokens_used'],
                'selected_elements': len(context['selected_ids']),
                'top_hits': [
                    {'element_id': h.element.element_id if hasattr(h, 'element') else getattr(h, 'element_id', ''),
                     'page': h.element.page if hasattr(h, 'element') else getattr(h, 'page', 0),
                     'score': h.score if hasattr(h, 'score') else getattr(h, 'final_score', 0.0)}
                    for h in hits[:5]
                ],
                'latency_s': round(elapsed, 3),
            }

    async def _stream_response(self, context, hits, weights, qt, t0):
        async def gen():
            yield f'data: {{"query_type": "{qt.value}", "dominant_layer": "{weights.dominant()}"}}\n\n'
            async for token in self.llm.stream(context):
                yield f'data: {{"token": {repr(token)}}}\n\n'
            yield 'data: [DONE]\n\n'
        return gen()

    async def stream(self, question: str, top_k: int = 8) -> AsyncIterator[str]:
        '''Stream response.'''
        state = self.ingest.get_state()
        elements = state['elements']
        tables = state['tables']
        graph = state['graph']
        retriever = HybridRetriever(
            embedder=state['embedder'],
            vector_store=state['vector_store'],
            geometry=state['geometry'],
            recurrence=state['recurrence'],
            frequency=state['frequency'],
            matrix=state['matrix'],
            template=state['template'],
            graph=graph,
        )
        hits, _, _ = await retriever.retrieve(question, elements, top_k)
        context = self.context_builder.build(
            question=question, hits=hits, elements=elements,
            tables=tables, graph=graph,
        )
        async for token in self.llm.stream(context):
            yield token
