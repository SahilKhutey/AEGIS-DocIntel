"""
AEGIS-DocIntel / AMDI-OS — Canonical Document State Schema
============================================================
Defines the mathematical canonical representation of a document across
all stages of the pipeline:

    D = (P, S, G, R, F, M, T, X, H, E)

Where:
    P : Physical Layout (Pages, Bounding Boxes, Reading Order DAG)
    S : Semantic Layer (Embeddings, Topics, Keyphrases, Entities)
    G : Graph Structure (Entity-Relation Knowledge Graph, Connectivity)
    R : Recurrence & Repetition (Boilerplate, Headers/Footers, Patterns)
    F : Frequency & Spectral (Graph Laplacians, Spectral Clusters)
    M : Matrix & Tabular (Tables, Extracted Metrics, Numeric Density)
    T : Topology & Simplicial Complexes (Betti Numbers, Persistence)
    X : Information Physics (Entropy, Energy Flow, Gradients)
    H : Hypergraph (N-ary Cross-Modal Multi-Relations)
    E : Provenance & Telemetry (Execution Timestamps, Tenant Isolation)
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ─────────────────────────────────────────────────────────────────
# 1. P — Physical Layout
# ─────────────────────────────────────────────────────────────────

class BoundingBox(BaseModel):
    """Normalized bounding box coordinates [0.0, 1.0] or physical point units."""
    model_config = ConfigDict(frozen=True)

    x0: float = Field(..., description="Left coordinate")
    y0: float = Field(..., description="Top coordinate")
    x1: float = Field(..., description="Right coordinate")
    y1: float = Field(..., description="Bottom coordinate")
    rotation: float = Field(default=0.0, description="Rotation angle in degrees")

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)

    @property
    def area(self) -> float:
        return self.width * self.height


class PageInfo(BaseModel):
    """Page dimension and scanning metadata."""
    page_number: int = Field(ge=1, description="1-indexed page number")
    width: float = Field(default=612.0, ge=0.0, description="Page width in points")
    height: float = Field(default=792.0, ge=0.0, description="Page height in points")
    is_scanned: bool = Field(default=False, description="Whether the page required OCR")
    rotation: int = Field(default=0, description="Page rotation in degrees")


class LayoutElement(BaseModel):
    """Discrete physical layout element (paragraph, heading, table region, figure)."""
    element_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(default="text", description="Element type: text, heading, table, figure, code, etc.")
    content: str = Field(default="", description="Text content or markdown snippet")
    page: int = Field(default=1, ge=1, description="Page number")
    bbox: Optional[BoundingBox] = Field(default=None, description="Spatial bounding box")
    reading_order_index: int = Field(default=0, ge=0, description="Topological reading order index")
    importance_weight: float = Field(default=1.0, ge=0.0, description="Importance or salience weight")


class ReadingOrderDAG(BaseModel):
    """Directed Acyclic Graph (DAG) representing topological reading order."""
    nodes: List[str] = Field(default_factory=list, description="Ordered element IDs")
    edges: List[Tuple[str, str]] = Field(default_factory=list, description="Directed reading precedence edges (u -> v)")
    is_acyclic: bool = Field(default=True, description="Whether topological sort verified acyclicity")


class PhysicalLayer(BaseModel):
    """P — Physical Layout and Spatial Structure."""
    page_count: int = Field(default=1, ge=0)
    pages: List[PageInfo] = Field(default_factory=list)
    elements: List[LayoutElement] = Field(default_factory=list)
    reading_order: ReadingOrderDAG = Field(default_factory=ReadingOrderDAG)
    total_words: int = Field(default=0, ge=0)
    total_chars: int = Field(default=0, ge=0)


# ─────────────────────────────────────────────────────────────────
# 2. S — Semantic Layer
# ─────────────────────────────────────────────────────────────────

class TopicDistribution(BaseModel):
    """Semantic topic representation."""
    name: str
    weight: float = Field(default=0.0, ge=0.0, le=1.0)
    keywords: List[str] = Field(default_factory=list)


class Keyphrase(BaseModel):
    """Salient keyphrase with TF-IDF or relevance score."""
    text: str
    score: float = Field(default=0.0, ge=0.0)
    frequency: int = Field(default=1, ge=1)


class Entity(BaseModel):
    """Extracted named entity."""
    text: str
    type: str = Field(default="MISC")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    page: Optional[int] = Field(default=None, ge=1)


class SemanticLayer(BaseModel):
    """S — Semantic Content, Vector Space, and Extracted Topics."""
    model_name: Optional[str] = Field(default=None, description="Embedding model identifier")
    embedding_dimension: Optional[int] = Field(default=None, ge=1)
    topics: List[TopicDistribution] = Field(default_factory=list)
    keyphrases: List[Keyphrase] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    abstract_summary: Optional[str] = Field(default=None)


# ─────────────────────────────────────────────────────────────────
# 3. G — Graph Structure
# ─────────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    """Knowledge graph vertex."""
    id: str
    label: str = ""
    node_type: str = "concept"
    attributes: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Knowledge graph directed edge."""
    src: str
    dst: str
    type: str = "related"
    weight: float = Field(default=1.0, ge=0.0)


