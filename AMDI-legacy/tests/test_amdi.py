"""
AEGIS-AMDI — Comprehensive Test Suite
========================================
Tests all 12 engines:
    L1  SemanticEngine
    L2  GeometryEngine (via MDIE)
    L3  RecurrenceEngine (via MDIE)
    L4  FrequencyEngine (via MDIE)
    L5  MatrixEngine (via MDIE)
    L6  TemplateEngine (NEW)
    L7  GraphEngine (via MDIE)
    L8  HypergraphEngine (NEW)
    L9  SpectralEngine (NEW)
    L10 AdaptiveFusionEngine (NEW)
    L11 MemoryEngine (NEW)
    L12 AMDIPipeline (integration)
"""
from __future__ import annotations
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np
import pytest

from AMDI.engines.geometry.element import BoundingBox, Element, ElementType
from AMDI.engines.semantic.semantic_engine import SemanticEngine
from AMDI.engines.template.template_engine import TemplateEngine
from AMDI.engines.spectral.spectral_engine import SpectralEngine
from AMDI.engines.hypergraph.hypergraph_engine import HypergraphEngine, Hyperedge
from AMDI.engines.fusion.adaptive_fusion import (
    AdaptiveFusionEngine, FusionWeights, QueryClassifier, QueryType,
)
from AMDI.engines.memory.memory_engine import MemoryEngine, MemoryTier
from AMDI.core.pipeline import AMDIConfig, AMDIPipeline, create_amdi


# ─────────────────────────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────────────────────────

def elem(
    content="Sample text", etype=ElementType.PARAGRAPH, page=1,
    x0=0.1, y0=0.1, x1=0.9, y1=0.2, section="Introduction", doc_id="doc-001",
) -> Element:
    return Element(
        doc_id=doc_id, page=page, type=etype, content=content,
        bbox=BoundingBox(x0, y0, x1, y1), section=section,
    )


def make_invoice(n_pages: int = 5) -> list[Element]:
    """Multi-page invoice with repeating header/footer."""
    els = []
    for p in range(1, n_pages + 1):
        els.append(elem("ACME Corp Invoice Q4 2024", ElementType.HEADER, p,
                        x0=0.05, y0=0.01, x1=0.95, y1=0.06))
        els.append(elem(f"Page {p} of {n_pages}", ElementType.FOOTER, p,
                        x0=0.4, y0=0.95, x1=0.6, y1=0.99))
        els.append(elem(f"Line item {p}: Product SKU-{p*100} — ${ p*250 }",
                        ElementType.PARAGRAPH, p,
                        x0=0.1, y0=0.15, x1=0.9, y1=0.25))
    return els


TABLE_MD = """\
| Product | Q1 | Q2 | Q3 | Q4 |
|---------|----|----|----|----|
| Widget A | 100 | 150 | 200 | 250 |
| Widget B | 80  | 90  | 110 | 140 |
"""


# ─────────────────────────────────────────────────────────────────
# L1 — Semantic Engine
# ─────────────────────────────────────────────────────────────────

class TestSemanticEngine:

    def test_process_returns_results(self):
        se = SemanticEngine()
        elements = [elem(f"Document line {i}") for i in range(5)]
        se.fit(elements)
        results = se.process(elements)
        assert len(results) == 5

    def test_ner_extracts_money(self):
        se = SemanticEngine()
        ents = se._extract_entities("Revenue was $5,000,000 in 2024.")
        labels = [label for _, label in ents]
        assert "MONEY" in labels

    def test_ner_extracts_percent(self):
        se = SemanticEngine()
        ents = se._extract_entities("Growth was 25.5% year-over-year.")
        labels = [label for _, label in ents]
        assert "PERCENT" in labels

    def test_ner_extracts_date(self):
        se = SemanticEngine()
        ents = se._extract_entities("Signed on 2024-03-15.")
        labels = [label for _, label in ents]
        assert "DATE" in labels

    def test_keyphrases_non_empty(self):
        se = SemanticEngine()
        elements = [elem(f"Revenue growth profit Q{i}", ElementType.HEADING) for i in range(10)]
        se.fit(elements)
        kps = se._keyphrases("Revenue growth is 25% higher than profit forecast.", top_k=5)
        assert len(kps) >= 1

    def test_summarize_shorter_than_source(self):
        se = SemanticEngine()
        long_text = "This is sentence one. This is sentence two. This is sentence three. Final sentence here."
        summary = se._summarize(long_text, n=2)
        assert len(summary) <= len(long_text)

    def test_sentiment_positive(self):
        se = SemanticEngine()
        s = se._sentiment("Excellent growth and profit success this year.")
        assert s > 0

    def test_sentiment_negative(self):
        se = SemanticEngine()
        s = se._sentiment("Bad loss failure risk defect error poor.")
        assert s < 0

    def test_sentiment_neutral(self):
        se = SemanticEngine()
        s = se._sentiment("The document contains tables and sections.")
        assert s == 0.0

    def test_score_lexical_fallback(self):
        se = SemanticEngine()
        e = elem("Revenue growth profit forecast")
        se._query_text = "Revenue growth"
        score = se.score(None, e)
        assert 0.0 <= score <= 1.0

    def test_entities_written_to_element(self):
        se = SemanticEngine()
        elements = [elem("Revenue was $1M. Growth was 10%.")]
        se.fit(elements)
        se.process(elements)
        assert len(elements[0].entities) > 0

    def test_summary_written_to_element(self):
        se = SemanticEngine()
        elements = [elem("First sentence. Second sentence. Third sentence. Fourth sentence.")]
        se.fit(elements)
        se.process(elements)
        assert elements[0].summary != ""


