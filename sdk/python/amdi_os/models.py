"""
AMDI-OS SDK data models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DocumentSummary:
    """Summary of a document."""

    document_id: str
    name: str
    file_type: str
    size_bytes: int
    page_count: int = 0
    uploaded_at: Optional[str] = None
    processed: bool = False
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentSummary":
        return cls(
            document_id=data["document_id"],
            name=data["name"],
            file_type=data["file_type"],
            size_bytes=data["size_bytes"],
            page_count=data.get("page_count", 0),
            uploaded_at=data.get("uploaded_at"),
            processed=data.get("processed", False),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Document:
    """A full document object."""

    document_id: str
    name: str
    file_type: str
    size_bytes: int
    page_count: int
    text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    engine_reports: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        return cls(
            document_id=data["document_id"],
            name=data["name"],
            file_type=data["file_type"],
            size_bytes=data["size_bytes"],
            page_count=data.get("page_count", 0),
            text=data.get("text", ""),
            metadata=data.get("metadata", {}),
            engine_reports=data.get("engine_reports", {}),
        )


@dataclass
class RetrievalHit:
    """A single retrieval hit."""

    doc_id: str
    fused_score: float
    methods_found: List[str] = field(default_factory=list)
    per_method_score: Dict[str, float] = field(default_factory=dict)
    snippet: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "RetrievalHit":
        return cls(
            doc_id=data["doc_id"],
            fused_score=data["fused_score"],
            methods_found=data.get("methods_found", []),
            per_method_score=data.get("per_method_score", {}),
            snippet=data.get("snippet", ""),
        )


@dataclass
class RetrievalResult:
    """Result of a retrieval query."""

    query: str
    hits: List[RetrievalHit]
    per_method_counts: Dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    total_candidates: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "RetrievalResult":
        return cls(
            query=data.get("query", ""),
            hits=[RetrievalHit.from_dict(h) for h in data.get("hits", [])],
            per_method_counts=data.get("per_method_counts", {}),
            latency_ms=data.get("latency_ms", 0.0),
            total_candidates=data.get("total_candidates", 0),
        )


@dataclass
class Citation:
    """A citation."""

    doc_id: str
    page: Optional[int] = None
    section: str = ""
    excerpt: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Citation":
        return cls(
            doc_id=data.get("doc_id", ""),
            page=data.get("page"),
            section=data.get("section", ""),
            excerpt=data.get("excerpt", ""),
        )


@dataclass
class UniversalExportObject:
    """Universal Export Object (UEO)."""

    system: str
    context: str
    summary: str = ""
    citations: List[Citation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    total_tokens: int = 0
    agent_specific: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

    @classmethod
    def from_dict(cls, data: dict) -> "UniversalExportObject":
        return cls(
            system=data.get("system", ""),
            context=data.get("context", ""),
            summary=data.get("summary", ""),
            citations=[Citation.from_dict(c) for c in data.get("citations", [])],
            metadata=data.get("metadata", {}),
            confidence=data.get("confidence", 0.0),
            total_tokens=data.get("total_tokens", 0),
            agent_specific=data.get("agent_specific", {}),
            version=data.get("version", "1.0.0"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system": self.system,
            "context": self.context,
            "summary": self.summary,
            "citations": [
                {
                    "doc_id": c.doc_id,
                    "page": c.page,
                    "section": c.section,
                    "excerpt": c.excerpt,
                }
                for c in self.citations
            ],
            "metadata": self.metadata,
            "confidence": self.confidence,
            "total_tokens": self.total_tokens,
            "agent_specific": self.agent_specific,
            "version": self.version,
        }


@dataclass
class ConnectorResponse:
    """Response from an AI agent connector."""

    text: str
    agent: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ConnectorResponse":
        return cls(
            text=data.get("text", ""),
            agent=data.get("agent", ""),
            model=data.get("model", ""),
            usage=data.get("usage", {}),
            finish_reason=data.get("finish_reason", "stop"),
            latency_ms=data.get("latency_ms", 0.0),
            metadata=data.get("metadata", {}),
            success=data.get("success", True),
            error=data.get("error"),
        )


@dataclass
class EngineOutput:
    """Output from an engine."""

    engine_name: str
    data: Dict[str, Any]
    confidence: float = 0.0
    latency_ms: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "EngineOutput":
        return cls(
            engine_name=data["engine_name"],
            data=data.get("data", {}),
            confidence=data.get("confidence", 0.0),
            latency_ms=data.get("latency_ms", 0.0),
        )


@dataclass
class VerificationReport:
    """Verification report."""

    passed: bool
    confidence: float
    grade: str
    citation_accuracy: float = 0.0
    fact_accuracy: float = 0.0
    hallucination_rate: float = 0.0
    issues: List[str] = field(default_factory=list)
    recommendation: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "VerificationReport":
        return cls(
            passed=data.get("passed", False),
            confidence=data.get("confidence", 0.0),
            grade=data.get("grade", "F"),
            citation_accuracy=data.get("citation_accuracy", 0.0),
            fact_accuracy=data.get("fact_accuracy", 0.0),
            hallucination_rate=data.get("hallucination_rate", 0.0),
            issues=data.get("issues", []),
            recommendation=data.get("recommendation", ""),
        )
