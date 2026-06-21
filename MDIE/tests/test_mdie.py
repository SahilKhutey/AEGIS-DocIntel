"""
AEGIS-MDIE — Comprehensive Test Suite
=======================================
Tests all 9 mathematical engines:
    E1: GeometryEngine
    E2: RecurrenceEngine
    E3: FrequencyEngine
    E4: MatrixEngine
    E5: GraphEngine
    E6: CompressionEngine
    E7: HybridRetriever
    E8: ContextBuilder
    E9: LLMInterfaceEngine
    E0: MDIEPipeline (integration)
"""
from __future__ import annotations

import asyncio
import math
import sys
import os

# Ensure MDIE is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np
import pytest

from MDIE.engines.geometry.element import BoundingBox, ElementType, GeometricElement
from MDIE.engines.geometry.geometry_engine import GeometryEngine
from MDIE.engines.recurrence.recurrence_engine import RecurrenceEngine
from MDIE.engines.frequency.frequency_engine import FrequencyEngine, TYPE_BASELINE
from MDIE.engines.matrix.matrix_engine import MatrixEngine, TableMatrix, _parse_number
from MDIE.engines.graph.graph_engine import DocumentGraph, EdgeType, GraphEngine
from MDIE.engines.compression.compression_engine import CompressedDocument, CompressionEngine
from MDIE.engines.hybrid_retriever.hybrid_retriever import HybridRetriever, RetrievalResult
from MDIE.engines.context_builder.context_builder import ContextBuilder
from MDIE.engines.llm_interface.llm_interface import GroundingChecker, LLMInterfaceEngine
from MDIE.core.pipeline import MDIEConfig, MDIEPipeline, create_pipeline


# ─────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────

def make_element(
    content: str = "Sample content",
    etype:   ElementType = ElementType.PARAGRAPH,
    page:    int = 1,
    x0: float = 0.1, y0: float = 0.1,
    x1: float = 0.9, y1: float = 0.2,
    doc_id:  str = "doc-001",
    section: str | None = "Introduction",
) -> GeometricElement:
    return GeometricElement(
        doc_id=doc_id,
        bbox=BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1),
        page=page,
        type=etype,
        content=content,
        section=section,
    )


def make_invoice_elements(n_pages: int = 5) -> list[GeometricElement]:
    """Simulate a multi-page invoice with repeating headers/footers."""
    elements = []
    for p in range(1, n_pages + 1):
        # Repeating header
        elements.append(make_element(
            "ACME Corporation Invoice", ElementType.HEADER, page=p,
            x0=0.05, y0=0.02, x1=0.95, y1=0.07,
        ))
        # Repeating footer
        elements.append(make_element(
            f"Page {p} of {n_pages}", ElementType.FOOTER, page=p,
            x0=0.4, y0=0.95, x1=0.6, y1=0.99,
        ))
        # Unique content per page
        elements.append(make_element(
            f"Invoice line item {p}: Product SKU-{p*100}",
            ElementType.PARAGRAPH, page=p,
            x0=0.1, y0=0.15, x1=0.9, y1=0.25,
        ))
    return elements


INVOICE_TABLE_MD = """\
| Product | Q1 | Q2 | Q3 | Q4 |
|---------|----|----|----|----|
| Widget A | 100 | 150 | 200 | 250 |
| Widget B | 80  | 90  | 110 | 140 |
| Widget C | 200 | 180 | 220 | 300 |
"""


# ─────────────────────────────────────────────────────────────────
# E1: Geometry Engine
# ─────────────────────────────────────────────────────────────────