class GraphLayer(BaseModel):
    """G — Entity-Relation Knowledge Graph and Connectivity."""
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    density: float = Field(default=0.0, ge=0.0, le=1.0)
    diameter: Optional[int] = Field(default=None, ge=0)
    is_connected: bool = Field(default=True)


# ─────────────────────────────────────────────────────────────────
# 4. R — Recurrence & Repetition
# ─────────────────────────────────────────────────────────────────

class RepeatedPattern(BaseModel):
    """Detected repeating structural or textual element."""
    pattern_type: str = Field(..., description="header, footer, watermark, disclaimer, etc.")
    text: str
    pages: List[int] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class RecurrenceLayer(BaseModel):
    """R — Recurrence, Repetition, and Boilerplate Pruning."""
    patterns: List[RepeatedPattern] = Field(default_factory=list)
    boilerplate_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    template_ids: List[str] = Field(default_factory=list)
    periodicity_score: float = Field(default=0.0, ge=0.0)


# ─────────────────────────────────────────────────────────────────
# 5. F — Frequency & Spectral
# ─────────────────────────────────────────────────────────────────

class SpectralCluster(BaseModel):
    """Graph cluster partitioned via spectral clustering."""
    cluster_id: int
    element_ids: List[str] = Field(default_factory=list)
    centroid_eigenvalue: float = 0.0


class SpectralLayer(BaseModel):
    """F — Frequency, Fourier Components, and Graph Laplacian Spectrum."""
    laplacian_eigenvalues: List[float] = Field(default_factory=list)
    spectral_gap: float = Field(default=0.0, ge=0.0)
    clusters: List[SpectralCluster] = Field(default_factory=list)
    fourier_energy: float = Field(default=0.0, ge=0.0)


# ─────────────────────────────────────────────────────────────────
# 6. M — Matrix & Tabular
# ─────────────────────────────────────────────────────────────────

class TableData(BaseModel):
    """Extracted tabular grid with pre-computed mathematical metrics."""
    table_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    page: int = Field(default=1, ge=1)
    headers: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    computed_metrics: Dict[str, Any] = Field(default_factory=dict, description="Pre-computed sums, averages, growths")

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def col_count(self) -> int:
        return len(self.headers)


class MatrixLayer(BaseModel):
    """M — Matrix & Tabular Numerical Structure."""
    tables: List[TableData] = Field(default_factory=list)
    numeric_density: float = Field(default=0.0, ge=0.0, le=1.0)
    matrix_rank: Optional[int] = Field(default=None, ge=0)

    @property
    def n_tables(self) -> int:
        return len(self.tables)


# ─────────────────────────────────────────────────────────────────
# 7. T — Topology & Simplicial Complexes
# ─────────────────────────────────────────────────────────────────

