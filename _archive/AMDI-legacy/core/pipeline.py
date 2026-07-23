"""
AEGIS-AMDI — Unified Pipeline
================================
Adaptive Mathematical Document Intelligence

D = {S, G, R, F, M, T, X, H, P}

R_final = α·S + β·G + γ·R + δ·F + ε·M + ζ·T + η·X

All 12 sub-engines coordinated here:
    L1  SemanticEngine       → S layer
    L2  GeometryEngine       → G layer  (from MDIE)
    L3  RecurrenceEngine     → R layer  (from MDIE)
    L4  FrequencyEngine      → F layer  (from MDIE)
    L5  MatrixEngine         → M layer  (from MDIE)
    L6  TemplateEngine       → T layer  (NEW)
    L7  GraphEngine          → X layer  (from MDIE, enhanced)
    L8  HypergraphEngine     → H layer  (NEW)
    L9  SpectralEngine       → entropy + layout  (NEW)
    L10 AdaptiveFusionEngine → routing + scoring  (NEW)
    L11 MemoryEngine         → tiered store  (NEW)
    L12 ContextBuilder       → token budget  (from MDIE, enhanced)
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Optional

from AMDI.engines.geometry.element import Element, ElementType
from AMDI.engines.semantic.semantic_engine import SemanticEngine
from AMDI.engines.template.template_engine import PageTemplate, TemplateEngine
from AMDI.engines.spectral.spectral_engine import SpectralEngine
from AMDI.engines.hypergraph.hypergraph_engine import Hypergraph, HypergraphEngine
from AMDI.engines.fusion.adaptive_fusion import (
    AdaptiveFusionEngine, FusionContext, FusionResult, FusionWeights, QueryType,
)
from AMDI.engines.memory.memory_engine import MemoryEngine, MemoryTier

# Re-use proven MDIE engines
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from MDIE.engines.geometry.geometry_engine import GeometryEngine
from MDIE.engines.recurrence.recurrence_engine import RecurrenceEngine
from MDIE.engines.frequency.frequency_engine import FrequencyEngine
from MDIE.engines.matrix.matrix_engine import MatrixEngine
from MDIE.engines.graph.graph_engine import DocumentGraph, GraphEngine
from MDIE.engines.context_builder.context_builder import BuiltContext, ContextBuilder

log = logging.getLogger("amdi.pipeline")


# ─────────────────────────────────────────────────────────────────
# Processed Document
# ─────────────────────────────────────────────────────────────────

@dataclass
class AMDIDocument:
    """Complete multi-representation of a document."""
    doc_id:    str
    filename:  str
    elements:  list[Element]

    # Layer products
    templates:  list[PageTemplate]        = field(default_factory=list)
    graph:      Optional[DocumentGraph]   = None
    hypergraph: Optional[Hypergraph]      = None
    stats:      dict[str, Any]           = field(default_factory=dict)

    # Quick lookup
    _by_id:    dict[str, Element] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self._by_id = {e.element_id: e for e in self.elements}

    def element(self, eid: str) -> Optional[Element]:
        return self._by_id.get(eid)

    @property
    def page_count(self) -> int:
        return max((e.page for e in self.elements), default=0)

    @property
    def element_count(self) -> int:
        return len(self.elements)

    @property
    def table_count(self) -> int:
        return sum(1 for e in self.elements if e.type == ElementType.TABLE)

    def summary_str(self) -> str:
        s = self.stats
        return (
            f"[{self.filename}] pages={self.page_count} elements={len(self.elements)} "
            f"tables={self.table_count} templates={len(self.templates)} "
            f"compression={s.get('template_compression_pct', 0):.1f}%"
        )


# ─────────────────────────────────────────────────────────────────
# AMDI Response
# ─────────────────────────────────────────────────────────────────

@dataclass
class AMDIResponse:
    answer:           str
    citations:        list[dict]
    confidence:       float
    confidence_label: str
    query_type:       str
    weights_used:     dict[str, float]
    latency_ms:       float
    table_direct:     list[str]
    grounded:         bool
    tokens_used:      int
    model:            str


# ─────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────

@dataclass
class AMDIConfig:
    # Ingestion
    enable_semantic:    bool  = True
    enable_templates:   bool  = True
    enable_spectral:    bool  = True
    enable_hypergraph:  bool  = True
    enable_embeddings:  bool  = False
    template_threshold: float = 0.90
    min_template_pages: int   = 2

    # Retrieval
    top_k:       int   = 12
    use_mmr:     bool  = True
    mmr_lambda:  float = 0.70

    # Context
    max_tokens:      int = 8000
    reserve_tokens:  int = 2000
    model_name:      str = "mock"

    # Memory
    memory_enabled:  bool  = True
    hot_cache_mb:    float = 256.0


# ─────────────────────────────────────────────────────────────────
# AMDI Pipeline
# ─────────────────────────────────────────────────────────────────

class AMDIPipeline:
    """
    Adaptive Mathematical Document Intelligence — Master Pipeline.

    Usage:
        pipeline = AMDIPipeline()
        doc      = pipeline.ingest(elements, doc_id="report_2025")
        response = await pipeline.query(doc, "What is total revenue for 2024?")
    """

    def __init__(
        self,
        config:     Optional[AMDIConfig] = None,
        llm_client  = None,
        embedder    = None,
    ):
        self.cfg        = config or AMDIConfig()
        self.llm_client = llm_client
        self.embedder   = embedder

        # L1
        self.semantic   = SemanticEngine(embedder=embedder)
        # L6
        self.template   = TemplateEngine(
            similarity_threshold=self.cfg.template_threshold,
            min_cluster=self.cfg.min_template_pages,
        )
        # L9
        self.spectral   = SpectralEngine()
        # L8
        self.hypergraph = HypergraphEngine()
        # L10
        self.fusion     = AdaptiveFusionEngine()
        # L11
        self.memory     = MemoryEngine() if self.cfg.memory_enabled else None

        # MDIE engines (L2–L7)
        self._geo       = GeometryEngine()
        self._rec       = RecurrenceEngine()
        self._freq      = FrequencyEngine()
        self._matrix    = MatrixEngine()
        self._graph_eng = GraphEngine()
        self._ctx       = ContextBuilder(
            max_tokens=self.cfg.max_tokens,
            reserve_output=self.cfg.reserve_tokens,
        )

        log.info("AMDIPipeline initialized | model=%s", self.cfg.model_name)

    # ──────────────────────────────────────────────────────────────
    # Ingestion — all 12 engines
    # ──────────────────────────────────────────────────────────────

    def ingest(
        self,
        elements: list[Element],
        doc_id:   str,
        filename: str = "document",
    ) -> AMDIDocument:
        """
        Full 12-engine ingestion pipeline.
        Returns a fully annotated AMDIDocument.
        """
        t0 = time.perf_counter()
        log.info("AMDI ingestion: '%s' (%d elements)", doc_id, len(elements))

        # ── L2: Geometry ─────────────────────────────────────────
        self._geo = GeometryEngine()
        # Convert Element → GeometricElement proxy for MDIE engines
        geo_proxies = self._to_geo_elements(elements)
        self._geo.add_many(geo_proxies)

        # ── L3: Recurrence ───────────────────────────────────────
        self._rec = RecurrenceEngine()
        rec_groups = self._rec.detect(geo_proxies)
        # Propagate recurrence_id back to AMDI elements
        for gp, el in zip(geo_proxies, elements):
            el.recurrence_id = gp.recurrence_id
            el.is_template   = gp.is_template if hasattr(gp, "is_template") else False

        # ── L4: Frequency ────────────────────────────────────────
        self._freq = FrequencyEngine()
        self._freq.assign_weights(geo_proxies)
        for gp, el in zip(geo_proxies, elements):
            el.importance_weight = gp.importance_weight

        # ── L5: Matrix ───────────────────────────────────────────
        self._matrix = MatrixEngine()
        tables = self._matrix.extract_from_elements(geo_proxies)

        # ── L6: Template (NEW) ───────────────────────────────────
        tmpl_list = self.template.build(elements) if self.cfg.enable_templates else []
        # Mark template elements
        for tmpl in tmpl_list:
            if tmpl.is_dominant:
                for p in tmpl.pages:
                    for e in elements:
                        if e.page == p and e.type in (ElementType.HEADER, ElementType.FOOTER):
                            e.is_template = True

        # ── L7: Graph ────────────────────────────────────────────
        self._graph_eng = GraphEngine()
        doc_graph = self._graph_eng.build(geo_proxies)

        # ── L8: Hypergraph (NEW) ──────────────────────────────────
        hyper = self.hypergraph.build(elements) if self.cfg.enable_hypergraph else None

        # ── L9: Spectral (NEW) ───────────────────────────────────
        if self.cfg.enable_spectral:
            self.spectral.fit_idf(elements)
            entropy_profiles = self.spectral.profile_elements(elements)
            repetitive_pages = self.spectral.find_repetitive_pages(elements)
        else:
            entropy_profiles = []
            repetitive_pages = []

        # ── L1: Semantic (NEW) ───────────────────────────────────
        if self.cfg.enable_semantic:
            self.semantic.fit(elements)
            sem_results = self.semantic.process(elements)
        else:
            sem_results = []

        # ── L11: Memory ──────────────────────────────────────────
        if self.memory:
            self._cache_document(doc_id, elements, tmpl_list)

        elapsed = (time.perf_counter() - t0) * 1000

        tmpl_compression = self.template.compression_factor(
            max((e.page for e in elements), default=1)
        ) if tmpl_list else 1.0
        template_compression_pct = round((1 - tmpl_compression) * 100, 1)

        stats = {
            "ingestion_ms":            round(elapsed, 1),
            "elements":                len(elements),
            "tables":                  len(tables),
            "templates":               len(tmpl_list),
            "repetitive_pages":        len(repetitive_pages),
            "graph_nodes":             len(doc_graph.nodes),
            "graph_edges":             len(doc_graph.edges),
            "hyperedges":              len(hyper.hyperedges) if hyper else 0,
            "template_compression_pct": template_compression_pct,
            "rec_groups":              len(rec_groups),
            "semantic_elements":       len(sem_results),
        }

        log.info(
            "Ingestion complete: %.1fms | %d templates | %d tables | "
            "%.1f%% template compression",
            elapsed, len(tmpl_list), len(tables), template_compression_pct,
        )

        doc = AMDIDocument(
            doc_id=doc_id, filename=filename,
            elements=elements,
            templates=tmpl_list,
            graph=doc_graph,
            hypergraph=hyper,
            stats=stats,
        )
        return doc

    # ──────────────────────────────────────────────────────────────
    # Query — L10 + L12
    # ──────────────────────────────────────────────────────────────

    async def query(
        self,
        doc:          AMDIDocument,
        question:     str,
        top_k:        int              = None,
        query_pages:  Optional[list[int]] = None,
        section_hint: Optional[str]       = None,
        history:      Optional[list[dict]] = None,
    ) -> AMDIResponse:
        """
        Full adaptive query pipeline:
            L10 AdaptiveFusion: classify + route + score
            L12 ContextBuilder: token-budget assembly
            LLM: grounded reasoning
        """
        t0   = time.perf_counter()
        k    = top_k or self.cfg.top_k
        elements = doc.elements

        # Check hot cache
        if self.memory:
            cached = self.memory.retrieve(f"{doc.doc_id}:qa:{question[:80]}", MemoryTier.SUMMARY)
            if cached:
                log.info("Cache hit for query: '%s'", question[:60])
                return AMDIResponse(**cached)

        # ── Compute layer scores ─────────────────────────────────
        geo_proxies   = self._to_geo_elements(elements)
        q_emb         = self.semantic.embed_query(question)
        seed_ids      = set()

        s_scores: dict[str, float] = {}
        g_scores: dict[str, float] = {}
        r_scores: dict[str, float] = {}
        f_scores: dict[str, float] = {}
        m_scores: dict[str, float] = {}
        t_scores: dict[str, float] = {}
        x_scores: dict[str, float] = {}

        for el, gp in zip(elements, geo_proxies):
            eid = el.element_id
            # S — semantic cosine
            s_scores[eid] = self.semantic.score(q_emb, el)
            # G — geometry (page/section match)
            g_scores[eid] = self._geo.geometry_relevance(query_pages, gp, section_hint)
            # R — recurrence penalty (templates de-prioritized)
            r_scores[eid] = 0.2 if el.is_template else 0.8
            # F — frequency importance
            f_scores[eid] = el.importance_weight
            # M — matrix (table affinity)
            m_scores[eid] = self._matrix_score(question, el)
            # T — template (is it unique content?)
            t_scores[eid] = self.template.score(query_pages, el)
            # X — graph structural score (seeded from top-S candidates)
            x_scores[eid] = 0.0   # filled below

        # Graph expansion: compute structural scores relative to top-S seeds
        top_s = sorted(s_scores, key=s_scores.get, reverse=True)[:5]
        if doc.graph:
            for el in elements:
                eid = el.element_id
                x_scores[eid] = doc.graph.structural_score(eid, top_s)

        # Hypergraph expansion
        if doc.hypergraph:
            seed_ids = set(top_s)
            for el in elements:
                hg_s = self.hypergraph.hypergraph_score(el, seed_ids)
                x_scores[el.element_id] = max(x_scores[el.element_id], hg_s * 0.8)

        # ── L10: Adaptive Fusion ─────────────────────────────────
        # Direct table answers (bypass LLM)
        table_answers = self._matrix.query(question)

        fusion: FusionContext = self.fusion.fuse(
            query=question, elements=elements,
            s_scores=s_scores, g_scores=g_scores, r_scores=r_scores,
            f_scores=f_scores, m_scores=m_scores, t_scores=t_scores,
            x_scores=x_scores,
            table_answers=table_answers,
            top_k=k, use_mmr=self.cfg.use_mmr, mmr_lambda=self.cfg.mmr_lambda,
        )

        # ── L12: Context Building ────────────────────────────────
        from MDIE.engines.hybrid_retriever.hybrid_retriever import RetrievalContext, RetrievalResult
        # Wrap fusion results into MDIE RetrievalResult objects for ContextBuilder
        wrapped = []
        for fr in fusion.results:
            gp = self._to_geo_element(fr.element)
            rr = RetrievalResult(
                element=gp,
                score=fr.final_score,
                score_s=fr.layer_scores.get("semantic", 0),
                score_g=fr.layer_scores.get("geometry", 0),
                score_f=fr.layer_scores.get("frequency", 0),
                score_m=fr.layer_scores.get("matrix", 0),
            )
            wrapped.append(rr)

        from MDIE.engines.hybrid_retriever.hybrid_retriever import RetrievalContext
        retrieval_ctx = RetrievalContext(
            query=question,
            results=wrapped,
            table_answers=table_answers,
            weights_used=fusion.weights.to_dict(),
            latency_ms=fusion.latency_ms,
            token_count=sum(e.token_count for e in elements if any(fr.element is e for fr in fusion.results)),
        )
        built: BuiltContext = self._ctx.build(question, retrieval_ctx, history)

        # ── LLM ──────────────────────────────────────────────────
        from MDIE.engines.llm_interface.llm_interface import LLMInterfaceEngine
        llm = LLMInterfaceEngine(llm_client=self.llm_client, model_name=self.cfg.model_name)
        elem_map = {e.element_id: self._to_geo_element(e) for e in elements}
        llm_resp = await llm.reason(
            messages=built.messages,
            source_map=built.source_map,
            elements_map=elem_map,
            table_answers=table_answers,
        )

        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        response = AMDIResponse(
            answer           = llm_resp.answer,
            citations        = [{"source": c.source_num, "page": c.page,
                                 "type": c.element_type, "snippet": c.snippet}
                                for c in llm_resp.citations],
            confidence       = llm_resp.confidence,
            confidence_label = llm_resp.confidence_label,
            query_type       = fusion.query_type.value,
            weights_used     = fusion.weights.to_dict(),
            latency_ms       = latency_ms,
            table_direct     = table_answers,
            grounded         = llm_resp.grounded,
            tokens_used      = built.tokens_used,
            model            = llm_resp.model,
        )

        # Cache in hot tier
        if self.memory:
            self.memory.store(
                f"{doc.doc_id}:qa:{question[:80]}",
                response.__dict__,
                MemoryTier.SUMMARY,
                doc.doc_id,
            )

        log.info(
            "Query complete: type=%s conf=%.2f latency=%.0fms tokens=%d",
            fusion.query_type.value, response.confidence,
            latency_ms, built.tokens_used,
        )
        return response

    async def stream_query(
        self, doc: AMDIDocument, question: str, top_k: int = None, history=None,
    ) -> AsyncGenerator[dict, None]:
        """Streaming version — yields SSE dicts."""
        k = top_k or self.cfg.top_k
        # Simplified stream: compute, then yield tokens
        yield {"type": "routing", "content": self.fusion.explain_routing(question)}
        resp = await self.query(doc, question, top_k=k, history=history)
        for word in resp.answer.split():
            yield {"type": "token", "content": word + " "}
            await asyncio.sleep(0)
        yield {"type": "citations", "citations": resp.citations}
        yield {"type": "metadata", "confidence": resp.confidence,
               "query_type": resp.query_type, "weights": resp.weights_used}
        yield {"type": "done"}

    # ──────────────────────────────────────────────────────────────
    # Utilities
    # ──────────────────────────────────────────────────────────────

    def explain(self, doc: AMDIDocument, question: str) -> str:
        lines = [self.fusion.explain_routing(question), ""]
        # Template stats
        lines.append(f"Templates detected: {len(doc.templates)}")
        for t in doc.templates[:3]:
            lines.append(f"  {t.template_id}: {t.cluster_size} pages")
        # Entropy stats
        ents = sorted(doc.elements, key=lambda e: e.entropy, reverse=True)[:5]
        lines.append("\nTop-5 highest-entropy elements:")
        for e in ents:
            lines.append(f"  [{e.type.value}] p={e.page} H={e.entropy:.2f} '{e.content[:50]}'")
        return "\n".join(lines)

    def compression_report(self, doc: AMDIDocument) -> str:
        s = doc.stats
        lines = [
            "=" * 64,
            "AMDI COMPRESSION REPORT",
            "=" * 64,
            f"Document:                {doc.filename}",
            f"Elements:                {s.get('elements', 0):,}",
            f"Page templates:          {s.get('templates', 0)}",
            f"Template compression:    {s.get('template_compression_pct', 0):.1f}%",
            f"Recurrence groups:       {s.get('rec_groups', 0)}",
            f"Tables (algebraic):      {s.get('tables', 0)}",
            f"Graph edges:             {s.get('graph_edges', 0)}",
            f"Hyperedges:              {s.get('hyperedges', 0)}",
            f"Ingestion time:          {s.get('ingestion_ms', 0):.1f}ms",
            "=" * 64,
        ]
        if self.memory:
            ms = self.memory.statistics()
            lines.append(f"Cache hit rate:          {ms['hit_rate']*100:.1f}%")
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────

    def _matrix_score(self, query: str, el: Element) -> float:
        if el.type != ElementType.TABLE:
            return 0.0
        tbl = self._matrix.get(el.element_id)
        if tbl:
            q = query.lower()
            if any(h.lower() in q for h in tbl.headers):
                return 0.9
        numeric_kw = ["total","sum","average","max","min","growth","revenue","profit"]
        return 0.4 if any(k in query.lower() for k in numeric_kw) else 0.1

    def _to_geo_elements(self, elements: list[Element]):
        """Create GeometricElement proxies from AMDI Elements for MDIE engines."""
        from MDIE.engines.geometry.element import GeometricElement as GE
        from MDIE.engines.geometry.element import BoundingBox as GBB, ElementType as GET
        from MDIE.engines.geometry.element import ElementType as GETy
        result = []
        for e in elements:
            gbbox = GBB(e.bbox.x0, e.bbox.y0, e.bbox.x1, e.bbox.y1) if e.bbox else None
            try:
                gtype = GET(e.type.value)
            except ValueError:
                gtype = GET.PARAGRAPH
            ge = GE(
                doc_id=e.doc_id, bbox=gbbox, page=e.page,
                type=gtype, content=e.content, section=e.section,
            )
            ge.element_id       = e.element_id
            ge.importance_weight = e.importance_weight
            ge.embedding        = e.embedding
            ge.recurrence_id    = e.recurrence_id
            result.append(ge)
        return result

    def _to_geo_element(self, el: Element):
        return self._to_geo_elements([el])[0]

    def _cache_document(self, doc_id: str, elements: list[Element], templates: list[PageTemplate]) -> None:
        if not self.memory:
            return
        # Cache summaries in hot tier
        for e in elements:
            if e.summary:
                self.memory.store(
                    f"{doc_id}:summary:{e.element_id}",
                    {"text": e.summary, "keyphrases": e.keyphrases, "entities": e.entities},
                    MemoryTier.SUMMARY, doc_id,
                )
        # Cache template metadata in cold tier
        for t in templates:
            self.memory.store(
                f"{doc_id}:template:{t.template_id}",
                t.to_dict(),
                MemoryTier.TEMPLATE, doc_id,
            )


# ─────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────

def create_amdi(
    model_name:      str   = "mock",
    use_embeddings:  bool  = False,
    llm_client       = None,
    embedder         = None,
    **config_kwargs,
) -> AMDIPipeline:
    """
    Convenience factory.

    Examples:
        amdi = create_amdi()                              # dev mode
        amdi = create_amdi("gpt-4o", llm_client=client)  # production
        amdi = create_amdi(use_embeddings=True)           # with dense search
    """
    cfg = AMDIConfig(
        model_name=model_name,
        enable_embeddings=use_embeddings,
        **{k: v for k, v in config_kwargs.items() if hasattr(AMDIConfig, k)},
    )
    return AMDIPipeline(config=cfg, llm_client=llm_client, embedder=embedder)
