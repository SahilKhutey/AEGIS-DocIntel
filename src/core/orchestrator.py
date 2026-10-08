"""
orchestrator.py
===============
AEGIS-AMDI-OS · Central Orchestrator

``AMDIOrchestrator`` is the top-level entry point for document ingestion
and question-answering.  It wires together every engine and service in the
AEGIS-AMDI pipeline and exposes three public coroutines:

* :meth:`ingest`       — parse, OCR, layout-detect, and analyse a document
* :meth:`query`        — retrieve and reason over ingested knowledge
* :meth:`stream_query` — streaming variant of :meth:`query`

All I/O-heavy operations are ``async`` so the orchestrator can run inside
any event loop (FastAPI, aiohttp, standalone ``asyncio.run()``, etc.).

Typical usage
-------------
>>> orch = AMDIOrchestrator()
>>> stats  = await orch.ingest(doc)
>>> result = await orch.query("What is the main finding?", doc_id=stats["doc_id"])
>>> await orch.close()
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
import time
import traceback
import uuid
import numpy as np
from typing import Any, AsyncIterator, Dict, List, Optional

# ---------------------------------------------------------------------------
# Logging — prefer loguru, fall back to stdlib
# ---------------------------------------------------------------------------
try:
    from loguru import logger as log  # type: ignore
except ImportError:
    import logging as _logging
    log = _logging.getLogger(__name__)  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Core geometry types (always required)
# ---------------------------------------------------------------------------
from src.engines.geometry.element import (  # noqa: E402
    BoundingBox,
    ElementType,
    GeometricElement,
)

# ---------------------------------------------------------------------------
# Optional engine / service imports — all guarded with try/except
# ---------------------------------------------------------------------------

# Geometry engine
try:
    from src.engines.geometry.geometry_engine import GeometryEngine  # type: ignore
except ImportError:
    GeometryEngine = None  # type: ignore

# Recurrence engine
try:
    from src.engines.recurrence.recurrence_engine import RecurrenceEngine  # type: ignore
except ImportError:
    RecurrenceEngine = None  # type: ignore

# Frequency engine
try:
    from src.engines.frequency.frequency_engine import FrequencyEngine  # type: ignore
except ImportError:
    FrequencyEngine = None  # type: ignore

# Matrix engine
try:
    from src.engines.matrix.matrix_engine import MatrixEngine  # type: ignore
except ImportError:
    MatrixEngine = None  # type: ignore

# Template engine
try:
    from src.engines.template.template_engine import TemplateEngine  # type: ignore
except ImportError:
    TemplateEngine = None  # type: ignore

# Graph engine (requires networkx)
try:
    import networkx as _nx  # noqa: F401  # type: ignore
    from src.engines.graph.graph_engine import GraphEngine  # type: ignore
    _NX_AVAILABLE = True
except ImportError:
    GraphEngine = None  # type: ignore
    _NX_AVAILABLE = False

# Hypergraph engine (this module)
try:
    from src.engines.hypergraph.hypergraph_engine import HypergraphEngine  # type: ignore
except ImportError:
    HypergraphEngine = None  # type: ignore

# Spectral engine (this module)
try:
    from src.engines.spectral.spectral_engine import SpectralEngine  # type: ignore
except ImportError:
    SpectralEngine = None  # type: ignore

# Semantic engine
try:
    from src.engines.semantic.semantic_engine import SemanticEngine  # type: ignore
except ImportError:
    SemanticEngine = None  # type: ignore

# Embedding service
try:
    from src.engines.embeddings.embedding_service import EmbeddingService  # type: ignore
except ImportError:
    EmbeddingService = None  # type: ignore

# FAISS / vector store
try:
    from src.engines.vector_db.faiss_store import FAISSStore  # type: ignore
except ImportError:
    FAISSStore = None  # type: ignore

# Adaptive fusion engine
try:
    from src.engines.fusion.adaptive_fusion import AdaptiveFusionEngine  # type: ignore
except ImportError:
    AdaptiveFusionEngine = None  # type: ignore

# Hierarchical memory
try:
    from src.engines.memory.hierarchical_memory import HierarchicalMemory  # type: ignore
except ImportError:
    HierarchicalMemory = None  # type: ignore

# Retriever
try:
    from src.engines.retrieval.amdi_retriever import AMDIRetriever  # type: ignore
except ImportError:
    AMDIRetriever = None  # type: ignore

# Context builder
try:
    from src.engines.context.context_builder import ContextBuilder  # type: ignore
except ImportError:
    ContextBuilder = None  # type: ignore

# LLM interface
try:
    from src.engines.llm.llm_interface import LLMInterface  # type: ignore
except ImportError:
    LLMInterface = None  # type: ignore

# Document parsing
try:
    from src.engines.parsers.universal_parser import UniversalParser  # type: ignore
    _PARSER_AVAILABLE = True
except ImportError:
    UniversalParser = None  # type: ignore
    _PARSER_AVAILABLE = False

try:
    from src.engines.ocr.universal_ocr import UniversalOCR  # type: ignore
    _OCR_AVAILABLE = True
except ImportError:
    UniversalOCR = None  # type: ignore
    _OCR_AVAILABLE = False

try:
    from src.engines.layout.layout_detector import LayoutDetector  # type: ignore
    _LAYOUT_AVAILABLE = True
except ImportError:
    LayoutDetector = None  # type: ignore
    _LAYOUT_AVAILABLE = False

try:
    from src.engines.physics.information_physics import InformationPhysicsEngine
    from src.engines.topology.topology_engine import TopologyEngine
    from src.engines.tensor.tensor_engine import TensorEngine
    from src.engines.bayesian.bayesian_engine import BayesianEngine
    from src.engines.markov.markov_engine import MarkovEngine
    from src.engines.decision.decision_engine import DecisionEngine
    from src.engines.optimization.optimization_engine import OptimizationEngine
    from src.engines.economics.economics_engine import EconomicsEngine
    from src.engines.meta.meta_engine import MetaLearningEngine
    from src.engines.rl.rl_engine import RLEngine
    _MIOS_AVAILABLE = True
except ImportError:
    _MIOS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Core document data model imports
# ---------------------------------------------------------------------------
from src.models.document_object import DocumentObject
from src.core.master_state import (
    Element,
    LayerStatus,
    MasterState,
    PageRepresentation,
)
from src.core.normalized_document import (
    NormalizedBlock,
    NormalizedPage,
    NormalizedDocument,
    BlockType,
)


# ---------------------------------------------------------------------------
# Block-type → ElementType mapping
# ---------------------------------------------------------------------------

_TYPE_MAP: Dict[str, ElementType] = {
    "TEXT": ElementType.TEXT,
    "PARAGRAPH": ElementType.PARAGRAPH,
    "HEADING": ElementType.HEADING,
    "TITLE": ElementType.HEADING,
    "TABLE": ElementType.TABLE,
    "FIGURE": ElementType.FIGURE,
    "IMAGE": ElementType.FIGURE,
    "CAPTION": ElementType.CAPTION,
    "EQUATION": ElementType.EQUATION,
    "LIST": ElementType.LIST_ITEM,
    "FOOTER": ElementType.FOOTER,
    "HEADER": ElementType.HEADER,
}


# ---------------------------------------------------------------------------
# Response Wrapper Types (Dual dict and attribute access)
# ---------------------------------------------------------------------------

class IngestionStats(dict):
    """Ingestion statistics dict supporting both dict key and attribute access."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'IngestionStats' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class QueryResult(dict):
    """Query response dict supporting both dict key and attribute access."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'QueryResult' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class AMDIOrchestrator:
    """Top-level orchestrator for the AEGIS-AMDI document intelligence system.

    The orchestrator bootstraps every engine at construction time and
    exposes a simple async API for document ingestion and question answering.
    All engine instances are optional — if a dependency is not installed the
    corresponding engine is set to ``None`` and gracefully skipped.

    Parameters
    ----------
    config:
        Optional configuration object or dict.  If a ``dict`` is supplied
        its keys are accessible via ``config.get(key, default)``.  If any
        other object is supplied it is stored as-is and engines may inspect
        it directly.
    """

    def __init__(self, config: Any = None) -> None:
        self._config = config or {}
        self._closed = False

        # ---- Master document state -------------------------------------
        #
        # Phase 5: Core Schema Unification (Master State D)
        # Synchronizes all 10 representation layers (P, S, G, R, F, M, T, X, H, E)
        # into a single MasterState object per document, while preserving tenant
        # tracking (Repository Audit, Workstream R follow-up).
        self._doc_state: Dict[str, MasterState] = {}
        self._doc_tenant: Dict[str, str] = {}
        self._graph: Any = None
        self._hypergraph: Any = None
        self._templates: List[Any] = []

        # ---- Engine / service instantiation ----------------------------
        self._geometry    = self._init_engine("GeometryEngine",    GeometryEngine)
        self._recurrence  = self._init_engine("RecurrenceEngine",  RecurrenceEngine)
        self._frequency   = self._init_engine("FrequencyEngine",   FrequencyEngine)
        self._matrix      = self._init_engine("MatrixEngine",      MatrixEngine)
        self._template    = self._init_engine("TemplateEngine",    TemplateEngine)
        self._graph_eng   = self._init_engine("GraphEngine",       GraphEngine)
        self._hypergraph_eng = self._init_engine("HypergraphEngine", HypergraphEngine)
        self._spectral    = self._init_engine("SpectralEngine",    SpectralEngine)
        
        self._embedding   = self._init_engine("EmbeddingService",  EmbeddingService)
        if SemanticEngine is not None:
            self._semantic = SemanticEngine(embedder=self._embedding)
            log.debug("_init_engine: SemanticEngine initialised with embedder")
        else:
            self._semantic = None
            
        self._fusion      = self._init_engine("AdaptiveFusionEngine", AdaptiveFusionEngine)
        self._memory      = self._init_engine("HierarchicalMemory", HierarchicalMemory)
        
        if AMDIRetriever is not None:
            self._retriever = AMDIRetriever(
                embedder=self._embedding,
                geometry_engine=self._geometry,
                recurrence_engine=self._recurrence,
                frequency_engine=self._frequency,
                matrix_engine=self._matrix,
                template_engine=self._template,
                semantic_engine=self._semantic,
                graph_engine=self._graph_eng,
            )
            log.debug("_init_engine: AMDIRetriever initialised")
        else:
            self._retriever = None
            
        self._ctx_builder = self._init_engine("ContextBuilder",    ContextBuilder)
        self._llm         = self._init_engine("LLMInterface",      LLMInterface)

        # Vector store
        dim = self._cfg_get("embedding_dim", 1024)
        if FAISSStore is not None:
            self._vector_store = FAISSStore(dim=dim, collection="amdi")
        else:
            self._vector_store = None

        # ---- MIOS Engines ----------------------------------------------
        if _MIOS_AVAILABLE:
            self.physics = InformationPhysicsEngine()
            self.topology = TopologyEngine()
            self.tensor_eng = TensorEngine()
            self.bayesian = BayesianEngine()
            self.markov = MarkovEngine()
            self.decision = DecisionEngine()
            self.optimizer = OptimizationEngine()
            self.economics = EconomicsEngine()
            self.meta = MetaLearningEngine()
            self.rl = RLEngine()
        else:
            self.physics = None
            self.topology = None
            self.tensor_eng = None
            self.bayesian = None
            self.markov = None
            self.decision = None
            self.optimizer = None
            self.economics = None
            self.meta = None
            self.rl = None

        log.info(
            "AMDIOrchestrator initialised. networkx=%s, faiss=%s, parser=%s, mios=%s",
            _NX_AVAILABLE,
            self._vector_store is not None,
            _PARSER_AVAILABLE,
            _MIOS_AVAILABLE,
        )

    @property
    def _doc_elements(self) -> Dict[str, List[GeometricElement]]:
        """Dynamic backward-compatible mapping of doc_id to GeometricElements,
        backed by self._doc_state."""
        return {
            doc_id: state.get_geometric_elements()
            for doc_id, state in self._doc_state.items()
        }

    @property
    def _doc_tables(self) -> Dict[str, List[GeometricElement]]:
        """Dynamic backward-compatible mapping of doc_id to table GeometricElements,
        backed by self._doc_state."""
        return {
            doc_id: state.get_geometric_tables()
            for doc_id, state in self._doc_state.items()
        }

    @property
    def _elements(self) -> List[GeometricElement]:
        """Flattened, read-only view across all ingested documents.

        Backward-compatible accessor for any code still expecting the old
        single flat list. Unlike the pre-fix flat list, this aggregates
        across *all* ingested documents rather than only the most recently
        ingested one, and carries no tenant filtering of its own — callers
        that need tenant-scoped access should use query()/stream_query()'s
        tenant_id parameter, or get_document_elements(doc_id, tenant_id=...)
        below, rather than this unscoped view directly.
        """
        out: List[GeometricElement] = []
        for state in self._doc_state.values():
            out.extend(state.get_geometric_elements())
        return out

    @property
    def _tables(self) -> List[GeometricElement]:
        """Flattened, read-only table view across all ingested documents.
        See _elements docstring above for the same tenant-filtering caveat."""
        out: List[GeometricElement] = []
        for state in self._doc_state.values():
            out.extend(state.get_geometric_tables())
        return out

    @property
    def vector_store(self):
        """Vector store instance."""
        return self._vector_store

    @property
    def semantic_cache(self):
        """Semantic cache instance if wired."""
        return getattr(self, "_semantic_cache", None)

    @semantic_cache.setter
    def semantic_cache(self, value):
        self._semantic_cache = value

    async def delete_document(self, doc_id: str, tenant_id: Optional[str] = None) -> bool:
        """Cascading document deletion: removes state, vector store embeddings, and cache entries."""
        if doc_id in self._doc_state:
            state = self._doc_state[doc_id]
            if tenant_id and getattr(state, "tenant_id", None) and str(state.tenant_id) != str(tenant_id):
                return False
            self._doc_state.pop(doc_id, None)
        if self._vector_store is not None:
            await self._vector_store.delete(doc_id=doc_id)
        if getattr(self, "_semantic_cache", None) is not None:
            await self._semantic_cache.invalidate(doc_id=doc_id, tenant_id=tenant_id)
        return True

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def ingest(self, doc: DocumentObject) -> Dict[str, Any]:
        """Parse, analyse, and index a document.

        Pipeline stages (each is skipped gracefully if its engine is not
        available):

        1. **Parse** via ``UniversalParser``; fall back to plain-text
           normaliser.
        2. **OCR** via ``UniversalOCR`` if available.
        3. **Layout detection** via ``LayoutDetector`` if available.
        4. **Convert** ``NormalizedDocument`` → ``list[GeometricElement]``.
        5. **Run engines** sequentially:
           GeometryEngine → RecurrenceEngine → FrequencyEngine →
           MatrixEngine → TemplateEngine → GraphEngine →
           HypergraphEngine → SpectralEngine → SemanticEngine.
        6. **Embed** elements and upsert into the vector store.
        7. **Store** document summaries in ``HierarchicalMemory``.

        Parameters
        ----------
        doc:
            The document to ingest.

        Returns
        -------
        dict
            Ingestion statistics with keys:
            ``doc_id``, ``filename``, ``pages``, ``elements``, ``tables``,
            ``templates``, ``ingestion_ms``, ``compression_pct``.
        """
        self._check_open()
        t0 = time.perf_counter()
        log.info("ingest: starting doc_id=%s filename=%s", doc.doc_id, doc.filename)

        # --- Stage 1: Parse -------------------------------------------
        nd = await self._parse(doc)

        # --- Stage 2: OCR (optional) -----------------------------------
        nd = await self._ocr(nd, doc)

        # --- Stage 3: Layout detection (optional) ----------------------
        nd = await self._layout(nd, doc)

        # --- Stage 4: Convert to GeometricElements --------------------
        elements = self._to_elements(nd, tenant_id=getattr(doc, "tenant_id", "default") or "default")
        tables = [
            e for e in elements
            if getattr(e, "type", None) == ElementType.TABLE
        ]

        # --- Stage 4.5: PII & Compliance Redaction (if enabled) --------
        pii_entities_count = 0
        redactions_applied = 0
        if getattr(doc, "enable_redaction", False) or getattr(doc, "redact_pii", False):
            from src.compliance.redaction_engine import redact_elements
            elements, compliance_report = redact_elements(elements)
            pii_entities_count = len(compliance_report.entities_found)
            redactions_applied = compliance_report.redactions_applied
            tables = [e for e in elements if getattr(e, "type", None) == ElementType.TABLE]

        # --- Master State D Construction ------------------------------
        state = MasterState(doc_id=doc.doc_id)
        pages_dict: Dict[int, List[Element]] = defaultdict(list)
        for e in elements:
            p_num = max(1, getattr(e, "page", 1))
            bx = getattr(e, "bbox", None)
            x0 = max(0.0, min(1.0, float(bx.x0))) if bx else 0.0
            y0 = max(0.0, min(1.0, float(bx.y0))) if bx else 0.0
            w = max(0.0, min(1.0, float(bx.width))) if bx else 1.0
            h = max(0.0, min(1.0, float(bx.height))) if bx else 1.0
            etype = e.type.value if hasattr(e.type, "value") else str(e.type)
            pages_dict[p_num].append(
                Element(
                    x=x0,
                    y=y0,
                    w=w,
                    h=h,
                    page=p_num,
                    theta=getattr(e, "theta", 0.0),
                    element_type=etype,
                    content=e.content or "",
                    element_id=e.element_id,
                    tenant_id=getattr(e, "tenant_id", "default"),
                )
            )

        state.pages = [
            PageRepresentation(
                page_number=p_num,
                elements=p_els,
                physical_width=612.0,
                physical_height=792.0,
            )
            for p_num, p_els in sorted(pages_dict.items())
        ] if pages_dict else [PageRepresentation(page_number=1, elements=[], physical_width=612.0, physical_height=792.0)]
        state.pages_status = LayerStatus(is_hardened=True)
        state.set_geometric_elements(elements)

        # Store keyed by doc_id (does not evict any other already-ingested
        # document) and record which tenant owns this document
        self._doc_state[doc.doc_id] = state
        self._doc_tenant[doc.doc_id] = getattr(doc, "tenant_id", "default") or "default"
        log.info(
            "ingest: %d elements (%d tables) after conversion",
            len(elements),
            len(tables),
        )

        # --- Stage 5: Engine pipeline ---------------------------------
        await self._run_engines(elements, state=state)

        # --- Stage 6: Embed + store -----------------------------------
        await self._embed_and_store(elements, doc.doc_id)

        # --- Stage 7: Memory ------------------------------------------
        await self._store_memory(nd, doc.doc_id)

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        original_size = len(doc.raw_bytes)
        stored_chars = sum(len(e.content or "") for e in elements)
        compression_pct = (
            round(100.0 * (1.0 - stored_chars / max(original_size, 1)), 1)
            if original_size > 0
            else 0.0
        )

        stats = IngestionStats(
            doc_id=doc.doc_id,
            filename=doc.filename,
            pages=len({getattr(e, "page", 1) for e in elements}) or 1,
            elements=len(elements),
            tables=len(self._tables),
            templates=len(self._templates),
            ingestion_ms=elapsed_ms,
            compression_pct=compression_pct,
            pii_entities_found=pii_entities_count,
            redactions_applied=redactions_applied,
            master_state=state,
        )

        # --- Stage 8: MIOS Ingestion Space (optional) -----------------
        if _MIOS_AVAILABLE and self.physics is not None:
            try:
                positions = {}
                importances = {}
                connectivity = {}
                for idx, el in enumerate(elements):
                    bbox = getattr(el, 'bbox', None)
                    space = (bbox.x0, bbox.y0, bbox.x1, bbox.y1) if bbox else (0.0, 0.0, 1.0, 1.0)
                    entropy = getattr(el, 'entropy', 0.5)
                    relevance = 0.5
                    p_state = self.physics.register(
                        element_id=el.element_id,
                        content=el.content,
                        space=space,
                        page=el.page,
                        entropy=entropy,
                        relevance=relevance
                    )
                    positions[el.element_id] = (space[0] + space[2]) / 2.0, (space[1] + space[3]) / 2.0
                    importances[el.element_id] = p_state.energy
                    connectivity[el.element_id] = 1 + (1 if idx % 2 == 0 else 0)

                # Point-Set Topology Space
                topo_sig = self.topology.analyze(positions)
                stats['betti_0'] = topo_sig.betti_0
                stats['betti_1'] = topo_sig.betti_1

                # Spectral Layout signal
                layout_signal = np.array([p.energy for p in self.physics.particles.values()], dtype=np.float32)
                if self._spectral is not None:
                    spectral_sig = self._spectral.analyze(layout_signal)
                    stats['periodicity'] = spectral_sig.periodicity

                # Tensor Space
                raw_elements = [
                    {'page': p.page, 'section': getattr(p, 'section', 'default'), 'content': p.content}
                    for p in self.physics.particles.values()
                ]
                doc_tensor = self.tensor_eng.build_tensor(raw_elements)
                stats['tensor_shape'] = doc_tensor.shape

                # Markov transition matrix
                section_sequences = [[getattr(el, 'section', 'default') or 'default' for el in elements]]
                markov_sig = self.markov.build_transition_chain(section_sequences)
                stats['n_transition_states'] = len(markov_sig.states)
            except Exception as mios_exc:
                log.warning('MIOS Ingestion failed: %s', mios_exc, exc_info=True)

        log.info("ingest: completed %s", stats)
        return stats

    async def query(
        self,
        question: str,
        doc_id: Optional[str] = None,
        top_k: int = 12,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve relevant content and reason over it to answer *question*.

        Pipeline stages:

        1. Check ``HierarchicalMemory`` cache.
        2. Retrieve candidate elements via ``AMDIRetriever``.
        3. Build a context window via ``ContextBuilder``.
        4. Reason via ``LLMInterface``.
        5. Cache the result.

        Parameters
        ----------
        question:
            Natural-language question to answer.
        doc_id:
            Optional filter to restrict retrieval to a specific document.
            If *tenant_id* is also given and the document belongs to a
            different tenant, this raises ``PermissionError`` rather than
            silently returning another tenant's content.
        top_k:
            Maximum number of source elements to retrieve.
        tenant_id:
            Caller's tenant. When given, retrieval is scoped to documents
            owned by this tenant only — both when *doc_id* is supplied
            (ownership is checked) and when it is not (the search space is
            every document owned by this tenant, not every document in the
            application). When omitted, behavior is unscoped (matches the
            pre-fix behavior) for backward compatibility with any existing
            single-tenant caller; new callers should always pass tenant_id.

        Returns
        -------
        dict
            Response dict with keys:
            ``answer``, ``citations``, ``confidence``, ``query_type``,
            ``weights_used``, ``latency_ms``, ``table_direct``,
            ``tokens_used``, ``grounded``.
        """
        self._check_open()
        t0 = time.perf_counter()
        log.info("query: question='%s' doc_id=%s tenant_id=%s top_k=%d",
                  question, doc_id, tenant_id, top_k)

        if doc_id and tenant_id is not None:
            owner = self._doc_tenant.get(doc_id)
            if owner is not None and owner != tenant_id:
                raise PermissionError(
                    f"doc_id={doc_id!r} belongs to a different tenant; "
                    f"refusing cross-tenant access."
                )

        # --- Stage 1: Cache check -------------------------------------
        cache_key = f"{tenant_id}::{doc_id}::{question}"
        if self._memory is not None:
            try:
                cached = await self._call_maybe_async(
                    self._memory.get, cache_key
                )
                if cached is not None:
                    log.debug("query: cache hit for key=%s", cache_key)
                    cached["latency_ms"] = int(
                        (time.perf_counter() - t0) * 1000
                    )
                    return cached
            except Exception:
                log.debug("query: cache miss or memory error")

        # --- Stage 2: Retrieve ----------------------------------------
        retrieved = None
        if self._retriever is not None:
            try:
                if doc_id:
                    state = self._doc_state.get(doc_id)
                    elements = state.get_geometric_elements() if state else []
                    tables = state.get_geometric_tables() if state else []
                elif tenant_id is not None:
                    allowed_docs = {
                        d for d, t in self._doc_tenant.items() if t == tenant_id
                    }
                    elements = [
                        e
                        for d in allowed_docs
                        if d in self._doc_state
                        for e in self._doc_state[d].get_geometric_elements()
                    ]
                    tables = [
                        t
                        for d in allowed_docs
                        if d in self._doc_state
                        for t in self._doc_state[d].get_geometric_tables()
                    ]
                else:
                    # No tenant_id given: unscoped, pre-fix-compatible
                    # behavior for backward compatibility only.
                    elements = self._elements
                    tables = self._tables

                retrieved = await self._call_maybe_async(
                    self._retriever.retrieve,
                    query=question,
                    elements=elements,
                    tables=tables,
                    graph=self._graph,
                    hypergraph=self._hypergraph,
                    top_k=top_k,
                )
            except Exception as exc:
                log.warning("query: retriever error: %s", exc)

        # --- Stage 3: Context ----------------------------------------
        context: Any = None
        if self._ctx_builder is not None and retrieved is not None:
            try:
                context = await self._call_maybe_async(
                    self._ctx_builder.build,
                    question,
                    retrieved,
                )
            except Exception as exc:
                log.warning("query: context builder error: %s", exc)

        # --- Stage 4: LLM reasoning ----------------------------------
        llm_result = None
        if self._llm is not None:
            try:
                llm_result = await self._call_maybe_async(
                    self._llm.reason,
                    question,
                    context or retrieved,
                    retrieved,
                    self._tables,
                )
            except Exception as exc:
                log.warning("query: LLM error: %s", exc)
                llm_result = {
                    "answer": f"[LLM unavailable: {exc}]",
                    "confidence": 0.0,
                }

        # Convert LLMResponse object to dict if needed
        if llm_result is not None and not isinstance(llm_result, dict):
            llm_dict = {
                "answer": getattr(llm_result, "answer", ""),
                "citations": getattr(llm_result, "citations", []),
                "confidence": getattr(llm_result, "confidence", 0.0),
                "grounded": getattr(llm_result, "grounded", False),
                "tokens_used": getattr(llm_result, "input_tokens", 0) + getattr(llm_result, "output_tokens", 0),
            }
        else:
            llm_dict = llm_result or {}

        # Default weights_used and query_type if not present in llm_dict
        if "weights_used" not in llm_dict and retrieved is not None:
            llm_dict["weights_used"] = getattr(retrieved, "weights", {})

        if "query_type" not in llm_dict and retrieved is not None:
            llm_dict["query_type"] = getattr(retrieved, "query_type", "analytical")

        weights_used = llm_dict.get("weights_used", {})
        if hasattr(weights_used, "to_dict"):
            weights_used = weights_used.to_dict()

        # Assemble response
        results_list = getattr(retrieved, "results", []) if retrieved is not None else []
        retrieved_doc_id = doc_id
        if not retrieved_doc_id and results_list:
            first_el = getattr(results_list[0], "element", None)
            if first_el and getattr(first_el, "doc_id", None):
                retrieved_doc_id = first_el.doc_id

        has_table = any(
            getattr(getattr(r, "element", None), "type", None) == ElementType.TABLE
            for r in results_list
        )

        response = QueryResult({
            "doc_id": retrieved_doc_id,
            "answer": llm_dict.get("answer", ""),
            "citations": llm_dict.get("citations") if llm_dict.get("citations") is not None else [r for r in results_list[:5]],
            "confidence": llm_dict.get("confidence", 0.0),
            "confidence_label": llm_dict.get("confidence_label", "MEDIUM"),
            "query_type": llm_dict.get("query_type", "analytical"),
            "weights_used": weights_used,
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "table_direct": getattr(retrieved, "table_answers", []) if retrieved is not None else [],
            "tokens_used": llm_dict.get("tokens_used", 0),
            "grounded": llm_dict.get("grounded", bool(results_list)),
            "model": llm_dict.get("model", "mock"),
        })
        # --- Stage 5: MIOS Optimization & Economics (optional) --------
        if _MIOS_AVAILABLE and self.optimizer is not None:
            try:
                citations = response.get("citations", [])
                candidates = []
                for idx, cit in enumerate(citations):
                    if isinstance(cit, dict):
                        content = cit.get("content", "") or ""
                        el_id = cit.get("element_id", str(idx))
                    else:
                        content = getattr(cit, "content", getattr(cit, "text", "")) or ""
                        el_id = getattr(cit, "element_id", str(idx))

                    candidates.append({
                        "id": el_id,
                        "tokens": len(content.split()) * 2,
                        "value": float(response.get("confidence", 0.8)) - (idx * 0.05),
                        "latency": 0.05,
                        "memory": 1.2
                    })
                
                optimized_candidates = self.optimizer.optimize_context(
                    candidates, max_tokens=1500, max_latency_s=0.5, max_memory_mb=256.0
                )
                
                success = response.get("grounded", False)
                rating = float(response.get("confidence", 0.8))
                weights_used = response.get("weights_used", {"s": 0.5, "g": 0.5})
                
                if hasattr(weights_used, "to_dict"):
                    weights_used_dict = weights_used.to_dict()
                else:
                    weights_used_dict = weights_used if isinstance(weights_used, dict) else {}

                self.meta.log_attempt("default_category", weights_used_dict, success, rating)
                
                state = self.rl.get_state(stats_len := len(citations), True, "easy")
                action = self.rl.select_action(state)
                
                next_state = self.rl.get_state(stats_len, True, "medium")
                self.rl.learn(state, action, rating, next_state)

                e_ratios = self.economics.calculate_ratios(
                    quality=rating,
                    tokens=int(response.get("tokens_used", 200)),
                    useful_data_mb=2.5,
                    memory_mb=64.0,
                    useful_info_bytes=1024,
                    storage_bytes=5000,
                    correct_retrieved=len(optimized_candidates),
                    total_ops=max(1, len(candidates)),
                    agent_cost_usd=0.002
                )
                
                response.update({
                    "mios_ratios": {
                        "token_economics": e_ratios.token_economics,
                        "memory_economics": e_ratios.memory_economics,
                        "retrieval_economics": e_ratios.retrieval_economics
                    },
                    "mios_optimized_count": len(optimized_candidates),
                    "mios_rl_action": action,
                    "mios_query_ms": int((time.perf_counter() - t0) * 1000)
                })
            except Exception as mios_exc:
                log.warning("MIOS query optimization failed: %s", mios_exc, exc_info=True)
        # --- Stage 5: Cache result ------------------------------------
        if self._memory is not None:
            try:
                await self._call_maybe_async(self._memory.set, cache_key, response)
            except Exception as mem_err:
                log.warning("Memory caching of query result failed: %s", mem_err)

        log.info(
            "query: completed latency_ms=%d grounded=%s",
            response["latency_ms"],
            response["grounded"],
        )
        return response

    async def stream_query(self, question: str) -> AsyncIterator[str]:
        """Stream the answer token-by-token for a question.

        Delegates to ``LLMInterface.stream_reason`` if available; falls
        back to yielding the full answer from :meth:`query` in a single
        chunk.

        Parameters
        ----------
        question:
            Natural-language question to answer.

        Yields
        ------
        str
            Progressive answer tokens or text chunks.
        """
        self._check_open()

        if self._llm is not None and hasattr(self._llm, "stream_reason"):
            try:
                async for token in self._llm.stream_reason(question):
                    yield token
                return
            except Exception as exc:
                log.warning("stream_query: stream_reason failed: %s", exc)

        # Fallback: run full query and yield result in one shot
        result = await self.query(question)
        yield result.get("answer", "")

    async def close(self) -> None:
        """Shut down all engines and release resources.

        Safe to call multiple times; subsequent calls are no-ops.
        """
        if self._closed:
            return
        self._closed = True

        if self._vector_store is not None:
            try:
                await self._vector_store.close()
            except Exception as vs_err:
                log.warning("Vector store close failed: %s", vs_err)

        for attr in (
            "_geometry", "_recurrence", "_frequency", "_matrix", "_template",
            "_graph_eng", "_hypergraph_eng", "_spectral", "_semantic",
            "_embedding", "_fusion", "_memory", "_retriever", "_ctx_builder",
            "_llm",
        ):
            engine = getattr(self, attr, None)
            if engine is not None and hasattr(engine, "close"):
                try:
                    await self._call_maybe_async(engine.close)
                except Exception as close_err:
                    log.warning("Engine close failed for %s: %s", attr, close_err)

        log.info("AMDIOrchestrator: closed")

    # ------------------------------------------------------------------
    # Normalisation helpers
    # ------------------------------------------------------------------

    def _normalize(self, doc: DocumentObject) -> NormalizedDocument:
        """Fallback plain-text normaliser.

        Decodes *doc.raw_bytes* as UTF-8 (with ``errors='replace'``),
        splits on double newlines, and creates one ``NormalizedBlock``
        per non-empty paragraph.

        Parameters
        ----------
        doc:
            The raw document object.

        Returns
        -------
        NormalizedDocument
            A document with TEXT blocks only.
        """
        try:
            text = doc.raw_bytes.decode("utf-8", errors="replace")
        except Exception:
            text = ""

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        blocks: List[NormalizedBlock] = []
        for i, para in enumerate(paragraphs):
            blocks.append(
                NormalizedBlock(
                    block_id=f"{doc.doc_id}_blk_{i:04d}",
                    text=para,
                    type=BlockType.TEXT,
                    page=1,
                    bbox=None,
                    section=None,
                )
            )

        page = NormalizedPage(
            page_number=1,
            blocks=blocks,
        )

        return NormalizedDocument(
            doc_id=doc.doc_id,
            filename=doc.filename,
            pages=[page],
            metadata=doc.metadata,
        )

    def _to_elements(
        self, nd: NormalizedDocument, tenant_id: str = "default"
    ) -> List[GeometricElement]:
        """Convert a ``NormalizedDocument`` to a list of ``GeometricElement``.

        Each ``NormalizedBlock`` is mapped to a ``GeometricElement`` using
        the type lookup table ``_TYPE_MAP``.  Unknown block types fall back
        to ``ElementType.TEXT``.

        Parameters
        ----------
        nd:
            The normalised document to convert.
        tenant_id:
            Stamped onto every constructed element's ``tenant_id`` field.
            This is a defense-in-depth measure, independent of and
            redundant with the orchestrator's own document-level
            ``self._doc_tenant`` tracking (see ``ingest()``): if elements
            are ever consumed by downstream code that indexes or caches
            them outside this orchestrator's own storage (e.g. a future
            cross-document retrieval index), that code has a tenant tag
            to enforce against even if it does not go through this
            orchestrator's own query()/get_document_elements() checks.

        Returns
        -------
        list[GeometricElement]
            One element per block in document order.
        """
        elements: List[GeometricElement] = []
        blocks = nd.all_blocks() if hasattr(nd, "all_blocks") else getattr(nd, "blocks", [])
        for blk in blocks:
            btype = getattr(blk, "type", getattr(blk, "block_type", "TEXT"))
            if not isinstance(btype, str):
                btype = btype.value
            etype = _TYPE_MAP.get(btype.upper(), ElementType.TEXT)

            bbox: Optional[BoundingBox] = None
            blk_bbox = getattr(blk, "bbox", None)
            if blk_bbox is not None:
                try:
                    if hasattr(blk_bbox, "x0"):
                        bbox = BoundingBox(
                            x0=float(blk_bbox.x0),
                            y0=float(blk_bbox.y0),
                            x1=float(blk_bbox.x1),
                            y1=float(blk_bbox.y1),
                        )
                    else:
                        x0, y0, x1, y1 = blk_bbox
                        bbox = BoundingBox(
                            x0=float(x0),
                            y0=float(y0),
                            x1=float(x1),
                            y1=float(y1),
                        )
                except (TypeError, ValueError):
                    bbox = None

            el = GeometricElement(
                element_id=getattr(blk, "block_id", str(uuid.uuid4())),
                doc_id=getattr(nd, "doc_id", ""),
                tenant_id=tenant_id,
                type=etype,
                content=getattr(blk, "text", ""),
                page=getattr(blk, "page", 1),
                bbox=bbox,
            )
            section_val = getattr(blk, "section", getattr(blk, "section_id", None))
            if section_val is not None:
                el.section = section_val

            elements.append(el)

        return elements

    # ------------------------------------------------------------------
    # Internal pipeline stages
    # ------------------------------------------------------------------

    async def _parse(self, doc: DocumentObject) -> NormalizedDocument:
        """Stage 1: parse the raw document bytes into a NormalizedDocument."""
        if UniversalParser is not None:
            try:
                parser = UniversalParser()
                nd = await self._call_maybe_async(parser.parse, doc)
                if nd is not None:
                    return nd
            except Exception as exc:
                log.warning("_parse: UniversalParser failed: %s — using fallback", exc)

        return self._normalize(doc)

    async def _ocr(
        self, nd: NormalizedDocument, doc: DocumentObject
    ) -> NormalizedDocument:
        """Stage 2 (optional): apply OCR to enhance or fill in text."""
        if UniversalOCR is None:
            return nd
        try:
            ocr = UniversalOCR()
            enhanced = await self._call_maybe_async(ocr.enhance, nd, doc.raw_bytes)
            return enhanced if enhanced is not None else nd
        except Exception as exc:
            log.debug("_ocr: skipped (%s)", exc)
            return nd

    async def _layout(
        self, nd: NormalizedDocument, doc: DocumentObject
    ) -> NormalizedDocument:
        """Stage 3 (optional): run layout detection to annotate block types."""
        if LayoutDetector is None:
            return nd
        try:
            detector = LayoutDetector()
            annotated = await self._call_maybe_async(
                detector.detect, nd, doc.raw_bytes
            )
            return annotated if annotated is not None else nd
        except Exception as exc:
            log.debug("_layout: skipped (%s)", exc)
            return nd

    async def _run_engines(
        self, elements: List[GeometricElement], state: Optional[MasterState] = None
    ) -> None:
        """Stage 5: run all analytical engines sequentially.

        Engines are run in a fixed order to avoid race conditions on shared
        state.  Each engine call is wrapped in a broad exception handler so
        that a failure in one engine does not abort the entire pipeline.
        Results are recorded directly into the document's MasterState object.
        """
        # --- GeometryEngine -------------------------------------------
        if self._geometry is not None:
            try:
                await self._call_maybe_async(self._geometry.analyze, elements)
                if state is not None:
                    state.geometric_adjacency = {
                        "n_elements": len(elements),
                        "n_pages": len(state.pages),
                    }
                    state.geometric_status = LayerStatus(is_hardened=True)
            except Exception as exc:
                log.warning("GeometryEngine.analyze failed: %s", exc)

        # --- RecurrenceEngine -----------------------------------------
        if self._recurrence is not None:
            try:
                rec_res = await self._call_maybe_async(self._recurrence.detect, elements)
                if state is not None:
                    groups = getattr(rec_res, "groups", [])
                    state.recurrence_patterns = [
                        g.to_dict() if hasattr(g, "to_dict") else dict(g)
                        for g in groups
                    ] if groups else []
                    state.recurrence_status = LayerStatus(is_hardened=True)
            except Exception as exc:
                log.warning("RecurrenceEngine.detect failed: %s", exc)

        # --- FrequencyEngine ------------------------------------------
        if self._frequency is not None:
            try:
                await self._call_maybe_async(self._frequency.analyze, elements)
                if state is not None:
                    if hasattr(self._frequency, "_tf"):
                        state.frequency_weights = {
                            k: float(v) for k, v in self._frequency._tf.most_common(50)
                        }
                    state.frequency_status = LayerStatus(is_hardened=True)
            except Exception as exc:
                log.warning("FrequencyEngine.analyze failed: %s", exc)

        # --- MatrixEngine ---------------------------------------------
        if self._matrix is not None:
            try:
                mat_res = await self._call_maybe_async(self._matrix.build, elements)
                if state is not None:
                    tables_data = [
                        t.to_dict() if hasattr(t, "to_dict") else {
                            "rows": getattr(t, "n_rows", 0),
                            "cols": getattr(t, "n_cols", 0),
                        }
                        for t in (mat_res or [])
                    ]
                    state.tables = tables_data
                    state.matrix_status = LayerStatus(is_hardened=True)
            except Exception as exc:
                log.warning("MatrixEngine.build failed: %s", exc)

        # --- TemplateEngine -------------------------------------------
        if self._template is not None:
            try:
                self._templates = await self._call_maybe_async(
                    self._template.detect, elements
                ) or []
                if state is not None:
                    state.template_fingerprint = (
                        str(self._templates[0].template_id)
                        if self._templates and hasattr(self._templates[0], "template_id")
                        else None
                    )
                    state.template_status = LayerStatus(is_hardened=True)
            except Exception as exc:
                log.warning("TemplateEngine.detect failed: %s", exc)

        # --- GraphEngine (networkx) ------------------------------------
        if self._graph_eng is not None:
            try:
                self._graph = await self._call_maybe_async(
                    self._graph_eng.build, elements
                )
                if state is not None:
                    state.linkage_graph = {
                        "n_nodes": len(self._graph.nodes),
                        "n_edges": len(self._graph.edges),
                    } if self._graph and hasattr(self._graph, "nodes") else None
                    state.linkage_status = LayerStatus(is_hardened=True)
            except Exception as exc:
                log.warning("GraphEngine.build failed: %s", exc)

        # --- HypergraphEngine -----------------------------------------
        if self._hypergraph_eng is not None:
            try:
                self._hypergraph = await self._call_maybe_async(
                    self._hypergraph_eng.build,
                    elements,
                    graph=self._graph,
                )
            except Exception as exc:
                log.warning("HypergraphEngine.build failed: %s", exc)

        # --- SpectralEngine (IDF fit + entropy profiling) --------------
        if self._spectral is not None:
            try:
                self._spectral.fit_idf(elements)
                self._spectral.profile_elements(elements)
                if state is not None:
                    entropies = [getattr(e, "entropy", 0.0) for e in elements]
                    state.entropy_profile = {
                        "mean_entropy": float(np.mean(entropies)) if entropies else 0.0,
                    }
                    state.entropy_status = LayerStatus(is_hardened=True)
            except Exception as exc:
                log.warning("SpectralEngine profiling failed: %s", exc)

        # --- SemanticEngine -------------------------------------------
        if self._semantic is not None:
            try:
                await self._call_maybe_async(self._semantic.analyze, elements)
            except Exception as exc:
                log.warning("SemanticEngine.analyze failed: %s", exc)

        # --- Semantic Embeddings (Master State S Layer) ----------------
        if state is not None and self._embedding is not None:
            try:
                texts = [e.content or "" for e in elements]
                embeddings = await self._call_maybe_async(
                    self._embedding.encode_text, texts
                )
                if embeddings is not None:
                    state.semantic_embeddings = [
                        v.tolist() if hasattr(v, "tolist") else list(v)
                        for v in embeddings
                    ]
                is_mock = getattr(self._embedding, "is_mock", True)
                state.semantic_status.is_mock = is_mock
                state.semantic_status.note = (
                    "Using sentence-transformers (real encoder)."
                    if not is_mock
                    else "sentence-transformers unavailable — deterministic mock vectors in use."
                )
            except Exception as exc:
                log.warning("MasterState S embedding failed: %s", exc)

    async def _embed_and_store(
        self, elements: List[GeometricElement], doc_id: str
    ) -> None:
        """Embed elements and upsert into the vector store."""
        if self._embedding is None or self._vector_store is None:
            return
        try:
            texts = [e.content or "" for e in elements]
            embeddings = await self._call_maybe_async(
                self._embedding.encode_text, texts
            )
            if embeddings is None:
                return
            metadatas = [
                {
                    "id": e.element_id,
                    "doc_id": doc_id,
                    "type": str(getattr(e, "type", "")),
                    "page": getattr(e, "page", 1),
                    "text": (e.content or "")[:512],
                }
                for e in elements
            ]
            await self._vector_store.upsert(embeddings, metadatas)
            log.debug(
                "_embed_and_store: upserted %d vectors (doc=%s)",
                len(embeddings),
                doc_id,
            )
        except Exception as exc:
            log.warning("_embed_and_store failed: %s", exc)

    async def _store_memory(
        self, nd: NormalizedDocument, doc_id: str
    ) -> None:
        """Store document-level summary in hierarchical memory."""
        if self._memory is None:
            return
        try:
            blocks = nd.all_blocks() if hasattr(nd, "all_blocks") else getattr(nd, "blocks", [])
            summary = {
                "doc_id": doc_id,
                "filename": nd.filename,
                "block_count": len(blocks),
                "metadata": nd.metadata,
            }
            await self._call_maybe_async(
                self._memory.store, f"doc_summary:{doc_id}", summary
            )
        except Exception as exc:
            log.debug("_store_memory failed: %s", exc)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _call_maybe_async(fn: Any, *args: Any, **kwargs: Any) -> Any:
        """Call *fn* with *args*/*kwargs*, awaiting if it is a coroutine.

        This allows the orchestrator to work with both synchronous and
        async engine implementations without code duplication.

        Parameters
        ----------
        fn:
            The callable (sync or async) to invoke.
        *args, **kwargs:
            Forwarded to *fn*.

        Returns
        -------
        Any
            The return value of *fn*.
        """
        result = fn(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _init_engine(self, name: str, cls: Any) -> Any:
        """Instantiate *cls* or return ``None`` if unavailable.

        Parameters
        ----------
        name:
            Human-readable engine name (for logging).
        cls:
            Engine class, or ``None`` if the import failed.

        Returns
        -------
        Any
            An engine instance or ``None``.
        """
        if cls is None:
            log.debug("_init_engine: %s not available (import failed)", name)
            return None
        try:
            instance = cls()
            log.debug("_init_engine: %s initialised", name)
            return instance
        except Exception as exc:
            log.warning("_init_engine: %s failed to initialise: %s", name, exc)
            return None

    def _cfg_get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the config dict (if config is a dict)."""
        if isinstance(self._config, dict):
            return self._config.get(key, default)
        return getattr(self._config, key, default)

    def _check_open(self) -> None:
        """Raise ``RuntimeError`` if the orchestrator has been closed."""
        if self._closed:
            raise RuntimeError("AMDIOrchestrator has been closed")

    def get_document_elements(
        self, doc_id: str, tenant_id: Optional[str] = None
    ) -> list[GeometricElement]:
        """Return all elements belonging to a specific document.

        Raises ``PermissionError`` if *tenant_id* is given and does not
        match the document's owning tenant.
        """
        if tenant_id is not None:
            owner = self._doc_tenant.get(doc_id)
            if owner is not None and owner != tenant_id:
                raise PermissionError(
                    f"doc_id={doc_id!r} belongs to a different tenant."
                )
        state = self._doc_state.get(doc_id)
        return list(state.get_geometric_elements()) if state else []

    def get_document_tables(
        self, doc_id: str, tenant_id: Optional[str] = None
    ) -> list[GeometricElement]:
        """Return all table elements belonging to a specific document.

        Raises ``PermissionError`` if *tenant_id* is given and does not
        match the document's owning tenant.
        """
        if tenant_id is not None:
            owner = self._doc_tenant.get(doc_id)
            if owner is not None and owner != tenant_id:
                raise PermissionError(
                    f"doc_id={doc_id!r} belongs to a different tenant."
                )
        state = self._doc_state.get(doc_id)
        return list(state.get_geometric_tables()) if state else []

    def get_master_state(
        self, doc_id: str, tenant_id: Optional[str] = None
    ) -> Optional[MasterState]:
        """Return the MasterState for a given document.

        Raises ``PermissionError`` if *tenant_id* is given and does not match.
        """
        if tenant_id is not None:
            owner = self._doc_tenant.get(doc_id)
            if owner is not None and owner != tenant_id:
                raise PermissionError(
                    f"doc_id={doc_id!r} belongs to a different tenant."
                )
        return self._doc_state.get(doc_id)

    def get_document_templates(self, doc_id: str) -> list[Any]:
        '''Return templates representing the document layout.'''
        if self._template is not None:
            return list(self._template.templates.values())
        return self._templates


    def get_document_graph(self) -> Any:
        '''Return the global document relation graph.'''
        return self._graph

# Alias for backward compatibility
MIOSOrchestrator = AMDIOrchestrator