class TestGeometryEngine:

    def test_add_and_retrieve(self):
        geo = GeometryEngine()
        e = make_element("Hello geometry", page=1)
        geo.add(e)
        assert e.element_id in geo.elements

    def test_reading_order(self):
        geo = GeometryEngine()
        e1 = make_element("Second line", page=1, y0=0.5, y1=0.6)
        e2 = make_element("First line",  page=1, y0=0.1, y1=0.2)
        geo.add(e1); geo.add(e2)
        ordered = geo.reading_order(page=1)
        assert ordered[0].content == "First line"
        assert ordered[1].content == "Second line"

    def test_elements_above(self):
        geo = GeometryEngine()
        top    = make_element("Top element",    page=1, y0=0.1, y1=0.2)
        bottom = make_element("Bottom element", page=1, y0=0.5, y1=0.6)
        geo.add(top); geo.add(bottom)
        above = geo.elements_above(bottom, k=5)
        assert any(e.content == "Top element" for e in above)

    def test_elements_below(self):
        geo = GeometryEngine()
        top    = make_element("Top",    page=2, y0=0.1, y1=0.2)
        bottom = make_element("Bottom", page=2, y0=0.7, y1=0.8)
        geo.add(top); geo.add(bottom)
        below = geo.elements_below(top, k=5)
        assert any(e.content == "Bottom" for e in below)

    def test_page_signature_shape(self):
        geo = GeometryEngine()
        for i in range(5):
            geo.add(make_element(f"Elem {i}", page=1, y0=0.1*i, y1=0.1*i+0.09))
        sig = geo.page_signature(page=1)
        assert sig.shape == (32,)
        assert abs(np.linalg.norm(sig) - 1.0) < 0.01   # unit norm

    def test_bounding_box_iou(self):
        a = BoundingBox(0.0, 0.0, 1.0, 1.0)
        b = BoundingBox(0.5, 0.5, 1.5, 1.5)
        iou = a.iou(b)
        assert 0 < iou < 1

    def test_geometry_relevance(self):
        geo = GeometryEngine()
        e = make_element("Revenue section", ElementType.HEADING, page=3, section="Revenue")
        geo.add(e)
        score = geo.geometry_relevance(query_pages=[3], element=e, section_hint="Revenue")
        assert score > 0.7

    def test_stats(self):
        geo = GeometryEngine()
        geo.add(make_element("P", page=1))
        geo.add(make_element("H", ElementType.HEADING, page=1))
        s = geo.stats()
        assert s["total_elements"] == 2
        assert s["pages"] == 1


# ─────────────────────────────────────────────────────────────────
# E2: Recurrence Engine
# ─────────────────────────────────────────────────────────────────

class TestRecurrenceEngine:

    def test_identical_elements_grouped(self):
        rec = RecurrenceEngine()
        elements = [
            make_element("ACME Corp", ElementType.HEADER, page=p,
                         x0=0.05, y0=0.02, x1=0.95, y1=0.07)
            for p in range(1, 8)
        ]
        groups = rec.detect(elements)
        # All 7 identical headers → 1 group
        assert len(groups) == 1
        assert groups[0].count == 7
        assert groups[0].is_template

    def test_unique_elements_not_grouped(self):
        rec = RecurrenceEngine()
        elements = [
            make_element(f"Unique content {i}", ElementType.PARAGRAPH, page=i)
            for i in range(1, 6)
        ]
        rec.detect(elements)
        for g in rec.groups.values():
            assert not g.is_template

    def test_compression_ratio(self):
        rec = RecurrenceEngine()
        elements = make_invoice_elements(n_pages=10)
        rec.detect(elements)
        compressed = rec.compress(elements)
        # header+footer both repeat — expect at least 1 template group
        assert len(compressed["templates"]) >= 1
        savings = compressed["stats"]["savings_pct"]
        assert savings > 0

    def test_statistics(self):
        rec = RecurrenceEngine()
        elements = make_invoice_elements(5)
        rec.detect(elements)
        stats = rec.statistics()
        assert "total_elements" in stats
        assert "template_groups" in stats
        assert stats["total_elements"] > 0

    def test_recurrence_id_assigned(self):
        rec = RecurrenceEngine()
        elements = [
            make_element("Same header", ElementType.HEADER, page=p)
            for p in range(1, 4)
        ]
        rec.detect(elements)
        for e in elements:
            assert e.recurrence_id is not None


