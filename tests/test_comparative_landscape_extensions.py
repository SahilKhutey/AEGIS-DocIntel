'''
AEGIS-DocIntel / AMDI-OS — Comparative Landscape Extensions Test Suite
========================================================================
Verifies recommendations from July 2026 Comparative Landscape Report:
  - Query-adaptive token budget sizing (Databricks Mosaic paradigm)
  - Anthropic-style contextual retrieval prefixing
  - LangChain & LlamaIndex drop-in connector adapters
'''
from __future__ import annotations

import pytest
from src.engines.optimization.optimization_engine import OptimizationEngine
from src.ael.elastic_chunker import ElasticChunker
from src.connectors.framework_connectors import (
    AEGISLangChainDocumentTransformer,
    AEGISLlamaIndexNodeParser,
)


def test_query_adaptive_token_budget_sizing():
    '''Test Databricks Mosaic-style query adaptive budget sizing.'''
    opt = OptimizationEngine()

    budget_factoid = opt.adapt_budget_for_query('factoid', base_budget=2000)
    assert budget_factoid == 500

    budget_analytical = opt.adapt_budget_for_query('analytical', base_budget=2000)
    assert budget_analytical == 4000

    budget_multihop = opt.adapt_budget_for_query('multi_hop', base_budget=2000)
    assert budget_multihop == 2000


def test_anthropic_contextual_prefixing():
    '''Test Anthropic-style contextual prefix generation for chunks.'''
    chunk = {
        'text': 'Revenue grew by 25% year over year.',
        'page': 3,
        'type': 'table',
        'heading': 'Financial Performance',
    }

    prefixed = ElasticChunker.generate_contextual_prefix(chunk, doc_title='Q3 Report')
    assert '[Q3 Report | Page 3 | Type: table]' in prefixed
    assert '(Section: Financial Performance)' in prefixed
    assert 'Revenue grew by 25%' in prefixed


def test_langchain_document_transformer():
    '''Test LangChain drop-in document transformer adapter.'''
    transformer = AEGISLangChainDocumentTransformer()

    docs = [
        {'id': 'n1', 'text': 'Title Heading', 'type': 'heading', 'font_size': 18.0, 'x': 0.1, 'y': 0.1, 'w': 0.8, 'h': 0.05, 'page': 1},
        {'id': 'n2', 'text': 'Q1 Revenue table data', 'type': 'table', 'font_size': 11.0, 'x': 0.1, 'y': 0.2, 'w': 0.8, 'h': 0.2, 'page': 1},
    ]

    transformed = transformer.transform_documents(docs)
    assert len(transformed) >= 1
    assert 'page_content' in transformed[0]
    assert 'metadata' in transformed[0]
    assert transformed[0]['metadata']['chunk_id'].startswith('aegis_chunk_')


def test_llamaindex_node_parser():
    '''Test LlamaIndex drop-in node parser adapter.'''
    parser = AEGISLlamaIndexNodeParser()

    docs = [
        {'id': 'n1', 'text': 'Financial Overview', 'type': 'heading', 'font_size': 18.0, 'x': 0.1, 'y': 0.1, 'w': 0.8, 'h': 0.05, 'page': 1},
        {'id': 'n2', 'text': 'Net margin increased 12%', 'type': 'text', 'font_size': 11.0, 'x': 0.1, 'y': 0.2, 'w': 0.8, 'h': 0.1, 'page': 1},
    ]

    nodes = parser.get_nodes_from_documents(docs)
    assert len(nodes) >= 1
    assert 'text' in nodes[0]
    assert 'extra_info' in nodes[0]