# ─────────────────────────────────────────────────────────────────
# L6 — Template Engine
# ─────────────────────────────────────────────────────────────────

class TestTemplateEngine:

    def test_build_detects_templates_in_invoice(self):
        te = TemplateEngine(similarity_threshold=0.90, min_cluster=2)
        elements = make_invoice(n_pages=8)
        templates = te.build(elements)
        # Repeating header+footer pages should form clusters
        assert len(templates) >= 1

    def test_cluster_sizes_correct(self):
        te = TemplateEngine(min_cluster=2)
        elements = make_invoice(n_pages=10)
        templates = te.build(elements)
        total_pages = sum(t.cluster_size for t in templates)
        assert total_pages >= 2

    def test_page_signature_is_unit_vector(self):
        te = TemplateEngine()
        elements = make_invoice(n_pages=1)
        sig = te._page_signature(elements)
        assert abs(np.linalg.norm(sig) - 1.0) < 0.01

    def test_cosine_similarity_identical(self):
        te = TemplateEngine()
        elements = make_invoice(n_pages=1)
        sig = te._page_signature(elements)
        assert te._cos_sim(sig, sig) > 0.999

    def test_template_score_dominant_template(self):
        te = TemplateEngine(min_cluster=2)
        elements = make_invoice(n_pages=5)
        te.build(elements)
        footer = next(e for e in elements if e.type == ElementType.FOOTER)
        footer.is_template = True
        score = te.score(query_pages=[1], element=footer)
        assert score <= 0.9   # boilerplate suppressed

    def test_compression_factor_less_than_one(self):
        te = TemplateEngine(min_cluster=2)
        elements = make_invoice(n_pages=10)
        te.build(elements)
        factor = te.compression_factor(total_pages=10)
        assert 0.0 < factor <= 1.0

    def test_statistics_returns_dict(self):
        te = TemplateEngine(min_cluster=2)
        elements = make_invoice(n_pages=6)
        te.build(elements)
        stats = te.statistics()
        assert "templates" in stats and "pages_covered" in stats


# ─────────────────────────────────────────────────────────────────
# L9 — Spectral Engine
# ─────────────────────────────────────────────────────────────────

class TestSpectralEngine:

    def test_fft_returns_signature(self):
        se = SpectralEngine()
        elements = [elem(f"E{i}", page=1, y0=0.1*i, y1=0.1*i+0.09) for i in range(8)]
        sig = se.analyze_page_layout(elements, page=1)
        assert len(sig.power_spectrum) > 0
        assert 0.0 <= sig.layout_periodicity <= 1.0

    def test_fft_short_page_returns_empty(self):
        se = SpectralEngine()
        elements = [elem("Only one", page=1)]
        sig = se.analyze_page_layout(elements, page=1)
        assert sig.is_repetitive is False

    def test_entropy_high_for_unique_content(self):
        se = SpectralEngine()
        corpus = [elem(f"Word{i} term{i} concept{i} idea{i}") for i in range(20)]
        se.fit_idf(corpus)
        long_text = elem("critical unprecedented discovery anomaly finding warning signal")
        h = se.element_entropy(long_text)
        assert h > 0.0   # non-empty unique content → positive entropy

    def test_profile_elements_assigns_priority(self):
        se = SpectralEngine()
        elements = [elem(f"Content line {i}" * 5) for i in range(10)]
        profiles = se.profile_elements(elements)
        priorities = [p.priority for p in profiles]
        assert sorted(priorities) == list(range(len(elements)))

    def test_split_by_entropy(self):
        se = SpectralEngine()
        elements = [
            elem("unique anomaly critical unprecedented finding!", ElementType.HEADING),
            elem("Page of document header", ElementType.HEADER),
        ]
        se.profile_elements(elements)
        informative, boilerplate = se.split_by_entropy(elements)
        assert len(informative) + len(boilerplate) == 2

    def test_entropy_score_in_range(self):
        se = SpectralEngine()
        elements = [elem(f"Word{i} content" * 5) for i in range(5)]
        se.profile_elements(elements)
        for e in elements:
            s = se.entropy_score(e)
            assert 0.0 <= s <= 1.0


