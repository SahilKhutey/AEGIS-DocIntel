'''
AEGIS-AEL — Agent Export Layer Unit Tests
===========================================
Tests UEO models, priority queue, token budget, formatters, and verification.
'''
from __future__ import annotations

import pytest
import numpy as np

from src.ael.ueo import UniversalExportObject, Metadata, DocumentSummary
from src.ael.priority_queue import ExportPriorityQueue
from src.ael.token_budget import TokenBudgetManager, count_tokens
from src.ael.formats.json_exporter import JSONExporter
from src.ael.formats.markdown_exporter import MarkdownExporter
from src.ael.formats.yaml_exporter import YAMLExporter
from src.ael.verification import ResponseVerificationLayer
from src.ael.exporter import AgentExporter
from src.engines.geometry.element import GeometricElement, ElementType


def test_priority_queue():
    queue = ExportPriorityQueue(w_importance=0.5, w_confidence=0.2, w_query=0.3)
    
    # Add items
    el1 = GeometricElement(element_id='el1', content='low priority')
    el2 = GeometricElement(element_id='el2', content='high priority')
    
    # Priority el1 = 0.5*0.2 + 0.2*0.5 + 0.3*0.1 = 0.1 + 0.1 + 0.03 = 0.23
    # Priority el2 = 0.5*0.9 + 0.2*0.8 + 0.3*0.9 = 0.45 + 0.16 + 0.27 = 0.88
    queue.add(el1, importance=0.2, confidence=0.5, query_relevance=0.1, token_cost=10, dedup_key='el1')
    queue.add(el2, importance=0.9, confidence=0.8, query_relevance=0.9, token_cost=10, dedup_key='el2')
    
    assert len(queue) == 2
    top = queue.pop_top(2)
    assert len(top) == 2
    assert top[0].item.element_id == 'el2'
    assert top[1].item.element_id == 'el1'


def test_token_budget_manager():
    mgr = TokenBudgetManager(agent='chatgpt', model='gpt-4o', target_context=1000)
    
    text_100_tokens = 'hello ' * 80  # ~80-100 tokens
    
    # Check allocation
    assert mgr.can_fit(text_100_tokens)
    assert mgr.allocate('context', text_100_tokens)
    
    summary = mgr.summary()
    assert summary['remaining'] < 1000
    
    # Test truncation
    truncated = mgr.truncate_to_fit(text_100_tokens, max_tokens=10)
    assert count_tokens(truncated) <= 10


def test_response_verification_layer():
    verifier = ResponseVerificationLayer(semantic_match_threshold=0.5)
    
    # Mock UEO
    exporter = AgentExporter()
    meta = {'doc_id': 'doc1', 'document_name': 'report.pdf', 'pages': 5, 'language': 'English', 'document_type': 'Report'}
    summary = {'title': 'Company Report', 'abstract': 'Q3 revenue grew by 15%.'}
    el1 = GeometricElement(element_id='e1', page=1, content='Q3 revenue grew by 15%.')
    el2 = GeometricElement(element_id='e2', page=2, content='Operating expenses were $2M.')
    elements = [el1, el2]
    citations_list = [el1, el2]
    
    ueo = exporter.create_ueo(
        query='What is the revenue growth?',
        doc_metadata=meta,
        summary=summary,
        elements=elements,
        tables=[],
        relationships=[],
        templates=[],
        citations_list=citations_list,
        confidence_scores={'overall': 0.95, 'semantic': 0.9, 'numerical': 0.9, 'structural': 0.9, 'retrieval': 0.9}
    )
    
    # Valid grounded answer
    resp_valid = 'According to the report, Q3 revenue grew by 15% [page 1] and expenses were $2M [page 2].'
    res = verifier.verify(resp_valid, ueo)
    assert res.is_grounded
    assert res.grounding_score > 0.8
    assert len(res.verified_citations) == 2
    assert res.verified_citations[0].is_valid
    
    # Hallucinated answer
    resp_invalid = 'The company purchased 4 new facilities in Q3 [page 12].'
    res_inv = verifier.verify(resp_invalid, ueo)
    assert not res_inv.is_grounded
    assert len(res_inv.verified_citations) == 1
    assert not res_inv.verified_citations[0].is_valid  # page 12 exceeds doc pages (5)


def test_format_exporters():
    exporter = AgentExporter()
    meta = {'doc_id': 'doc1', 'document_name': 'report.pdf', 'pages': 1}
    summary = {'title': 'Test', 'abstract': 'This is a test document.'}
    el = GeometricElement(element_id='e1', page=1, content='Test text.')
    
    ueo = exporter.create_ueo(
        query='Test query',
        doc_metadata=meta,
        summary=summary,
        elements=[el],
        tables=[],
        relationships=[],
        templates=[],
        citations_list=[el],
        confidence_scores={'overall': 0.9}
    )
    
    # Export formats
    json_str = JSONExporter.export(ueo)
    assert 'ueo_id' in json_str
    
    md_str = MarkdownExporter.export(ueo)
    assert '# Test' in md_str
    
    yaml_str = YAMLExporter.export(ueo)
    assert 'ueo_id' in yaml_str
