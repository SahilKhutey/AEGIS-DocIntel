"""
aegis.corpus.adapters.models
============================
Canonical data representations for documents, annotations, and evaluation items.
All models strictly conform to schemas/corpus/*.schema.json.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContentInfo(BaseModel):
    uri: str
    format: str
    sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    size_bytes: Optional[int] = Field(None, ge=0)


class MetadataInfo(BaseModel):
    title: str
    document_type: str
    language: List[str] = Field(default_factory=lambda: ["en"])
    page_count: int = Field(1, ge=1)
    publication_date: Optional[str] = None
    publisher: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class RightsInfo(BaseModel):
    licence_id: str = Field(..., pattern=r"^LIC-[A-Z0-9_-]+$")
    status: str = Field("APPROVED", pattern=r"^(APPROVED|CONDITIONAL|PENDING|REJECTED)$")
    attribution_required: bool = False
    attribution_text: Optional[str] = None


class CanonicalDocument(BaseModel):
    """Normalized document representation conforming to document.schema.json."""
    document_id: str = Field(..., pattern=r"^[A-Z0-9_-]+$")
    source_id: str = Field(..., pattern=r"^SRC-[A-Z0-9_-]+$")
    dataset_id: str
    content: ContentInfo
    metadata: MetadataInfo
    rights: RightsInfo
    raw_text: Optional[str] = None
    pages: Optional[List[Dict[str, Any]]] = None

    def to_schema_dict(self) -> Dict[str, Any]:
        """Convert to dict matching document.schema.json required & allowed fields."""
        data = {
            "document_id": self.document_id,
            "source_id": self.source_id,
            "dataset_id": self.dataset_id,
            "content": {
                "uri": self.content.uri,
                "format": self.content.format,
                "sha256": self.content.sha256,
            },
            "metadata": {
                "title": self.metadata.title,
                "document_type": self.metadata.document_type,
                "language": self.metadata.language,
                "page_count": self.metadata.page_count,
            },
            "rights": {
                "licence_id": self.rights.licence_id,
                "status": self.rights.status,
                "attribution_required": self.rights.attribution_required,
            }
        }
        if self.content.size_bytes is not None:
            data["content"]["size_bytes"] = self.content.size_bytes
        if self.metadata.publication_date:
            data["metadata"]["publication_date"] = self.metadata.publication_date
        if self.metadata.publisher:
            data["metadata"]["publisher"] = self.metadata.publisher
        if self.rights.attribution_text:
            data["rights"]["attribution_text"] = self.rights.attribution_text
        return data


class BoundingBoxItem(BaseModel):
    page: int = 1
    bbox: List[float] = Field(..., min_length=4, max_length=4)  # [x0, y0, x1, y1]
    category: str
    confidence: Optional[float] = 1.0
    text: Optional[str] = None


class EvidenceSpan(BaseModel):
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    text: Optional[str] = None


class CanonicalAnnotation(BaseModel):
    """Normalized annotation representation conforming to annotation.schema.json."""
    annotation_id: str
    document_id: str
    task: str = Field(
        ...,
        pattern=r"^(document_classification|ocr_evaluation|layout_detection|entity_extraction|table_extraction|question_answering|citation_validation|document_retrieval|cross_document_analysis)$"
    )
    schema_version: str = "1.0.0"
    labels: Dict[str, Any] = Field(default_factory=dict)
    bounding_boxes: List[BoundingBoxItem] = Field(default_factory=list)
    evidence_spans: List[EvidenceSpan] = Field(default_factory=list)

    def to_schema_dict(self) -> Dict[str, Any]:
        """Convert to dict matching annotation.schema.json."""
        data = {
            "annotation_id": self.annotation_id,
            "document_id": self.document_id,
            "task": self.task,
            "schema_version": self.schema_version,
            "labels": self.labels,
            "bounding_boxes": [b.model_dump(exclude_none=True) for b in self.bounding_boxes],
            "evidence_spans": [e.model_dump(exclude_none=True) for e in self.evidence_spans],
        }
        return data


class CanonicalEvaluationItem(BaseModel):
    """Normalized evaluation item representation conforming to evaluation_item.schema.json."""
    item_id: str
    document_id: str
    task: str
    input: Dict[str, Any]
    ground_truth: Dict[str, Any]
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    annotation_version: str = "1.0.0"

    def to_schema_dict(self) -> Dict[str, Any]:
        """Convert to dict matching evaluation_item.schema.json."""
        return {
            "item_id": self.item_id,
            "document_id": self.document_id,
            "task": self.task,
            "input": self.input,
            "ground_truth": self.ground_truth,
            "evidence": self.evidence,
            "annotation_version": self.annotation_version,
        }


class ConversionReport(BaseModel):
    """Report detailing conversion execution statistics and any warnings/errors."""
    dataset_id: str
    adapter_name: str
    documents_converted: int = 0
    annotations_converted: int = 0
    evaluation_items_converted: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    success: bool = True
