"""
AEGIS-AMDI-OS — Universal Export Object Schema
================================================
UEO — The standard format for exporting to any AI agent.
"""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, computed_field

from src.models.geometry_object import BoundingBox, ElementType
from src.models.context_object import Citation


class ExportFormat(str, Enum):
    """Output format."""
    JSON = "json"
    MARKDOWN = "markdown"
    YAML = "yaml"
    XML = "xml"
    HTML = "html"
    AGENT_NATIVE = "agent_native"


class AgentType(str, Enum):
    """Target AI agent."""
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    LOCAL = "local"
    AUTO = "auto"


class ExportMetadata(BaseModel):
    """Document-level metadata for export."""
    document_name: str
    pages: int
    language: str = "en"
    document_type: str = "unknown"
    doc_id: str
    total_elements: int = 0
    total_tables: int = 0
    total_templates: int = 0
    total_graph_nodes: int = 0
    total_graph_edges: int = 0
    export_timestamp: float = 0.0
    amdi_version: str = "1.0.0"


class ExportSummary(BaseModel):
    """Document summary section of UEO."""
    title: str
    abstract: str = ""
    key_topics: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    entities: list[dict] = Field(default_factory=list)
    sections: list[dict] = Field(default_factory=list)
    sentiment: dict[str, float] = Field(default_factory=dict)


class ExportSemantic(BaseModel):
    """Semantic layer export."""
    topics: list[dict] = Field(default_factory=list)
    keywords: list[dict] = Field(default_factory=list)
    entities: list[dict] = Field(default_factory=list)


class ExportGeometry(BaseModel):
    """Geometry layer export."""
    important_regions: list[dict] = Field(default_factory=list)
    section_locations: list[dict] = Field(default_factory=list)
    layout_summary: dict = Field(default_factory=dict)


class ExportTable(BaseModel):
    """A single table for export."""
    name: str
    page: int
    headers: list[str]
    data: list[list[Any]]
    shape: list[int]
    computed_metrics: dict[str, Any] = Field(default_factory=dict)
    element_id: str = ""


class ExportMatrix(BaseModel):
    """Matrix layer export."""
    tables: list[ExportTable] = Field(default_factory=list)
    n_tables: int = 0


class ExportGraphNode(BaseModel):
    """Graph node for export."""
    id: str
    type: str
    label: str = ""
    page: int | None = None


class ExportGraphEdge(BaseModel):
    """Graph edge for export."""
    src: str
    dst: str
    type: str = "follows"
    weight: float = 1.0


class ExportGraph(BaseModel):
    """Graph layer export."""
    nodes: list[ExportGraphNode] = Field(default_factory=list)
    edges: list[ExportGraphEdge] = Field(default_factory=list)
    n_nodes: int = 0
    n_edges: int = 0
    key_relationships: list[dict] = Field(default_factory=list)


class ExportTemplate(BaseModel):
    """Template layer export."""
    templates: list[dict] = Field(default_factory=list)
    n_templates: int = 0
    dominant_template_id: str = ""


class ExportKeyPoint(BaseModel):
    """A key point/insight for export."""
    text: str
    page: int
    section: str | None = None
    importance: float = 0.0
    citations: list[Citation] = Field(default_factory=list)


class ExportConfidence(BaseModel):
    """Confidence scores."""
    overall: float = 0.0
    semantic: float = 0.0
    numerical: float = 0.0
    structural: float = 0.0
    retrieval: float = 0.0
    calibration_method: str = "bayesian"