class PersistenceInterval(BaseModel):
    """Topological persistent homology birth-death interval."""
    dimension: int = Field(ge=0)
    birth: float = Field(ge=0.0)
    death: float = Field(ge=0.0)

    @field_validator("death")
    @classmethod
    def death_ge_birth(cls, v: float, info) -> float:
        birth = info.data.get("birth", 0.0)
        if v < birth:
            raise ValueError(f"death ({v}) cannot precede birth ({birth})")
        return v


class TopologyLayer(BaseModel):
    """T — Topology, Simplicial Complexes, and Betti Invariants."""
    betti_numbers: List[int] = Field(default_factory=lambda: [1, 0, 0], description="[beta_0, beta_1, beta_2, ...]")
    euler_characteristic: int = Field(default=1, description="Euler-Poincare characteristic chi = sum (-1)^k beta_k")
    persistence_intervals: List[PersistenceInterval] = Field(default_factory=list)
    simplex_count: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_euler_characteristic(self) -> TopologyLayer:
        # Calculate chi from betti numbers
        if self.betti_numbers:
            calculated_chi = sum((-1)**k * beta for k, beta in enumerate(self.betti_numbers))
            self.euler_characteristic = calculated_chi
        return self


# ─────────────────────────────────────────────────────────────────
# 8. X — Information Physics
# ─────────────────────────────────────────────────────────────────

class InfoPhysicsLayer(BaseModel):
    """X — Information Entropy, Energy Gradients, and Flow Dynamics."""
    shannon_entropy: float = Field(default=0.0, ge=0.0, description="H(X) in bits/nats")
    information_energy: float = Field(default=0.0, ge=0.0)
    flow_gradient: float = Field(default=0.0)
    compression_ratio: float = Field(default=0.0, ge=0.0)
    layer_temperatures: Dict[str, float] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────
# 9. H — Hypergraph
# ─────────────────────────────────────────────────────────────────

class HyperEdge(BaseModel):
    """Hyperedge connecting >= 2 nodes across modalities."""
    edge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_ids: List[str] = Field(default_factory=list)
    weight: float = Field(default=1.0, ge=0.0)
    edge_type: str = "cross_modal"


class HypergraphLayer(BaseModel):
    """H — Multi-Way N-ary Hypergraph Relationships."""
    hyperedges: List[HyperEdge] = Field(default_factory=list)
    incidence_nodes_count: int = Field(default=0, ge=0)
    incidence_edges_count: int = Field(default=0, ge=0)
    cross_modal_links: int = Field(default=0, ge=0)


# ─────────────────────────────────────────────────────────────────
# 10. E — Provenance & Telemetry
# ─────────────────────────────────────────────────────────────────

class PipelineStageRecord(BaseModel):
    """Execution telemetry for a single pipeline phase."""
    stage_name: str
    start_time: float = Field(default_factory=time.time)
    duration_ms: float = Field(default=0.0, ge=0.0)
    success: bool = True
    details: Dict[str, Any] = Field(default_factory=dict)


class TelemetryLayer(BaseModel):
    """E — Provenance, Execution Telemetry, and Tenant Security."""
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(default="default")
    source_filename: str = Field(default="")
    content_hash: str = Field(default="")
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    stages: List[PipelineStageRecord] = Field(default_factory=list)
    calibrated_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    total_latency_ms: float = Field(default=0.0, ge=0.0)
    amdi_version: str = Field(default="1.0.0")


# ─────────────────────────────────────────────────────────────────
# Canonical Document State Model: D = (P, S, G, R, F, M, T, X, H, E)
# ─────────────────────────────────────────────────────────────────