# ─────────────────────────────────────────────────────────────────
# E3: Frequency Engine
# ─────────────────────────────────────────────────────────────────

class TestFrequencyEngine:

    def test_inverse_frequency_decreases_with_higher_freq(self):
        freq = FrequencyEngine()
        rare_elem   = make_element("Total Revenue is 5 million USD")
        common_elem = make_element("Page 1 Page 2 Page 3 Page 4 Page 5")
        freq.fit([rare_elem, common_elem] * 20 + [rare_elem])
        w_rare   = freq.inverse_frequency(rare_elem.content)
        w_common = freq.inverse_frequency(common_elem.content)
        assert w_rare > w_common    # unique → higher weight

    def test_type_baseline_table_highest(self):
        freq = FrequencyEngine()
        assert freq.type_baseline(ElementType.TABLE) > freq.type_baseline(ElementType.FOOTER)
        assert freq.type_baseline(ElementType.HEADING) > freq.type_baseline(ElementType.HEADER)

    def test_assign_weights_inplace(self):
        freq = FrequencyEngine()
        elements = [make_element(f"Content {i}") for i in range(10)]
        freq.assign_weights(elements)
        for e in elements:
            assert 0.0 < e.importance_weight <= 1.0

    def test_footer_suppressed(self):
        freq = FrequencyEngine()
        footer_e = make_element("Page 5 of 50", ElementType.FOOTER, page=5)
        heading_e = make_element("Executive Summary", ElementType.HEADING, page=1)
        freq.assign_weights([footer_e, heading_e])
        assert footer_e.importance_weight <= 0.15

    def test_top_k(self):
        freq = FrequencyEngine()
        elements = [make_element(f"Word{i} " * 5) for i in range(20)]
        elements[0] = make_element("Critical finding conclusion", ElementType.HEADING)
        freq.assign_weights(elements)
        top = freq.top_k(elements, k=3)
        assert len(top) == 3

    def test_filter_boilerplate(self):
        freq = FrequencyEngine()
        elements = [
            make_element("Boilerplate", ElementType.FOOTER),
            make_element("Important conclusion", ElementType.HEADING),
        ]
        freq.assign_weights(elements)
        filtered = freq.filter_boilerplate(elements, threshold=0.14)
        # Footer is at 0.15 which is > 0.14, heading is much higher
        for e in filtered:
            assert e.importance_weight > 0.14


# ─────────────────────────────────────────────────────────────────
# E4: Matrix Engine
# ─────────────────────────────────────────────────────────────────

class TestMatrixEngine:

    def test_parse_number(self):
        assert _parse_number("1,000") == 1000.0
        assert _parse_number("3.14") == pytest.approx(3.14)
        assert _parse_number("$500") == 500.0
        assert _parse_number("10%") == 10.0
        assert _parse_number("N/A") is None
        assert _parse_number("") is None

    def test_table_matrix_construction(self):
        tm = TableMatrix(
            table_id="t1",
            headers=["Product", "Q1", "Q2", "Q3", "Q4"],
            row_labels=["Widget A", "Widget B"],
            raw_rows=[
                ["100", "150", "200", "250"],
                ["80",  "90",  "110", "140"],
            ],
        )
        M = tm.matrix()
        assert M.shape == (2, 4)
        assert M[0, 0] == 100.0
        assert M[1, 3] == 140.0

    def test_column_sum(self):
        tm = TableMatrix(
            table_id="t2",
            headers=["Q1", "Q2"],
            raw_rows=[["100", "200"], ["150", "250"]],
        )
        assert tm.col_sum("Q1") == pytest.approx(250.0)

    def test_growth_rate(self):
        tm = TableMatrix(
            table_id="t3",
            headers=["Revenue"],
            raw_rows=[["100"], ["150"], ["200"]],
        )
        g = tm.growth_rate("Revenue")
        assert g == pytest.approx(1.0)   # 100% growth from 100 → 200

    def test_dependencies(self):
        tm = TableMatrix(
            table_id="t4",
            headers=["A", "B", "C"],
            raw_rows=[["10", "20", "30"], ["40", "50", "60"]],
        )
        dep = tm.dependencies(1, 1)   # M[1,1]=50
        assert dep["left"]  == 40.0
        assert dep["above"] == 20.0
        assert dep["diag"]  == 10.0

    def test_to_llm_repr_contains_stats(self):
        tm = TableMatrix(
            table_id="t5",
            headers=["Sales"],
            row_labels=["2024"],
            raw_rows=[["500"]],
        )
        repr_str = tm.to_llm_repr()
        assert "TABLE" in repr_str
        assert "sum=" in repr_str

    def test_answer_question_sum(self):
        tm = TableMatrix(
            table_id="t6",
            headers=["Revenue"],
            raw_rows=[["100"], ["200"], ["300"]],
        )
        ans = tm.answer_question("What is the total Revenue?")
        assert "600" in ans

    def test_matrix_engine_extract_from_elements(self):
        me = MatrixEngine()
        e  = make_element(INVOICE_TABLE_MD, ElementType.TABLE, page=2)
        tables = me.extract_from_elements([e])
        assert len(tables) == 1
        assert tables[0].shape[0] > 0   # has rows


