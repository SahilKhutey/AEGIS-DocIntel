"""
src/models/evidence_object.py
=============================
Canonical data models for extraction fidelity, source provenance,
and evidence-grounded retrieval.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SourceLocation:
    """Canonical source document location metadata preserving full provenance."""
    document_id: str
    page_number: Optional[int]
    element_id: str
    section_path: Tuple[str, ...]
    source_format: str


@dataclass(frozen=True)
class NormalizedElement:
    """Canonical representation of an extracted element across all formats."""
    element_id: str
    kind: str  # "heading", "paragraph", "table", "table_cell", "list_item", "caption", "footnote", "image", "formula"
    content: str
    location: SourceLocation
    reading_order: int
    bounding_box: Optional[Tuple[float, float, float, float]] = None
    parent_id: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedEvidence:
    """Canonical representation of retrieved evidence preserving source provenance."""
    document_id: str
    chunk_id: str
    text: str
    page_number: Optional[int]
    section_path: Tuple[str, ...]
    retrieval_score: float
    source_format: str = "pdf"


@dataclass(frozen=True)
class CitationValidationResult:
    """Verification result for answer grounding and citation integrity."""
    is_valid: bool
    total_citations: int
    valid_citations: int
    invalid_citations: List[Dict[str, Any]]
    details: str = "All citations verified against retrieved evidence."


def validate_citations(
    citations: List[Any],
    retrieved_evidence: List[RetrievedEvidence],
    tenant_id: str = "",
) -> CitationValidationResult:
    """
    Verifies that every citation in the answer references an actual chunk or document
    in the retrieved evidence set. Flags invented, ungrounded, or cross-document citations.
    """
    if not citations:
        return CitationValidationResult(
            is_valid=True,
            total_citations=0,
            valid_citations=0,
            invalid_citations=[],
            details="No citations to validate.",
        )

    evidence_chunk_ids = {e.chunk_id for e in retrieved_evidence if e.chunk_id}
    evidence_doc_ids = {e.document_id for e in retrieved_evidence if e.document_id}
    chunk_to_doc = {e.chunk_id: e.document_id for e in retrieved_evidence if e.chunk_id}

    invalid: List[Dict[str, Any]] = []
    for idx, c in enumerate(citations):
        if isinstance(c, dict):
            c_chunk = c.get("chunk_id")
            c_doc = c.get("doc_id") or c.get("document_id")
        else:
            c_chunk = getattr(c, "chunk_id", None)
            c_doc = getattr(c, "doc_id", None) or getattr(c, "document_id", None)

        if not c_chunk and not c_doc:
            invalid.append({
                "citation_index": idx,
                "chunk_id": c_chunk,
                "doc_id": c_doc,
                "reason": "citation contains neither chunk_id nor doc_id",
            })
        elif c_chunk and c_chunk not in evidence_chunk_ids:
            invalid.append({
                "citation_index": idx,
                "chunk_id": c_chunk,
                "doc_id": c_doc,
                "reason": "chunk_id not found in retrieved evidence",
            })
        elif c_chunk and c_doc and chunk_to_doc.get(c_chunk) != c_doc:
            invalid.append({
                "citation_index": idx,
                "chunk_id": c_chunk,
                "doc_id": c_doc,
                "reason": f"chunk_id '{c_chunk}' belongs to document '{chunk_to_doc.get(c_chunk)}', not cited document '{c_doc}'",
            })
        elif c_doc and not c_chunk and c_doc not in evidence_doc_ids:
            invalid.append({
                "citation_index": idx,
                "chunk_id": c_chunk,
                "doc_id": c_doc,
                "reason": "doc_id not found in retrieved evidence",
            })

    is_valid = len(invalid) == 0
    return CitationValidationResult(
        is_valid=is_valid,
        total_citations=len(citations),
        valid_citations=len(citations) - len(invalid),
        invalid_citations=invalid,
        details="All citations verified." if is_valid else f"{len(invalid)} ungrounded citations detected.",
    )