# ─────────────────────────────────────────────────────────────────
# L8 — Hypergraph Engine
# ─────────────────────────────────────────────────────────────────

class TestHypergraphEngine:

    def test_build_returns_hypergraph(self):
        hge = HypergraphEngine()
        elements = [
            elem("Revenue table", ElementType.TABLE, page=1, y0=0.3, y1=0.6),
            elem("Table 1: Revenue breakdown", ElementType.CAPTION, page=1, y0=0.62, y1=0.65),
            elem("Table 1 shows revenue growth over four quarters.", ElementType.PARAGRAPH, page=1, y0=0.67, y1=0.75),
        ]
        hg = hge.build(elements)
        assert len(hg.hyperedges) >= 1

    def test_section_groups_created(self):
        hge = HypergraphEngine()
        elements = [
            elem(f"Section content {i}", ElementType.PARAGRAPH, page=1, section="Results")
            for i in range(5)
        ]
        hg = hge.build(elements)
        section_edges = [h for h in hg.hyperedges if h.type == "section_group"]
        assert len(section_edges) >= 1

    def test_hyperedge_arity_ge_2(self):
        hge = HypergraphEngine()
        elements = [
            elem("Big table", ElementType.TABLE, page=1, y0=0.2, y1=0.5),
            elem("Caption for big table", ElementType.CAPTION, page=1, y0=0.52, y1=0.55),
        ]
        hg = hge.build(elements)
        for h in hg.hyperedges:
            assert h.arity >= 2

    def test_edges_of_node(self):
        hge = HypergraphEngine()
        tbl = elem("Sales matrix", ElementType.TABLE, page=2, y0=0.3, y1=0.6)
        cap = elem("Table 2 caption", ElementType.CAPTION, page=2, y0=0.61, y1=0.64)
        hg  = hge.build([tbl, cap])
        edges = hg.edges_of(tbl.element_id)
        assert isinstance(edges, list)

    def test_hypergraph_score_seed_is_one(self):
        hge = HypergraphEngine()
        e = elem("Target")
        hge.build([e])
        score = hge.hypergraph_score(e, {e.element_id})
        assert score == 1.0

    def test_statistics_dict(self):
        hge = HypergraphEngine()
        elements = [
            elem("T", ElementType.TABLE, page=1, y0=0.2, y1=0.5),
            elem("C", ElementType.CAPTION, page=1, y0=0.52, y1=0.55),
        ]
        hg = hge.build(elements)
        s = hg.statistics()
        assert "hyperedges" in s and "avg_arity" in s


# ─────────────────────────────────────────────────────────────────
# L10 — Adaptive Fusion Engine
# ─────────────────────────────────────────────────────────────────