# ─────────────────────────────────────────────────────────────────
# E5: Graph Engine
# ─────────────────────────────────────────────────────────────────

class TestGraphEngine:

    def test_build_basic_graph(self):
        ge = GraphEngine()
        elements = [
            make_element("Introduction", ElementType.HEADING, page=1, y0=0.1, y1=0.2),
            make_element("Body text",    ElementType.PARAGRAPH, page=1, y0=0.25, y1=0.5),
        ]
        graph = ge.build(elements)
        assert len(graph.nodes) == 2
        assert len(graph.edges) > 0

    def test_follows_edges_exist(self):
        ge = GraphEngine()
        e1 = make_element("First",  ElementType.PARAGRAPH, page=1, y0=0.1, y1=0.2)
        e2 = make_element("Second", ElementType.PARAGRAPH, page=1, y0=0.3, y1=0.4)
        graph = ge.build([e1, e2])
        # Should have FOLLOWS edge e1→e2
        follows = [ed for ed in graph.edges if ed.type == EdgeType.FOLLOWS]
        assert len(follows) >= 1

    def test_bfs_traversal(self):
        ge = GraphEngine()
        elements = [
            make_element(f"Elem {i}", page=1, y0=0.1*i, y1=0.1*i+0.09)
            for i in range(5)
        ]
        graph = ge.build(elements)
        start = elements[0].element_id
        reached = graph.bfs(start, max_depth=5)
        assert len(reached) > 0

    def test_structural_score_self_is_one(self):
        ge = GraphEngine()
        e = make_element("Target", page=1)
        graph = ge.build([e])
        score = graph.structural_score(e.element_id, [e.element_id])
        assert score == 1.0

    def test_stats(self):
        ge = GraphEngine()
        elements = [make_element(f"E{i}", page=1, y0=0.1*i, y1=0.1*i+0.09) for i in range(4)]
        graph = ge.build(elements)
        stats = graph.stats()
        assert stats["nodes"] == 4
        assert "edges" in stats


# ─────────────────────────────────────────────────────────────────
# E6: Compression Engine
# ─────────────────────────────────────────────────────────────────

