"""
AEGIS-MDIE — Core Pipeline Orchestrator
=========================================
Master pipeline:

    PDF
     ↓ GeometryEngine        e_i = (x,y,w,h,p,t,c)
     ↓ RecurrenceEngine      R_n = R_0
     ↓ FrequencyEngine       w(x) = 1/log(1+f(x))
     ↓ MatrixEngine          M[i,j] = v, D(i,j)
     ↓ GraphEngine           G = (V, E)
     ↓ CompressionEngine     D = {T, R_n, Δ}
     ↓ HybridRetriever       R = αS + βG + γF + δM
     ↓ ContextBuilder        Knapsack token budget
     ↓ LLMInterfaceEngine    Grounded reasoning + citations
     ↓
    MDIEResponse
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from MDIE.engines.compression.compression_engine import CompressedDocument, CompressionEngine
from MDIE.engines.context_builder.context_builder import BuiltContext, ContextBuilder
from MDIE.engines.frequency.frequency_engine import FrequencyEngine
from MDIE.engines.geometry.element import ElementType, GeometricElement
from MDIE.engines.geometry.geometry_engine import GeometryEngine
from MDIE.engines.graph.graph_engine import DocumentGraph, GraphEngine
from MDIE.engines.hybrid_retriever.hybrid_retriever import HybridRetriever, RetrievalContext
from MDIE.engines.llm_interface.llm_interface import LLMInterfaceEngine, MDIEResponse
from MDIE.engines.matrix.matrix_engine import MatrixEngine
from MDIE.engines.recurrence.recurrence_engine import RecurrenceEngine

log = logging.getLogger("mdie.pipeline")


# ─────────────────────────────────────────────────────────────────
# Processed Document
# ─────────────────────────────────────────────────────────────────

@dataclass
class ProcessedDocument:
    """Full mathematical representation of a document."""
    doc_id:     str
    filename:   str
    elements:   list[GeometricElement]
    graph:      Optional[DocumentGraph]       = None
    compressed: Optional[CompressedDocument]  = None
    stats:      dict[str, Any]               = field(default_factory=dict)

    # Engine references (for incremental operations)
    _geometry:    Optional[GeometryEngine]  = field(default=None, repr=False)
    _frequency:   Optional[FrequencyEngine] = field(default=None, repr=False)
    _matrix:      Optional[MatrixEngine]    = field(default=None, repr=False)
    _recurrence:  Optional[RecurrenceEngine] = field(default=None, repr=False)

    @property
    def page_count(self) -> int:
        return max((e.page for e in self.elements), default=0)

    @property
    def element_count(self) -> int:
        return len(self.elements)

    @property
    def table_count(self) -> int:
        return sum(1 for e in self.elements if e.type == ElementType.TABLE)

    def element_by_id(self, eid: str) -> Optional[GeometricElement]:
        for e in self.elements:
            if e.element_id == eid:
                return e
        return None

    def elements_on_page(self, page: int) -> list[GeometricElement]:
        return [e for e in self.elements if e.page == page]

    def summary(self) -> str:
        comp = self.compressed
        savings = comp.stats.get("savings_pct", 0) if comp else 0
        return (
            f"Document '{self.filename}' | {self.page_count} pages | "
            f"{self.element_count} elements | {self.table_count} tables | "
            f"Token savings: {savings:.1f}%"
        )


# ─────────────────────────────────────────────────────────────────
# MDIE Pipeline Configuration
# ─────────────────────────────────────────────────────────────────

@dataclass
class MDIEConfig:
    """Configuration for the MDIE pipeline."""
    # Retrieval
    top_k:          int   = 12
    use_mmr:        bool  = True
    mmr_lambda:     float = 0.7
    use_graph_expansion: bool = True

    # Weights R = αS + βG + γF + δM
    alpha:  float = 0.50
    beta:   float = 0.20
    gamma:  float = 0.20
    delta:  float = 0.10

    # Context budget
    max_context_tokens:  int = 8000
    reserve_output_tokens: int = 2000

    # Compression
    enable_compression: bool = True
    spatial_tolerance:  float = 0.04
    jaccard_threshold:  float = 0.92

    # LLM
    llm_max_tokens: int = 2048
    model_name:     str = "mock"

    # Embedding
    use_embeddings:     bool  = False
    embedding_model_name: str = "BAAI/bge-large-en-v1.5"
    embedding_device:   str   = "cpu"


# ─────────────────────────────────────────────────────────────────
# MDIE Pipeline
# ─────────────────────────────────────────────────────────────────

class MDIEPipeline:
    """
    Mathematical Document Intelligence Engine — Master Orchestrator

    Usage:
        pipeline = MDIEPipeline()
        doc      = pipeline.ingest(elements, doc_id="report_2025")
        response = await pipeline.query(doc, "What is the total revenue for 2024?")
    """

    def __init__(
        self,
        config:     Optional[MDIEConfig]         = None,
        llm_client  = None,
        embedder    = None,
    ):
        self.cfg      = config or MDIEConfig()
        self.llm_client = llm_client
        self.embedder   = embedder

        # Initialize engines
        self.geo_engine  = GeometryEngine()
        self.rec_engine  = RecurrenceEngine(
            spatial_tolerance=self.cfg.spatial_tolerance,
            text_jaccard_threshold=self.cfg.jaccard_threshold,
        )
        self.freq_engine  = FrequencyEngine()
        self.matrix_engine = MatrixEngine()
        self.graph_engine  = GraphEngine()
        self.comp_engine   = CompressionEngine(
            recurrence_engine=self.rec_engine,
            geometry_engine=self.geo_engine,
        )
        self.retriever = HybridRetriever(
            geometry_engine=self.geo_engine,
            frequency_engine=self.freq_engine,
            matrix_engine=self.matrix_engine,
            embedding_model=self.embedder,
            weights={
                "alpha": self.cfg.alpha, "beta": self.cfg.beta,
                "gamma": self.cfg.gamma, "delta": self.cfg.delta,
            },
        )
        self.context_builder = ContextBuilder(
            matrix_engine=self.matrix_engine,
            max_tokens=self.cfg.max_context_tokens,
            reserve_output=self.cfg.reserve_output_tokens,
        )
        self.llm_engine = LLMInterfaceEngine(
            llm_client=self.llm_client,
            model_name=self.cfg.model_name,
        )

        log.info("MDIEPipeline initialized | model=%s", self.cfg.model_name)

    # ──────────────────────────────────────────────────────────────
    # Engine 1–6: Document Ingestion Pipeline
    # ──────────────────────────────────────────────────────────────

    def ingest(
        self,
        elements: list[GeometricElement],
        doc_id:   str,
        filename: str = "document",
    ) -> ProcessedDocument:
        """
        Full mathematical ingestion pipeline:
            E1: GeometryEngine    — spatial indexing + normalization
            E2: RecurrenceEngine  — R_n = R_0 detection
            E3: FrequencyEngine   — w(x) = 1/log(1+f(x))
            E4: MatrixEngine      — M[i,j] extraction
            E5: GraphEngine       — G = (V, E) construction
            E6: CompressionEngine — D = {T, R_n, Δ}
        """
        t0 = time.perf_counter()
        log.info("Ingesting document '%s' (%d elements)", doc_id, len(elements))

        # Re-initialize engines for new document
        self.geo_engine   = GeometryEngine()
        self.rec_engine   = RecurrenceEngine(
            spatial_tolerance=self.cfg.spatial_tolerance,
            text_jaccard_threshold=self.cfg.jaccard_threshold,
        )
        self.freq_engine  = FrequencyEngine()
        self.matrix_engine = MatrixEngine()
        self.graph_engine  = GraphEngine()
        self.comp_engine   = CompressionEngine(self.rec_engine, self.geo_engine)

        # E1: Spatial indexing
        self.geo_engine.add_many(elements)
        log.debug("E1 Geometry: %d elements indexed", len(elements))

        # E2: Recurrence detection (R_n = R_0)
        groups = self.rec_engine.detect(elements)
        log.debug("E2 Recurrence: %d groups, %d templates",
                  len(groups), sum(1 for g in groups if g.is_template))

        # E3: Frequency weighting  w(x) = 1/log(1+f(x))
        self.freq_engine.assign_weights(elements)
        log.debug("E3 Frequency: weights assigned")

        # E4: Matrix extraction  M[i,j] = v
        tables = self.matrix_engine.extract_from_elements(elements)
        log.debug("E4 Matrix: %d tables extracted", len(tables))

        # E5: Graph construction  G = (V, E)
        graph = self.graph_engine.build(elements)
        log.debug("E5 Graph: %d nodes, %d edges", len(graph.nodes), len(graph.edges))

        # E6: Symbolic compression  D = {T, R_n, Δ}
        compressed = None
        if self.cfg.enable_compression:
            compressed = self.comp_engine.compress(elements, doc_id)
            log.debug("E6 Compression: %.1f%% token reduction",
                      compressed.stats.get("savings_pct", 0))

        # E7: Embeddings (optional)
        if self.cfg.use_embeddings and self.embedder:
            self.retriever.embed_elements(elements)
            log.debug("Embeddings computed for %d elements", len(elements))

        # Update retriever references
        self.retriever.geo    = self.geo_engine
        self.retriever.freq   = self.freq_engine
        self.retriever.matrix = self.matrix_engine
        self.retriever.graph  = graph

        elapsed = (time.perf_counter() - t0) * 1000
        stats = {
            "ingestion_ms":  round(elapsed, 1),
            "elements":      len(elements),
            "tables":        len(tables),
            "graph_nodes":   len(graph.nodes),
            "graph_edges":   len(graph.edges),
            "geometry":      self.geo_engine.stats(),
            "frequency":     self.freq_engine.statistics(),
            "matrix":        self.matrix_engine.statistics(),
            "recurrence":    self.rec_engine.statistics(),
            "compression":   compressed.stats if compressed else {},
        }

        log.info(
            "Ingestion complete: %.1fms | %d tables | %d graph edges | %.1f%% compressed",
            elapsed, len(tables), len(graph.edges),
            compressed.stats.get("savings_pct", 0) if compressed else 0,
        )

        return ProcessedDocument(
            doc_id     = doc_id,
            filename   = filename,
            elements   = elements,
            graph      = graph,
            compressed = compressed,
            stats      = stats,
            _geometry  = self.geo_engine,
            _frequency = self.freq_engine,
            _matrix    = self.matrix_engine,
            _recurrence= self.rec_engine,
        )

    # ──────────────────────────────────────────────────────────────
    # Engines 7–9: Query Pipeline
    # ──────────────────────────────────────────────────────────────

    async def query(
        self,
        doc:          ProcessedDocument,
        question:     str,
        top_k:        int              = None,
        query_pages:  Optional[list[int]] = None,
        section_hint: Optional[str]       = None,
        history:      Optional[list[dict]] = None,
    ) -> MDIEResponse:
        """
        Full query pipeline:
            E7: HybridRetriever   — R = αS + βG + γF + δM
            E8: ContextBuilder    — Token-budget knapsack
            E9: LLMInterface      — Grounded reasoning + citations
        """
        k = top_k or self.cfg.top_k
        t0 = time.perf_counter()
        log.info("Query: '%s'", question[:80])

        # E7: Hybrid retrieval
        retrieval: RetrievalContext = self.retriever.retrieve(
            query=question,
            elements=doc.elements,
            top_k=k,
            query_pages=query_pages,
            section_hint=section_hint,
        )

        # MMR diversity
        if self.cfg.use_mmr and len(retrieval.results) > 4:
            retrieval.results = self.retriever.mmr(
                retrieval.results,
                lambda_=self.cfg.mmr_lambda,
                top_k=k,
            )

        # E8: Context building
        built: BuiltContext = self.context_builder.build(
            query=question,
            retrieval=retrieval,
            history=history,
        )

        # Element map for citation resolution
        elements_map = {e.element_id: e for e in doc.elements}

        # E9: LLM reasoning
        response: MDIEResponse = await self.llm_engine.reason(
            messages     = built.messages,
            source_map   = built.source_map,
            elements_map = elements_map,
            table_answers= built.table_answers,
            max_tokens   = self.cfg.llm_max_tokens,
        )

        total_ms = (time.perf_counter() - t0) * 1000
        log.info(
            "Query complete: confidence=%.2f citations=%d total_latency=%.0fms",
            response.confidence, len(response.citations), total_ms,
        )

        return response

    async def stream_query(
        self,
        doc:          ProcessedDocument,
        question:     str,
        top_k:        int              = None,
        history:      Optional[list[dict]] = None,
    ) -> AsyncGenerator[dict, None]:
        """Streaming query pipeline — yields SSE event dicts."""
        k = top_k or self.cfg.top_k
        retrieval = self.retriever.retrieve(question, doc.elements, top_k=k)
        if self.cfg.use_mmr:
            retrieval.results = self.retriever.mmr(retrieval.results, top_k=k)
        built     = self.context_builder.build(question, retrieval, history)
        elements_map = {e.element_id: e for e in doc.elements}

        async for event in self.llm_engine.stream(
            built.messages, built.source_map, elements_map, built.table_answers
        ):
            yield event

    # ──────────────────────────────────────────────────────────────
    # Utility
    # ──────────────────────────────────────────────────────────────

    def compression_report(self, doc: ProcessedDocument) -> str:
        """Human-readable compression report."""
        c = doc.compressed
        if not c:
            return "Compression not enabled."
        s = c.stats
        lines = [
            "=" * 60,
            "MDIE COMPRESSION REPORT",
            "=" * 60,
            f"Document:            {doc.filename}",
            f"Original elements:   {s.get('original_elements', 0)}",
            f"Original tokens:     {s.get('original_tokens', 0):,}",
            f"Compressed tokens:   {s.get('compressed_tokens', 0):,}",
            f"Compression ratio:   {s.get('compression_ratio', 1):.3f}",
            f"Token savings:       {s.get('savings_pct', 0):.1f}%",
            f"Template groups:     {s.get('template_groups', 0)}",
            f"Unique elements:     {s.get('unique_elements', 0)}",
            "=" * 60,
        ]
        return "\n".join(lines)

    def retrieval_explain(self, doc: ProcessedDocument, question: str, top_k: int = 5) -> str:
        """Explain retrieval scores for debugging."""
        retrieval = self.retriever.retrieve(question, doc.elements, top_k=top_k)
        lines = [f"Retrieval Explanation: '{question}'", ""]
        for r in retrieval.results:
            lines.append(r.explain())
        w = retrieval.weights_used
        lines.append(f"\nWeights: α={w.get('alpha',0):.2f} β={w.get('beta',0):.2f} "
                     f"γ={w.get('gamma',0):.2f} δ={w.get('delta',0):.2f}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────

def create_pipeline(
    model_name:    str             = "mock",
    use_embeddings: bool           = False,
    llm_client     = None,
    embedder       = None,
    config_overrides: dict         = None,
) -> MDIEPipeline:
    """
    Convenience factory for creating an MDIEPipeline.

    Examples:
        pipeline = create_pipeline()                          # dev mode, no keys needed
        pipeline = create_pipeline("gpt-4o", llm_client=openai_client)
        pipeline = create_pipeline(use_embeddings=True, embedder=st_model)
    """
    cfg = MDIEConfig(
        model_name=model_name,
        use_embeddings=use_embeddings,
    )
    if config_overrides:
        for k, v in config_overrides.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
    return MDIEPipeline(config=cfg, llm_client=llm_client, embedder=embedder)