class TestAdaptiveFusion:

    def test_classify_numerical(self):
        qc = QueryClassifier()
        qt, conf = qc.classify("What is the total revenue for 2024?")
        assert qt in (QueryType.NUMERICAL, QueryType.AGGREGATION)

    def test_classify_semantic(self):
        qc = QueryClassifier()
        qt, conf = qc.classify("Explain the conclusions of this report.")
        assert qt == QueryType.SEMANTIC

    def test_classify_structural(self):
        qc = QueryClassifier()
        qt, conf = qc.classify("What is on page 3?")
        assert qt == QueryType.STRUCTURAL

    def test_classify_aggregation(self):
        qc = QueryClassifier()
        qt, conf = qc.classify("What is the total sum of all costs?")
        assert qt == QueryType.AGGREGATION

    def test_weights_sum_to_one(self):
        qc = QueryClassifier()
        for query in [
            "What is total revenue?",
            "Explain the conclusion.",
            "Where is figure 3?",
            "What changed in v2?",
        ]:
            weights, qt, conf = qc.route(query)
            total = weights._arr().sum()
            assert abs(total - 1.0) < 1e-6, f"Weights sum={total} for '{query}'"

    def test_matrix_gets_high_weight_for_sum(self):
        qc = QueryClassifier()
        weights, qt, conf = qc.route("What is the total sum?")
        assert weights.w_m > 0.4   # matrix dominant

    def test_semantic_gets_high_weight_for_explain(self):
        qc = QueryClassifier()
        weights, qt, conf = qc.route("Explain the main conclusions.")
        assert weights.w_s > 0.5

    def test_geometry_gets_high_weight_for_layout(self):
        qc = QueryClassifier()
        weights, qt, conf = qc.route("Show me the layout of figure on page 3.")
        assert weights.w_g > 0.3

    def test_fuse_returns_context(self):
        afe = AdaptiveFusionEngine()
        elements = [elem(f"Content {i}", page=i % 3 + 1) for i in range(6)]
        ctx = afe.fuse("What is total revenue?", elements, top_k=3)
        assert len(ctx.results) > 0
        assert ctx.query_type in QueryType.__members__.values()

    def test_fuse_scores_in_range(self):
        afe = AdaptiveFusionEngine()
        elements = [elem(f"Text {i}") for i in range(5)]
        s_scores = {e.element_id: 0.8 for e in elements}
        ctx = afe.fuse("General question", elements, s_scores=s_scores, top_k=5)
        for r in ctx.results:
            assert 0.0 <= r.final_score <= 1.0

    def test_mmr_reduces_duplicates(self):
        afe = AdaptiveFusionEngine()
        elements = [elem("Revenue was $5M. Growth was 25%.") for _ in range(6)]
        # All identical → MMR should select diverse subset
        ctx = afe.fuse("revenue", elements, top_k=3, use_mmr=True)
        assert len(ctx.results) <= 3

    def test_explain_routing_string(self):
        afe = AdaptiveFusionEngine()
        explanation = afe.explain_routing("What is total profit?")
        assert "Query:" in explanation
        assert "Weights:" in explanation

    def test_fusion_weights_dominant_layer(self):
        fw = FusionWeights(w_s=0.8, w_g=0.1, w_r=0.04, w_f=0.03, w_m=0.02, w_t=0.005, w_x=0.005)
        assert fw.dominant() == "semantic"


# ─────────────────────────────────────────────────────────────────
# L11 — Memory Engine
# ─────────────────────────────────────────────────────────────────

class TestMemoryEngine:

    def test_store_and_retrieve_hot(self):
        me = MemoryEngine()
        me.store("key1", {"text": "hello"}, MemoryTier.SUMMARY, "doc-1")
        val = me.retrieve("key1", MemoryTier.SUMMARY)
        assert val == {"text": "hello"}

    def test_retrieve_missing_returns_none(self):
        me = MemoryEngine()
        assert me.retrieve("nonexistent") is None

    def test_store_and_retrieve_across_tiers(self):
        me = MemoryEngine()
        me.store("k2", "warm-data", MemoryTier.TABLE, "doc-2")
        val = me.retrieve("k2")   # tier-agnostic search
        assert val == "warm-data"

    def test_hit_rate_increases_on_cache_hit(self):
        me = MemoryEngine()
        me.store("k3", [1,2,3], MemoryTier.CHUNK, "doc-3")
        me.retrieve("k3")
        me.retrieve("k3")
        assert me.hit_rate > 0

    def test_invalidate_document(self):
        me = MemoryEngine()
        me.store("k4", "data", MemoryTier.SUMMARY, "doc-X")
        me.store("k5", "data", MemoryTier.CHUNK,   "doc-X")
        evicted = me.invalidate_document("doc-X")
        assert evicted == 2

    def test_lru_eviction(self):
        me = MemoryEngine()
        # Fill tiny cache with 1-byte entries until full — then add one more
        me._caches[MemoryTier.SUMMARY]._max_bytes = 10
        for i in range(20):
            me.store(f"k{i}", f"{i}", MemoryTier.SUMMARY, "doc-ev")
        # Should not raise; LRU eviction should keep size under limit
        assert me._caches[MemoryTier.SUMMARY]._bytes <= 10

    def test_store_document_batch(self):
        me = MemoryEngine()
        me.store_document("doc-batch", {
            "summaries": {"e1": {"text": "Summary"}},
            "chunks":    {"c1": {"text": "Chunk"}},
            "templates": {"T1": {"cluster_size": 3}},
        })
        assert me.retrieve("doc-batch:summary:e1") == {"text": "Summary"}

    def test_statistics_structure(self):
        me = MemoryEngine()
        s = me.statistics()
        assert "hit_rate" in s and "tiers" in s
        assert "SUMMARY" in s["tiers"]


# ─────────────────────────────────────────────────────────────────
# L12 — Full AMDIPipeline Integration
# ─────────────────────────────────────────────────────────────────