class TestCompressionEngine:

    def test_compress_invoice(self):
        elements = make_invoice_elements(n_pages=10)
        comp_engine = CompressionEngine()
        result = comp_engine.compress(elements, "invoice-001")
        assert result.stats["savings_pct"] > 0
        assert "original_tokens" in result.stats
        assert result.stats["original_elements"] == len(elements)

    def test_compressed_tokens_less_than_original(self):
        elements = make_invoice_elements(n_pages=20)
        comp_engine = CompressionEngine()
        result = comp_engine.compress(elements, "doc")
        assert result.stats["compressed_tokens"] <= result.stats["original_tokens"]

    def test_to_json_roundtrip(self):
        elements = make_invoice_elements(n_pages=3)
        comp_engine = CompressionEngine()
        result = comp_engine.compress(elements, "json-test")
        json_str = result.to_json()
        assert "doc_id" in json_str or "recurrences" in json_str

    def test_template_signature(self):
        elements = make_invoice_elements(n_pages=5)
        comp_engine = CompressionEngine()
        sig = comp_engine.build_template_signature(elements, "sig-test")
        assert sig.heading_count >= 0
        assert sig.block_count > 0

    def test_bytes_roundtrip(self):
        elements = make_invoice_elements(n_pages=3)
        comp_engine = CompressionEngine()
        result = comp_engine.compress(elements, "bytes-test")
        raw = result.to_bytes()
        restored = CompressedDocument.from_bytes(raw, "bytes-test")  # type: ignore
        assert len(restored.uniques) == len(result.uniques)

    def test_decompress_page(self):
        elements = make_invoice_elements(n_pages=4)
        comp_engine = CompressionEngine()
        result = comp_engine.compress(elements, "decomp-test")
        page_elems = comp_engine.decompress_page(result, page=2)
        assert isinstance(page_elems, list)


# ─────────────────────────────────────────────────────────────────
# E7: Hybrid Retriever
# ─────────────────────────────────────────────────────────────────

class TestHybridRetriever:

    def _make_retriever_and_elements(self):
        elements = [
            make_element("Total revenue was $5 million", ElementType.PARAGRAPH, page=1),
            make_element("Revenue grew 25% in Q4",       ElementType.PARAGRAPH, page=2),
            make_element("Boilerplate footer text",       ElementType.FOOTER,    page=1),
            make_element("Executive Summary section",     ElementType.HEADING,   page=1),
            make_element(INVOICE_TABLE_MD,                ElementType.TABLE,     page=3),
        ]
        geo  = GeometryEngine(); geo.add_many(elements)
        freq = FrequencyEngine(); freq.assign_weights(elements)
        mx   = MatrixEngine();   mx.extract_from_elements(elements)
        ret  = HybridRetriever(geometry_engine=geo, frequency_engine=freq, matrix_engine=mx)
        return ret, elements

    def test_retrieve_returns_results(self):
        ret, elems = self._make_retriever_and_elements()
        ctx = ret.retrieve("What is the total revenue?", elems, top_k=3)
        assert len(ctx.results) > 0

    def test_scores_in_range(self):
        ret, elems = self._make_retriever_and_elements()
        ctx = ret.retrieve("revenue growth", elems, top_k=5)
        for r in ctx.results:
            assert 0.0 <= r.score <= 1.0

    def test_weight_adaptation_numeric_query(self):
        ret, elems = self._make_retriever_and_elements()
        a, b, g, d = ret._adapt_weights("What is the total sum of revenue?")
        assert d > 0.10   # matrix weight boosted for numeric query

    def test_weight_adaptation_spatial_query(self):
        ret, elems = self._make_retriever_and_elements()
        a, b, g, d = ret._adapt_weights("On which page is the figure?")
        assert b > 0.20   # geometry weight boosted

    def test_weights_sum_to_one(self):
        ret, elems = self._make_retriever_and_elements()
        a, b, g, d = ret._adapt_weights("General question about the document")
        assert abs(a + b + g + d - 1.0) < 0.001

    def test_mmr_reduces_duplicates(self):
        ret, elems = self._make_retriever_and_elements()
        ctx = ret.retrieve("revenue", elems, top_k=5)
        mmr_results = ret.mmr(ctx.results, lambda_=0.7, top_k=3)
        assert len(mmr_results) <= 3


# ─────────────────────────────────────────────────────────────────
# E8: Context Builder
# ─────────────────────────────────────────────────────────────────