class ExportObject(BaseModel):
    """
    Universal Export Object (UEO).

    The standard format for sending AMDI analysis to any AI agent.
    Compatible with ChatGPT, Claude, Gemini, DeepSeek, Qwen, and local LLMs.
    """

    # ===== Identity =====
    ueo_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_target: AgentType = AgentType.AUTO
    export_format: ExportFormat = ExportFormat.JSON

    # ===== Core =====
    metadata: ExportMetadata
    query: str
    document_summary: ExportSummary

    # ===== Layers =====
    semantic: ExportSemantic = Field(default_factory=ExportSemantic)
    geometry: ExportGeometry = Field(default_factory=ExportGeometry)
    matrix: ExportMatrix = Field(default_factory=ExportMatrix)
    graph: ExportGraph = Field(default_factory=ExportGraph)
    template: ExportTemplate = Field(default_factory=ExportTemplate)

    # ===== Content =====
    key_points: list[ExportKeyPoint] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)

    # ===== Confidence =====
    confidence: ExportConfidence = Field(default_factory=ExportConfidence)

    # ===== Metrics =====
    tokens_used: int = 0
    export_size_bytes: int = 0

    # ===== Metadata =====
    metadata_extra: dict[str, Any] = Field(default_factory=dict)

    # ===== Computed =====
    @computed_field
    @property
    def n_citations(self) -> int:
        return len(self.citations)

    @computed_field
    @property
    def n_key_points(self) -> int:
        return len(self.key_points)

    # ===== Methods =====
    def to_dict(self) -> dict[str, Any]:
        """Export to dictionary."""
        return self.model_dump(mode="json", exclude_none=True)

    def to_json(self, indent: int = 2) -> str:
        """Export to JSON string."""
        return self.model_dump_json(indent=indent, exclude_none=True)

    def to_markdown(self) -> str:
        """Export as Markdown document."""
        lines = [
            f"# {self.metadata.document_name}",
            "",
            f"**Pages**: {self.metadata.pages} | **Language**: {self.metadata.language}",
            f"**Type**: {self.metadata.document_type} | **Doc ID**: `{self.metadata.doc_id}`",
            "",
            "## Query",
            f"> {self.query}",
            "",
            "## Summary",
            self.document_summary.abstract or "No abstract available.",
            "",
        ]
        if self.document_summary.key_topics:
            lines.append("**Key Topics**: " + ", ".join(self.document_summary.key_topics))
        if self.document_summary.keywords:
            lines.append("")
            lines.append("**Keywords**: " + ", ".join(self.document_summary.keywords))
        # Key points
        if self.key_points:
            lines.extend(["", "## Key Findings"])
            for i, kp in enumerate(self.key_points, 1):
                cite = f" [p{kp.page}"
                if kp.section:
                    cite += f", §{kp.section}"
                cite += "]"
                lines.append(f"{i}. {kp.text}{cite}")
        # Tables
        if self.matrix.tables:
            lines.extend(["", "## Tables"])
            for tbl in self.matrix.tables[:5]:
                lines.extend([
                    f"### {tbl.name}",
                    f"*Page {tbl.page}*",
                    "",
                    "| " + " | ".join(tbl.headers) + " |",
                    "|" + "|".join("---" for _ in tbl.headers) + "|",
                ])
                for row in tbl.data[:20]:
                    lines.append("| " + " | ".join(str(c) for c in row) + " |")
                if tbl.computed_metrics:
                    lines.append("")
                    lines.append("**Computed:** " + ", ".join(
                        f"{k}={v}" for k, v in tbl.computed_metrics.items()
                    ))
                lines.append("")
        # Citations
        if self.citations:
            lines.extend(["", "## Citations"])
            for i, c in enumerate(self.citations[:20], 1):
                cite = f"[{i}] Page {c.page}"
                if c.section:
                    cite += f", §{c.section}"
                cite += f" (confidence: {c.confidence:.2f})"
                lines.append(cite)
                lines.append(f"    {c.snippet[:150]}")
        # Confidence
        lines.extend([
            "", "## Confidence",
            f"- **Overall**: {self.confidence.overall:.3f}",
            f"- **Semantic**: {self.confidence.semantic:.3f}",
            f"- **Numerical**: {self.confidence.numerical:.3f}",
            f"- **Structural**: {self.confidence.structural:.3f}",
            f"- **Retrieval**: {self.confidence.retrieval:.3f}",
            "",
        ])
        return "\n".join(lines)

    model_config = {"json_schema_extra": {
        "example": {
            "metadata": {
                "document_name": "Q4_Report.pdf",
                "pages": 200,
                "language": "en",
                "document_type": "Financial Report",
                "doc_id": "doc-123",
            },
            "query": "What is the total revenue?",
            "document_summary": {
                "title": "Q4 2024 Financial Report",
                "abstract": "Strong performance.",
            },
            "matrix": {
                "tables": [{
                    "name": "Regional Sales",
                    "page": 12,
                    "headers": ["Region", "2024", "2025"],
                    "data": [["India", 300, 500]],
                    "shape": [1, 3],
                }],
                "n_tables": 1,
            },
            "confidence": {
                "overall": 0.95,
                "semantic": 0.93,
                "numerical": 0.98,
                "structural": 0.90,
                "retrieval": 0.95,
            },
        }
    }}
