"""
Unit tests for Contextual-Prefix Enrichment and Query-Adaptive Budget Sizing (Tasks H-4, H-5).
"""

import pytest
from src.engines.retrieval.contextual_prefix import ContextualPrefixEnricher
from src.engines.retrieval.query_adaptive_budget import QueryAdaptiveBudgetSizer, QueryType


def test_contextual_prefix_enrichment():
    enricher = ContextualPrefixEnricher()
    enriched = enricher.enrich_chunk(
        chunk_id="chunk-1",
        text="The Net Operating Margin increased by 15%.",
        doc_title="FY2026 Q3 Monograph",
        section_title="Financial Performance",
        situational_summary="Executive report on quarterly earnings",
    )

    assert "FY2026 Q3 Monograph" in enriched.context_prefix
    assert "Financial Performance" in enriched.context_prefix
    assert "The Net Operating Margin" in enriched.enriched_text
    assert enriched.chunk_id == "chunk-1"


def test_contextual_prefix_batch_enrichment():
    enricher = ContextualPrefixEnricher()
    chunks = [
        {"chunk_id": "c1", "text": "Paragraph one text", "section": "Intro"},
        {"chunk_id": "c2", "text": "Paragraph two text", "section": "Methods"},
    ]
    res = enricher.enrich_chunks(chunks, doc_title="Technical Specs")

    assert len(res) == 2
    assert "Technical Specs" in res[0].enriched_text
    assert "Intro" in res[0].enriched_text
    assert "Methods" in res[1].enriched_text


def test_query_adaptive_budget_classification():
    sizer = QueryAdaptiveBudgetSizer()

    assert sizer.classify_query("What is the security classification?") == QueryType.FACTOID
    assert sizer.classify_query("Why did the memory consumption increase in Session 4?") == QueryType.MULTIHOP
    assert sizer.classify_query("Compare the latency between vector index and lexical index") == QueryType.ANALYTICAL
    assert sizer.classify_query("Provide an executive summary of the document") == QueryType.SUMMARIZATION


def test_query_adaptive_budget_computation():
    sizer = QueryAdaptiveBudgetSizer()

    b_factoid = sizer.compute_budget("What is the document title?")
    b_summary = sizer.compute_budget("Summarize the main findings")

    assert b_factoid < b_summary
    assert b_factoid == 512
    assert b_summary == 4096

    # Test scaling relative to base budget
    scaled_factoid = sizer.compute_budget("What is X?", base_budget=2000)
    scaled_summary = sizer.compute_budget("Summarize X", base_budget=2000)

    assert scaled_factoid == 1000
    assert scaled_summary == 4000