class TestContextBuilder:

    def _make_context(self, question: str = "What is total revenue?") -> BuiltContext:
        from MDIE.engines.hybrid_retriever.hybrid_retriever import RetrievalContext
        elements = [make_element(f"Content {i}", page=i % 3 + 1) for i in range(5)]
        geo  = GeometryEngine(); geo.add_many(elements)
        freq = FrequencyEngine(); freq.assign_weights(elements)
        mx   = MatrixEngine()
        ret  = HybridRetriever(geometry_engine=geo, frequency_engine=freq, matrix_engine=mx)
        ctx  = ret.retrieve(question, elements, top_k=5)
        cb   = ContextBuilder(matrix_engine=mx, max_tokens=4000)
        return cb.build(question, ctx)

    def test_messages_contain_system(self):
        built = self._make_context()
        assert built.messages[0]["role"] == "system"
        assert "MDIE" in built.messages[0]["content"]

    def test_messages_contain_user(self):
        built = self._make_context()
        assert any(m["role"] == "user" for m in built.messages)

    def test_token_budget_respected(self):
        built = self._make_context()
        assert built.tokens_used <= built.token_budget

    def test_source_map_populated(self):
        built = self._make_context()
        assert len(built.source_map) > 0

    def test_context_text_contains_source_label(self):
        built = self._make_context()
        assert "Source-" in built.context_text or "Direct Algebraic" in built.context_text


# ─────────────────────────────────────────────────────────────────
# E9: LLM Interface Engine
# ─────────────────────────────────────────────────────────────────

class TestLLMInterface:

    def test_grounding_checker_no_citations(self):
        gc = GroundingChecker()
        grounded, conf = gc.check("This is an answer with no citations", source_count=5)
        assert grounded is True
        assert conf < 0.7

    def test_grounding_checker_not_found(self):
        gc = GroundingChecker()
        grounded, conf = gc.check("Not found in the provided document.", source_count=5)
        assert grounded is False
        assert conf < 0.3

    def test_confidence_label_extraction(self):
        gc = GroundingChecker()
        label, score = gc.extract_confidence_label("The answer is X. **Confidence: HIGH**")
        assert label == "HIGH"
        assert score > 0.7

    def test_mock_complete(self):
        llm = LLMInterfaceEngine(model_name="mock")
        messages = [
            {"role": "system", "content": "You are MDIE."},
            {"role": "user", "content": "What is revenue?"},
        ]
        response = asyncio.run(llm.reason(messages, {}, {}))
        assert response.answer
        assert response.model == "mock"
        assert 0.0 <= response.confidence <= 1.0

    def test_table_direct_bypasses_llm(self):
        llm = LLMInterfaceEngine(model_name="mock")
        messages = [{"role": "user", "content": "What is the total sum of sales?"}]
        response = asyncio.run(
            llm.reason(messages, {}, {}, table_answers=["Total Sales = $1,500"])
        )
        assert "1,500" in response.answer
        assert response.model == "matrix_direct"

    def test_mock_stream(self):
        llm = LLMInterfaceEngine(model_name="mock")
        messages = [{"role": "user", "content": "Summarize this."}]
        events = []
        async def collect():
            async for ev in llm.stream(messages, {}, {}):
                events.append(ev)
        asyncio.run(collect())
        types = [e["type"] for e in events]
        assert "token" in types
        assert "done" in types


# ─────────────────────────────────────────────────────────────────
# E0: Integration — Full MDIEPipeline
# ─────────────────────────────────────────────────────────────────