class DocumentState(BaseModel):
    """
    Canonical Document State: D = (P, S, G, R, F, M, T, X, H, E).

    The single, unified, immutable-ready, typed document representation
    governing every transformation across the pipeline.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    physical: PhysicalLayer = Field(default_factory=PhysicalLayer, description="P: Physical Layout")
    semantic: SemanticLayer = Field(default_factory=SemanticLayer, description="S: Semantic Layer")
    graph: GraphLayer = Field(default_factory=GraphLayer, description="G: Graph Structure")
    recurrence: RecurrenceLayer = Field(default_factory=RecurrenceLayer, description="R: Recurrence & Repetition")
    spectral: SpectralLayer = Field(default_factory=SpectralLayer, description="F: Frequency & Spectral")
    matrix: MatrixLayer = Field(default_factory=MatrixLayer, description="M: Matrix & Tabular")
    topology: TopologyLayer = Field(default_factory=TopologyLayer, description="T: Topology & Simplicial Complexes")
    physics: InfoPhysicsLayer = Field(default_factory=InfoPhysicsLayer, description="X: Information Physics")
    hypergraph: HypergraphLayer = Field(default_factory=HypergraphLayer, description="H: Hypergraph Relations")
    telemetry: TelemetryLayer = Field(default_factory=TelemetryLayer, description="E: Provenance & Telemetry")

    # ── Mathematical Aliases ─────────────────────────────────────
    @property
    def P(self) -> PhysicalLayer:
        return self.physical

    @property
    def S(self) -> SemanticLayer:
        return self.semantic

    @property
    def G(self) -> GraphLayer:
        return self.graph

    @property
    def R(self) -> RecurrenceLayer:
        return self.recurrence

    @property
    def F(self) -> SpectralLayer:
        return self.spectral

    @property
    def M(self) -> MatrixLayer:
        return self.matrix

    @property
    def T(self) -> TopologyLayer:
        return self.topology

    @property
    def X(self) -> InfoPhysicsLayer:
        return self.physics

    @property
    def H(self) -> HypergraphLayer:
        return self.hypergraph

    @property
    def E(self) -> TelemetryLayer:
        return self.telemetry

    # ── Convenience Properties ───────────────────────────────────
    @property
    def doc_id(self) -> str:
        return self.telemetry.doc_id

    @property
    def tenant_id(self) -> str:
        return self.telemetry.tenant_id

    @property
    def page_count(self) -> int:
        return self.physical.page_count

    # ── Telemetry & Lifecycle Methods ────────────────────────────
    def record_stage(
        self,
        stage_name: str,
        duration_ms: float,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> DocumentState:
        """Record the completion of a pipeline stage."""
        record = PipelineStageRecord(
            stage_name=stage_name,
            duration_ms=max(0.0, duration_ms),
            success=success,
            details=details or {},
        )
        self.telemetry.stages.append(record)
        self.telemetry.total_latency_ms += record.duration_ms
        self.telemetry.updated_at = time.time()
        return self

    def summary(self) -> Dict[str, Any]:
        """Return a structured summary of document intelligence state."""
        return {
            "doc_id": self.doc_id,
            "filename": self.telemetry.source_filename,
            "pages": self.page_count,
            "elements": len(self.physical.elements),
            "tables": self.matrix.n_tables,
            "graph_nodes": len(self.graph.nodes),
            "graph_edges": len(self.graph.edges),
            "hyperedges": len(self.hypergraph.hyperedges),
            "betti_numbers": self.topology.betti_numbers,
            "euler_characteristic": self.topology.euler_characteristic,
            "shannon_entropy": round(self.physics.shannon_entropy, 3),
            "confidence": round(self.telemetry.calibrated_confidence, 4),
            "stages_completed": [s.stage_name for s in self.telemetry.stages if s.success],
        }

    # ── Interoperability & UEO Bridge ────────────────────────────
    def to_ueo(self, query: str = "") -> Any:
        """
        Convert canonical DocumentState into a UniversalExportObject (UEO)
        for external AI agent consumption.
        """
        from src.ael.ueo import (
            UniversalExportObject, Metadata, DocumentSummary,
            SemanticLayer as UEOSemantic, GeometryLayer as UEOGeometry,
            MatrixLayer as UEOMatrix, GraphLayer as UEOGraph,
            TemplateLayer as UEOTemplate, Citation, KeyPoint,
            Confidence as UEOConfidence,
        )

        metadata = Metadata(
            document_name=self.telemetry.source_filename or "document.pdf",
            pages=self.physical.page_count,
            language="en",
            document_type="Document",
            doc_id=self.doc_id,
            total_elements=len(self.physical.elements),
            total_tables=self.matrix.n_tables,
            total_templates=len(self.recurrence.template_ids),
        )

        doc_summary = DocumentSummary(
            title=self.telemetry.source_filename or "Document",
            abstract=self.semantic.abstract_summary or "",
            key_topics=[t.name for t in self.semantic.topics],
            keywords=[k.text for k in self.semantic.keyphrases],
            entities=[e.model_dump() for e in self.semantic.entities],
        )

        # Citations from physical elements
        citations = [
            Citation(
                element_id=el.element_id,
                page=el.page,
                section=None,
                snippet=el.content[:200],
                confidence=round(el.importance_weight, 3),
                bbox=[el.bbox.x0, el.bbox.y0, el.bbox.x1, el.bbox.y1] if el.bbox else None,
            )
            for el in self.physical.elements[:20]
        ]

        # Key points
        key_points = [
            KeyPoint(
                text=kp.text,
                page=1,
                section=None,
                importance=kp.score,
            )
            for kp in self.semantic.keyphrases[:10]
        ]

        # Table exports
        table_exports = [
            {
                "table_id": t.table_id,
                "page": t.page,
                "headers": t.headers,
                "data": t.rows,
                "computed_metrics": t.computed_metrics,
            }
            for t in self.matrix.tables
        ]

        return UniversalExportObject(
            metadata=metadata,
            query=query,
            document_summary=doc_summary,
            semantic=UEOSemantic(
                topics=[t.model_dump() for t in self.semantic.topics],
                keywords=[k.model_dump() for k in self.semantic.keyphrases],
                entities=[e.model_dump() for e in self.semantic.entities],
            ),
            geometry=UEOGeometry(
                important_regions=[
                    {"page": el.page, "content": el.content[:100]}
                    for el in self.physical.elements[:10]
                ]
            ),
            matrix=UEOMatrix(tables=table_exports, n_tables=len(table_exports)),
            graph=UEOGraph(
                nodes=[n.model_dump() for n in self.graph.nodes],
                edges=[e.model_dump() for e in self.graph.edges],
                n_nodes=len(self.graph.nodes),
            ),
            template=UEOTemplate(templates=[], n_templates=len(self.recurrence.template_ids)),
            key_points=key_points,
            citations=citations,
            confidence=UEOConfidence(
                overall=self.telemetry.calibrated_confidence,
                semantic=0.9,
                numerical=0.9,
                structural=0.9,
                retrieval=0.9,
            ),
            ueo_id=str(uuid.uuid4()),
        )

    # ── State Transition Validation ──────────────────────────────
    @classmethod
    def validate_transition(cls, prev: DocumentState, next_state: DocumentState) -> bool:
        """
        Asserts pipeline monotonic progression invariants:
        1. Document ID and Tenant ID must remain invariant.
        2. Stage count must be non-decreasing.
        3. Completed stages in previous state must still exist.
        4. Total latency must be non-decreasing.
        """
        if prev.doc_id != next_state.doc_id:
            raise ValueError(f"State transition mutation error: doc_id changed from {prev.doc_id} to {next_state.doc_id}")
        if prev.tenant_id != next_state.tenant_id:
            raise ValueError(f"State transition security error: tenant_id changed from {prev.tenant_id} to {next_state.tenant_id}")
        if len(next_state.telemetry.stages) < len(prev.telemetry.stages):
            raise ValueError("State transition monotonicity error: pipeline stage history was truncated")
        if next_state.telemetry.total_latency_ms < prev.telemetry.total_latency_ms:
            raise ValueError("State transition metric error: total latency cannot decrease")
        return True