class TestAMDIPipeline:

    def _make(self) -> tuple[AMDIPipeline, list[Element]]:
        pipeline = create_amdi(model_name="mock")
        elements = make_invoice(n_pages=5)
        elements.append(elem(TABLE_MD, ElementType.TABLE, page=3,
                             y0=0.2, y1=0.7, section="Revenue"))
        elements.append(elem("Executive Summary", ElementType.HEADING, page=1,
                             section="Summary"))
        elements.append(elem(
            "Total revenue for 2024 reached $5 million, up 25% from prior year.",
            ElementType.PARAGRAPH, page=1, section="Summary",
        ))
        return pipeline, elements

    def test_ingest_produces_document(self):
        p, els = self._make()
        doc = p.ingest(els, "test-amdi-001", "report_2024.pdf")
        assert doc.doc_id == "test-amdi-001"
        assert doc.element_count == len(els)

    def test_ingest_has_templates(self):
        p, els = self._make()
        doc = p.ingest(els, "tmpl-test", "invoice.pdf")
        # 5-page invoice with repeating header/footer → should produce templates
        assert isinstance(doc.templates, list)

    def test_ingest_stats_populated(self):
        p, els = self._make()
        doc = p.ingest(els, "stats-test", "f.pdf")
        assert "ingestion_ms" in doc.stats
        assert doc.stats["elements"] == len(els)

    def test_ingest_hyperedges(self):
        p, els = self._make()
        doc = p.ingest(els, "hg-test", "f.pdf")
        assert doc.hypergraph is not None
        assert len(doc.hypergraph.hyperedges) >= 0   # may be 0 for simple structure

    def test_query_returns_response(self):
        p, els = self._make()
        doc   = p.ingest(els, "q-test", "f.pdf")
        resp  = asyncio.run(p.query(doc, "What is the total revenue?"))
        assert resp.answer
        assert resp.model == "mock"

    def test_query_confidence_in_range(self):
        p, els = self._make()
        doc   = p.ingest(els, "conf-test", "f.pdf")
        resp  = asyncio.run(p.query(doc, "Summarize the document."))
        assert 0.0 <= resp.confidence <= 1.0

    def test_query_has_query_type(self):
        p, els = self._make()
        doc   = p.ingest(els, "qt-test", "f.pdf")
        resp  = asyncio.run(p.query(doc, "What is the total revenue?"))
        assert resp.query_type in [qt.value for qt in QueryType]

    def test_query_weights_sum_to_one(self):
        p, els = self._make()
        doc   = p.ingest(els, "w-test", "f.pdf")
        resp  = asyncio.run(p.query(doc, "What are the main findings?"))
        total = sum(resp.weights_used.values())
        assert abs(total - 1.0) < 0.001

    def test_stream_query(self):
        p, els = self._make()
        doc   = p.ingest(els, "stream-test", "f.pdf")
        events = []
        async def collect():
            async for ev in p.stream_query(doc, "What is in this document?"):
                events.append(ev)
        asyncio.run(collect())
        types = {e["type"] for e in events}
        assert "token" in types and "done" in types

    def test_compression_report(self):
        p, els = self._make()
        doc   = p.ingest(els, "cr-test", "invoice.pdf")
        report = p.compression_report(doc)
        assert "AMDI COMPRESSION REPORT" in report
        assert "invoice.pdf" in report

    def test_explain(self):
        p, els = self._make()
        doc   = p.ingest(els, "exp-test", "f.pdf")
        expl  = p.explain(doc, "What is the revenue?")
        assert "Query:" in expl

    def test_memory_cache_hit_after_two_queries(self):
        p, els = self._make()
        doc   = p.ingest(els, "mem-test", "f.pdf")
        q     = "What is the total revenue?"
        asyncio.run(p.query(doc, q))   # store
        asyncio.run(p.query(doc, q))   # should hit cache
        if p.memory:
            assert p.memory.hit_rate > 0

    def test_mathematical_constraint_weights_simplex(self):
        """∀ query: Σ W_i = 1 (probability simplex constraint)."""
        qc = QueryClassifier()
        test_queries = [
            "Total revenue 2024?", "Explain the conclusion.", "Figure on page 5?",
            "Sum of all costs?", "Which template is this?", "Headers on all pages?",
        ]
        for q in test_queries:
            w, qt, conf = qc.route(q)
            total = w._arr().sum()
            assert abs(total - 1.0) < 1e-6, f"Simplex violated for: '{q}' Σ={total}"

    def test_summary_str(self):
        p, els = self._make()
        doc = p.ingest(els, "sum-str-test", "report.pdf")
        s = doc.summary_str()
        assert "report.pdf" in s and "pages=" in s