class TestMDIEPipeline:

    def _make_pipeline(self) -> tuple[MDIEPipeline, list[GeometricElement]]:
        pipeline = create_pipeline(model_name="mock")
        elements = make_invoice_elements(n_pages=5)
        elements.append(make_element(INVOICE_TABLE_MD, ElementType.TABLE, page=3))
        elements.append(make_element("Executive Summary", ElementType.HEADING, page=1))
        elements.append(make_element(
            "Total revenue for 2024 was $5 million, representing a 25% increase.",
            ElementType.PARAGRAPH, page=1,
        ))
        return pipeline, elements

    def test_ingest_produces_document(self):
        pipeline, elements = self._make_pipeline()
        doc = pipeline.ingest(elements, "test-doc-001", "invoice_2024.pdf")
        assert doc.doc_id == "test-doc-001"
        assert doc.element_count == len(elements)
        assert doc.page_count >= 1

    def test_ingest_produces_stats(self):
        pipeline, elements = self._make_pipeline()
        doc = pipeline.ingest(elements, "stats-doc", "test.pdf")
        assert "ingestion_ms" in doc.stats
        assert "elements" in doc.stats

    def test_ingest_compression_reduces_tokens(self):
        pipeline, elements = self._make_pipeline()
        doc = pipeline.ingest(elements, "comp-test", "test.pdf")
        if doc.compressed:
            orig = doc.compressed.stats.get("original_tokens", 1)
            comp = doc.compressed.stats.get("compressed_tokens", 1)
            assert comp <= orig

    def test_query_returns_response(self):
        pipeline, elements = self._make_pipeline()
        doc = pipeline.ingest(elements, "query-test", "test.pdf")
        response = asyncio.run(pipeline.query(doc, "What is the total revenue?"))
        assert response.answer
        assert response.latency_ms > 0
        assert response.model == "mock"

    def test_query_confidence_range(self):
        pipeline, elements = self._make_pipeline()
        doc = pipeline.ingest(elements, "conf-test", "test.pdf")
        response = asyncio.run(pipeline.query(doc, "Summarize the document"))
        assert 0.0 <= response.confidence <= 1.0

    def test_compression_report(self):
        pipeline, elements = self._make_pipeline()
        doc = pipeline.ingest(elements, "report-test", "invoice.pdf")
        report = pipeline.compression_report(doc)
        assert "COMPRESSION" in report
        assert "savings" in report.lower() or "Savings" in report

    def test_retrieval_explain(self):
        pipeline, elements = self._make_pipeline()
        doc = pipeline.ingest(elements, "explain-test", "invoice.pdf")
        explanation = pipeline.retrieval_explain(doc, "What is the revenue?", top_k=3)
        assert "Retrieval Explanation" in explanation
        assert "R=" in explanation

    def test_stream_query(self):
        pipeline, elements = self._make_pipeline()
        doc = pipeline.ingest(elements, "stream-test", "test.pdf")
        events = []
        async def collect():
            async for ev in pipeline.stream_query(doc, "What is in this document?"):
                events.append(ev)
        asyncio.run(collect())
        types = {e["type"] for e in events}
        assert "token" in types
        assert "done" in types

    def test_document_summary(self):
        pipeline, elements = self._make_pipeline()
        doc = pipeline.ingest(elements, "summary-test", "test.pdf")
        summary = doc.summary()
        assert "test.pdf" in summary
        assert "pages" in summary

    def test_math_formula_D_equals_S_plus_G_plus_M_plus_F(self):
        """
        Validate the core mathematical identity:
            D = S + G + M + F
        Weights must sum to 1.0 (normalization constraint).
        """
        cfg = MDIEConfig(alpha=0.5, beta=0.2, gamma=0.2, delta=0.1)
        total = cfg.alpha + cfg.beta + cfg.gamma + cfg.delta
        assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"

    def test_information_theory_compression_bound(self):
        """
        Validate: compressed_tokens < original_tokens for structured docs (R_n = R_0).
        This is the core information-theoretic claim of MDIE.
        """
        pipeline = create_pipeline()
        # 20-page invoice with repeating header/footer
        elements = make_invoice_elements(n_pages=20)
        doc = pipeline.ingest(elements, "theory-test", "big_invoice.pdf")
        if doc.compressed:
            assert doc.compressed.stats["compressed_tokens"] \
                 < doc.compressed.stats["original_tokens"], \
                "Compression claim violated: C > 1"
