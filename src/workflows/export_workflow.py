'''Export Workflow - Send optimized context to any AI agent.'''

from __future__ import annotations

import json
import time
from typing import Any

from loguru import logger

from src.ael.ueo import (
    UniversalExportObject, Metadata, DocumentSummary,
    SemanticLayer, GeometryLayer, MatrixLayer, GraphLayer,
    TemplateLayer, KeyPoint, Citation, Confidence,
)
from src.ael.connectors import get_connector, CONNECTOR_REGISTRY
from src.ael.verification import ResponseVerifier
from src.workflows.ingest_workflow import IngestWorkflow
from src.workflows.query_workflow import QueryWorkflow


class ExportWorkflow:
    '''
    Export workflow: AMDI → UEO → Agent → Verification.

    Sends optimized context to ChatGPT, Claude, Gemini, and other agents.
    '''

    def __init__(self, ingest: IngestWorkflow, query: QueryWorkflow):
        self.ingest = ingest
        self.query = query
        self.verifier = ResponseVerifier()

    def list_agents(self) -> list[str]:
        '''List all supported agents.'''
        return list(CONNECTOR_REGISTRY.keys())

    def build_ueo(self, question: str, retrieved_hits: list = None) -> UniversalExportObject:
        '''Build Universal Export Object from current state.'''
        state = self.ingest.get_state()
        elements = state['elements']
        tables = state['tables']
        graph = state['graph']
        templates = list(state['template'].templates.values())

        # Top-K by importance
        top_elements = sorted(elements, key=lambda e: e.importance_weight, reverse=True)[:20]
        # Tables
        table_dicts = [t.to_dict() if hasattr(t, 'to_dict') else t.__dict__
                       for t in tables[:5]]
        # Citations
        citations = [
            Citation(
                element_id=h.element_id if hasattr(h, 'element_id') else getattr(h, 'element_id', ''),
                page=h.page if hasattr(h, 'page') else getattr(h, 'page', 0),
                section=None,
                snippet=h.content if hasattr(h, 'content') else getattr(h, 'text', ''),
                confidence=h.importance_weight if hasattr(h, 'importance_weight') else getattr(h, 'final_score', 0.5),
            )
            for h in (retrieved_hits or [])[:10]
        ]
        # Key points
        key_points = [
            KeyPoint(
                text=e.content[:500],
                page=e.page,
                section=e.section,
                importance=e.importance_weight,
            )
            for e in top_elements
        ]
        # Graph relations
        graph_data = graph.statistics() if graph else {'nodes': 0, 'edges': 0}
        norm_doc = state.get('normalized')
        pages_count = norm_doc.total_pages if norm_doc else 0

        return UniversalExportObject(
            metadata=Metadata(
                document_name=self.ingest._filename,
                pages=pages_count,
                language='en',
                document_type='unknown',
                doc_id=self.ingest._doc_id,
                total_elements=len(elements),
                total_tables=len(tables),
                total_templates=len(templates),
            ),
            query=question,
            document_summary=DocumentSummary(
                title=self.ingest._filename,
                abstract='',
                key_topics=[],
                keywords=[],
                entities=[],
                sections=[],
            ),
            matrix=MatrixLayer(tables=table_dicts, n_tables=len(tables)),
            graph=GraphLayer(
                nodes=[], edges=[],
                n_nodes=graph_data.get('nodes', 0),
                n_edges=graph_data.get('edges', 0),
            ),
            template=TemplateLayer(
                templates=[t.to_dict() for t in templates],
                n_templates=len(templates),
            ),
            key_points=key_points,
            citations=citations,
            confidence=Confidence(
                overall=0.85, semantic=0.9, numerical=0.95,
                structural=0.85, retrieval=0.85,
            ),
        )

    async def export(
        self,
        question: str,
        agent: str = 'chatgpt',
        api_key: str | None = None,
        model: str | None = None,
        verify: bool = True,
        **kwargs: Any,
    ) -> dict:
        '''Export query to agent and return verified response.'''
        t0 = time.perf_counter()
        # First run retrieval
        retrieval_result = await self.query.query(question, top_k=10)
        # Build UEO
        ueo = self.build_ueo(question)
        # Get connector
        api_key = api_key or ''
        connector = get_connector(agent, api_key=api_key, model=model or '')
        # Send
        try:
            result = await connector.send(ueo, **kwargs)
        except Exception as e:
            logger.exception(f'Export to {agent} failed')
            return {'agent': agent, 'error': str(e), 'latency_s': time.perf_counter() - t0}
        # Verify
        verification = None
        if verify and result.get('answer'):
            v = self.verifier.verify(ueo, result['answer'])
            verification = {
                'is_verified': v.is_verified,
                'overall_confidence': v.overall_confidence,
                'citation_accuracy': v.citation_accuracy,
                'numerical_accuracy': v.numerical_accuracy,
                'hallucination_score': v.hallucination_score,
                'warnings': v.warnings,
            }
        elapsed = time.perf_counter() - t0
        return {
            'agent': agent,
            'model': result.get('model', model),
            'question': question,
            'answer': result.get('answer', ''),
            'input_tokens': result.get('input_tokens', 0),
            'output_tokens': result.get('output_tokens', 0),
            'latency_s': round(elapsed, 3),
            'verification': verification,
            'retrieval': {
                'query_type': retrieval_result['query_type'],
                'dominant_layer': retrieval_result['dominant_layer'],
                'confidence': retrieval_result.get('confidence', 0),
            },
        }
