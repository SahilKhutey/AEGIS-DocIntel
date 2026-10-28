"""
src/engines/intelligence/contracts.py
=====================================
Data contracts for structured document intelligence, fact extraction,
cross-document comparison, and conflict detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional, Tuple

FactValueType = Literal["string", "integer", "decimal", "date", "boolean", "quantity"]
ComparisonStatus = Literal["equal", "different", "potential_conflict", "not_comparable", "needs_review"]
ConflictType = Literal["quantity_discrepancy", "date_mismatch", "obligation_conflict", "attribute_divergence"]
ExtractionStatus = Literal["completed", "partial", "failed"]


@dataclass(frozen=True, slots=True)
class EvidenceSpan:
    """Verifiable source span grounding an extracted fact in a source document."""

    document_id: str
    tenant_id: str
    chunk_id: str
    page_number: Optional[int] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    quoted_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "tenant_id": self.tenant_id,
            "chunk_id": self.chunk_id,
            "page_number": self.page_number,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "quoted_text": self.quoted_text,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceSpan:
        return cls(
            document_id=data["document_id"],
            tenant_id=data["tenant_id"],
            chunk_id=data["chunk_id"],
            page_number=data.get("page_number"),
            start_offset=data.get("start_offset"),
            end_offset=data.get("end_offset"),
            quoted_text=data.get("quoted_text", ""),
        )


@dataclass(frozen=True, slots=True)
class ExtractedFact:
    """A single normalized, provenance-backed factual assertion extracted from a document."""

    fact_id: str
    tenant_id: str
    document_id: str
    subject: str
    attribute: str
    value: Any
    raw_value: str
    value_type: FactValueType = "string"
    unit: Optional[str] = None
    period: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    evidence: Tuple[EvidenceSpan, ...] = ()
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "tenant_id": self.tenant_id,
            "document_id": self.document_id,
            "subject": self.subject,
            "attribute": self.attribute,
            "value": self.value,
            "raw_value": self.raw_value,
            "value_type": self.value_type,
            "unit": self.unit,
            "period": self.period,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "evidence": [e.to_dict() for e in self.evidence],
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExtractedFact:
        raw_evidence = data.get("evidence", [])
        evidence_spans = tuple(
            e if isinstance(e, EvidenceSpan) else EvidenceSpan.from_dict(e)
            for e in raw_evidence
        )
        return cls(
            fact_id=data["fact_id"],
            tenant_id=data["tenant_id"],
            document_id=data["document_id"],
            subject=data["subject"],
            attribute=data["attribute"],
            value=data["value"],
            raw_value=data.get("raw_value", str(data["value"])),
            value_type=data.get("value_type", "string"),
            unit=data.get("unit"),
            period=data.get("period"),
            valid_from=data.get("valid_from"),
            valid_to=data.get("valid_to"),
            evidence=evidence_spans,
            confidence=data.get("confidence"),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True, slots=True)
class FieldDefinition:
    """Schema definition for a typed attribute to extract."""

    name: str
    attribute: str
    value_type: FactValueType
    unit: Optional[str] = None
    description: str = ""
    required: bool = False
    patterns: Tuple[str, ...] = ()
    aliases: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "attribute": self.attribute,
            "value_type": self.value_type,
            "unit": self.unit,
            "description": self.description,
            "required": self.required,
            "patterns": list(self.patterns),
            "aliases": list(self.aliases),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FieldDefinition:
        return cls(
            name=data["name"],
            attribute=data["attribute"],
            value_type=data.get("value_type", "string"),
            unit=data.get("unit"),
            description=data.get("description", ""),
            required=bool(data.get("required", False)),
            patterns=tuple(data.get("patterns", ())),
            aliases=tuple(data.get("aliases", ())),
        )


@dataclass(frozen=True, slots=True)
class ExtractionSchema:
    """A target schema governing structured fact extraction."""

    schema_name: str
    schema_version: int = 1
    target_subject: str = "document"
    fields: Tuple[FieldDefinition, ...] = ()
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "target_subject": self.target_subject,
            "fields": [f.to_dict() for f in self.fields],
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExtractionSchema:
        fields = tuple(
            f if isinstance(f, FieldDefinition) else FieldDefinition.from_dict(f)
            for f in data.get("fields", ())
        )
        return cls(
            schema_name=data["schema_name"],
            schema_version=data.get("schema_version", 1),
            target_subject=data.get("target_subject", "document"),
            fields=fields,
            description=data.get("description", ""),
        )


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Result of an extraction execution on a single document."""

    status: ExtractionStatus
    document_id: str
    tenant_id: str
    facts: Tuple[ExtractedFact, ...] = ()
    errors: Tuple[str, ...] = ()
    schema_name: Optional[str] = None
    schema_version: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "document_id": self.document_id,
            "tenant_id": self.tenant_id,
            "facts": [f.to_dict() for f in self.facts],
            "errors": list(self.errors),
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExtractionResult:
        facts = tuple(
            f if isinstance(f, ExtractedFact) else ExtractedFact.from_dict(f)
            for f in data.get("facts", ())
        )
        return cls(
            status=data["status"],
            document_id=data["document_id"],
            tenant_id=data["tenant_id"],
            facts=facts,
            errors=tuple(data.get("errors", ())),
            schema_name=data.get("schema_name"),
            schema_version=data.get("schema_version"),
        )


@dataclass(frozen=True, slots=True)
class PairComparison:
    """Detailed comparison between two facts extracted from different documents."""

    subject: str
    attribute: str
    status: ComparisonStatus
    left_doc_id: str
    left_fact: ExtractedFact
    right_doc_id: str
    right_fact: ExtractedFact
    difference_summary: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "attribute": self.attribute,
            "status": self.status,
            "left_doc_id": self.left_doc_id,
            "left_fact": self.left_fact.to_dict(),
            "right_doc_id": self.right_doc_id,
            "right_fact": self.right_fact.to_dict(),
            "difference_summary": self.difference_summary,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class DocumentComparisonResult:
    """Outcome of comparing structured facts across two documents for a tenant."""

    tenant_id: str
    left_doc_id: str
    right_doc_id: str
    comparisons: Tuple[PairComparison, ...] = ()
    summary: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "left_doc_id": self.left_doc_id,
            "right_doc_id": self.right_doc_id,
            "comparisons": [c.to_dict() for c in self.comparisons],
            "summary": dict(self.summary),
        }


@dataclass(frozen=True, slots=True)
class ConflictReport:
    """Analytical conflict detected across documents within the same tenant."""

    tenant_id: str
    subject: str
    attribute: str
    conflict_type: ConflictType
    description: str
    participating_facts: Tuple[ExtractedFact, ...] = ()
    conflicting_document_ids: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "subject": self.subject,
            "attribute": self.attribute,
            "conflict_type": self.conflict_type,
            "description": self.description,
            "participating_facts": [f.to_dict() for f in self.participating_facts],
            "conflicting_document_ids": list(self.conflicting_document_ids),
        }
