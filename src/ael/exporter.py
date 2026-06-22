'''
AEGIS-AEL — Agent Exporter
============================
Integrates UEO construction, Priority Queue sorting, Token Budget limits,
and runs the connector request + verification pipeline.
'''
from __future__ import annotations

import logging
import time
from typing import List, Dict, Any, Optional

from src.ael.ueo import (
    UniversalExportObject, Metadata, DocumentSummary, SemanticLayer,
    GeometryLayer, MatrixLayer, GraphLayer, TemplateLayer, TableExport,
    Citation, KeyPoint, Confidence, ExportFormat
)
from src.ael.priority_queue import ExportPriorityQueue
from src.ael.token_budget import TokenBudgetManager, count_tokens
from src.ael.connectors import (
    ChatGPTConnector, GeminiConnector, ClaudeConnector,
    DeepSeekConnector, QwenConnector, LocalConnector
)
from src.ael.verification import ResponseVerificationLayer, VerificationResult

logger = logging.getLogger('amdi.ael.exporter')


class AgentExporter:
    '''
    Main export controller for the Agent Export Layer (AEL).
    Converts AMDI database/in-memory states to UEO, packages context,
    forwards it to the target connector, and verifies the response.
    '''

    def __init__(self, semantic_match_threshold: float = 0.5):
        self.verifier = ResponseVerificationLayer(semantic_match_threshold)

    def create_ueo(
        self,
        query: str,
        doc_metadata: dict,
        summary: dict,
        elements: List[Any],
        tables: List[Any],
        relationships: List[dict],
        templates: List[dict],
        citations_list: List[Any],
        confidence_scores: dict,
    ) -> UniversalExportObject:
        '''
        Assembles a clean UniversalExportObject from the raw AMDI engines' outputs.
        '''
        # Metadata
        meta = Metadata(
            document_name=doc_metadata.get('document_name', 'document.pdf'),
            pages=doc_metadata.get('pages', 1),
            language=doc_metadata.get('language', 'English'),
            document_type=doc_metadata.get('document_type', 'Unknown'),
            doc_id=doc_metadata.get('doc_id', 'default'),
            total_elements=len(elements),
            total_tables=len(tables),
            total_templates=len(templates)
        )

        # Document Summary
        doc_sum = DocumentSummary(
            title=summary.get('title', ''),
            abstract=summary.get('abstract', ''),
            key_topics=summary.get('key_topics', []),
            keywords=summary.get('keywords', []),
            entities=summary.get('entities', []),
            sections=summary.get('sections', [])
        )

        # Sort and filter elements using the Priority Queue to fit token budgets
        queue = ExportPriorityQueue()
        for idx, el in enumerate(elements):
            importance = getattr(el, 'importance_weight', 0.5)
            # Query relevance via semantic similarity or Jaccard fallback
            query_rel = 0.5
            if hasattr(el, 'metadata') and el.metadata:
                query_rel = el.metadata.get('query_relevance', 0.5)
            # Safe token estimation fallback
            content_text = getattr(el, 'content', '') or ''
            cost = count_tokens(content_text)
            queue.add(el, importance, 0.8, query_rel, token_cost=cost, dedup_key=getattr(el, 'element_id', str(idx)))

        # Retrieve top 20 prioritized elements
        top_items = queue.pop_top(20)
        selected_elements = [item.item for item in top_items]

        # Key Points from prioritized elements
        key_points = []
        for idx, el in enumerate(selected_elements[:5]):
            content_text = getattr(el, 'content', '') or ''
            key_points.append(KeyPoint(
                text=content_text,
                page=getattr(el, 'page', 1),
                section=getattr(el, 'section', None),
                importance=getattr(el, 'importance_weight', 1.0)
            ))

        # Citations list
        citations = []
        for cite in citations_list[:12]:
            content_text = getattr(cite, 'content', '') or ''
            citations.append(Citation(
                element_id=getattr(cite, 'element_id', ''),
                page=getattr(cite, 'page', 1),
                section=getattr(cite, 'section', None),
                snippet=content_text,
                confidence=getattr(cite, 'importance_weight', 0.9)
            ))

        # Tables (Matrix Layer)
        table_exports = []
        for tbl in tables[:5]:
            # Convert matrix object to UEO TableExport
            headers = tbl.get('headers', [])
            data = tbl.get('data', [])
            table_exports.append(TableExport(
                name=tbl.get('name', 'Table'),
                page=tbl.get('page', 1),
                headers=headers,
                data=data,
                shape=(len(data), len(headers)) if data else (0, 0),
                computed_metrics=tbl.get('computed_metrics', {}),
                element_id=tbl.get('element_id', '')
            ))

        # Confidence
        conf = Confidence(
            overall=confidence_scores.get('overall', 0.9),
            semantic=confidence_scores.get('semantic', 0.9),
            numerical=confidence_scores.get('numerical', 0.9),
            structural=confidence_scores.get('structural', 0.9),
            retrieval=confidence_scores.get('retrieval', 0.9)
        )

        return UniversalExportObject(
            metadata=meta,
            query=query,
            document_summary=doc_sum,
            semantic=SemanticLayer(
                topics=[{'name': t} for t in doc_sum.key_topics],
                keywords=[{'term': kw} for kw in doc_sum.keywords],
                entities=doc_sum.entities
            ),
            geometry=GeometryLayer(
                important_regions=[{'page': getattr(el, 'page', 1), 'content': getattr(el, 'content', '')[:100]} for el in selected_elements[:10]]
            ),
            matrix=MatrixLayer(tables=table_exports, n_tables=len(table_exports)),
            graph=GraphLayer(
                nodes=[{'id': n.get('id'), 'type': n.get('type')} for n in relationships],
                edges=relationships,
                n_nodes=len(relationships),
                key_relationships=relationships
            ),
            template=TemplateLayer(
                templates=templates,
                n_templates=len(templates)
            ),
            key_points=key_points,
            citations=citations,
            confidence=conf
        )

    def get_connector(self, agent: str, api_key: str, model: str | None = None, **kwargs) -> Any:
        agent_lower = agent.lower()
        if agent_lower == 'chatgpt':
            return ChatGPTConnector(api_key=api_key, model=model or 'gpt-4o', **kwargs)
        elif agent_lower == 'gemini':
            return GeminiConnector(api_key=api_key, model=model or 'gemini-2.0-flash', **kwargs)
        elif agent_lower == 'claude':
            return ClaudeConnector(api_key=api_key, model=model or 'claude-3-5-sonnet-20241022', **kwargs)
        elif agent_lower == 'deepseek':
            return DeepSeekConnector(api_key=api_key, model=model or 'deepseek-chat', **kwargs)
        elif agent_lower == 'qwen':
            return QwenConnector(api_key=api_key, model=model or 'qwen-max', **kwargs)
        elif agent_lower in ('local', 'vllm'):
            return LocalConnector(endpoint=kwargs.get('endpoint', 'http://localhost:8001/v1'), model=model or 'meta-llama/Llama-3.3-70B-Instruct', api_key=api_key, **kwargs)
        else:
            raise ValueError(f'Unknown agent connector: {agent}')

    async def export_and_verify(
        self,
        ueo: UniversalExportObject,
        agent: str,
        api_key: str,
        model: str | None = None,
        **kwargs
    ) -> dict:
        '''
        Constructs the client connector, pushes context packages,
        gets the response, runs citation and grounding verification,
        and outputs a verified citation package.
        '''
        connector = self.get_connector(agent, api_key, model, **kwargs)
        
        # Track start time
        t0 = time.perf_counter()
        
        # Send UEO
        response = await connector.send(ueo, **kwargs)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        
        if 'error' in response:
            return {
                'ueo_id': ueo.ueo_id,
                'agent': agent,
                'model': model or response.get('model', ''),
                'verified': False,
                'error': response['error'],
                'latency_ms': elapsed_ms
            }

        # Run verification layer
        answer = response.get('answer', '')
        verification_res = self.verifier.verify(answer, ueo)
        
        return {
            'ueo_id': ueo.ueo_id,
            'agent': agent,
            'model': response.get('model', ''),
            'answer': answer,
            'input_tokens': response.get('input_tokens', 0),
            'output_tokens': response.get('output_tokens', 0),
            'latency_ms': elapsed_ms,
            'verification': {
                'is_grounded': verification_res.is_grounded,
                'grounding_score': round(verification_res.grounding_score, 4),
                'verified_citations': [
                    {
                        'index': vc.citation_index,
                        'page': vc.page,
                        'section': vc.section,
                        'is_valid': vc.is_valid,
                        'reason': vc.reason
                    }
                    for vc in verification_res.verified_citations
                ],
                'unverified_claims': verification_res.unverified_claims,
                'calibrated_confidence': round(verification_res.calibrated_confidence, 4),
                'feedback': verification_res.feedback
            }
        }
