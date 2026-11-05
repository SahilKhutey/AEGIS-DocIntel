"""
aegis.processing.models
=======================
Unified Pydantic data models for AEGIS document processing pipeline,
guaranteeing strict compliance with schemas/processing/*.schema.json.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExtractionMethod(str, Enum):
    NATIVE_PDF = "native_pdf"
    OCR = "ocr"
    HYBRID = "hybrid"


class ProcessingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    INVALID_FORMAT = "INVALID_FORMAT"
    CORRUPTED_DOCUMENT = "CORRUPTED_DOCUMENT"
    ENCRYPTED_DOCUMENT = "ENCRYPTED_DOCUMENT"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    TIMEOUT = "TIMEOUT"
    UNSUPPORTED_FEATURE = "UNSUPPORTED_FEATURE"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    SECURITY_REJECTED = "SECURITY_REJECTED"


class RegionType(str, Enum):
    TITLE = "title"
    SECTION_HEADER = "section_header"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    FIGURE = "figure"
    CAPTION = "caption"
    LIST = "list"
    HEADER = "header"
    FOOTER = "footer"
    FOOTNOTE = "footnote"
    FORMULA = "formula"
    FORM_FIELD = "form_field"


class ExtractionBlock(BaseModel):
    block_id: str
    text: str
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    confidence: Optional[float] = None


class PageTextExtraction(BaseModel):
    document_id: str
    page_number: int = Field(..., ge=1)
    extraction_method: ExtractionMethod
    engine: str
    engine_version: str
    language: List[str] = Field(default_factory=lambda: ["en"])
    text: str
    confidence: Optional[float] = None
    blocks: List[ExtractionBlock] = Field(default_factory=list)
    processing_status: str = "SUCCESS"

    def to_schema_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "page_number": self.page_number,
            "extraction_method": self.extraction_method.value,
            "engine": self.engine,
            "engine_version": self.engine_version,
            "language": self.language,
            "text": self.text,
            "confidence": self.confidence,
            "blocks": [b.model_dump() for b in self.blocks],
            "processing_status": self.processing_status,
        }


class CoordinateSystem(BaseModel):
    units: str = "normalized"  # normalized, points, pixels
    origin: str = "top_left"
    page_width: float
    page_height: float


class LayoutRegion(BaseModel):
    region_id: str
    document_id: str
    page_number: int = Field(..., ge=1)
    region_type: RegionType
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    coordinate_system: CoordinateSystem
    text_reference: Optional[str] = None
    confidence: Optional[float] = None

    def to_schema_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "region_type": self.region_type.value,
            "bbox": self.bbox,
            "coordinate_system": self.coordinate_system.model_dump(),
            "text_reference": self.text_reference,
            "confidence": self.confidence,
        }


class OrderRelationship(BaseModel):
    source_id: str
    target_id: str
    relation_type: str


class ReadingOrderResult(BaseModel):
    document_id: str
    page_number: int = Field(..., ge=1)
    reading_order: List[str] = Field(default_factory=list)
    ordering_method: str = "layout_graph"
    confidence: Optional[float] = None
    relationships: List[OrderRelationship] = Field(default_factory=list)

    def to_schema_dict(self) -> Dict[str, Any]:
        data = {
            "document_id": self.document_id,
            "page_number": self.page_number,
            "reading_order": self.reading_order,
            "ordering_method": self.ordering_method,
            "confidence": self.confidence,
        }
        if self.relationships:
            data["relationships"] = [r.model_dump() for r in self.relationships]
        return data


class TableCellModel(BaseModel):
    cell_id: str
    row_index: int = Field(..., ge=0)
    column_index: int = Field(..., ge=0)
    row_span: int = Field(1, ge=1)
    column_span: int = Field(1, ge=1)
    text: str
    role: str = "data"  # column_header, row_header, data, empty, summary
    bbox: List[float] = Field(..., min_length=4, max_length=4)


class TableReconstruction(BaseModel):
    table_id: str
    document_id: str
    page_number: int = Field(..., ge=1)
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    row_count: int = Field(..., ge=0)
    column_count: int = Field(..., ge=0)
    cells: List[TableCellModel] = Field(default_factory=list)
    header_rows: List[int] = Field(default_factory=lambda: [0])
    source_reference: str

    def to_schema_dict(self) -> Dict[str, Any]:
        return {
            "table_id": self.table_id,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "bbox": self.bbox,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "cells": [c.model_dump() for c in self.cells],
            "header_rows": self.header_rows,
            "source_reference": self.source_reference,
        }


class FieldProvenance(BaseModel):
    field_id: str
    field_name: str
    raw_value: str
    normalized_value: Any
    normalization_rule: str
    document_id: str
    page_number: int = Field(..., ge=1)
    region_id: Optional[str] = None
    text_block_id: Optional[str] = None
    bbox: Optional[List[float]] = None
    source_span: Optional[Dict[str, Optional[int]]] = None
    processing_run_id: str
    normalization_status: str = "SUCCESS"  # SUCCESS, AMBIGUOUS, FAILED

    def to_schema_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class ProcessingError(BaseModel):
    code: str
    stage: str
    page_number: Optional[int] = None
    category: str = "DOCUMENT_PROCESSING"
    recoverable: bool = False
    message: str


class ResourceUsage(BaseModel):
    elapsed_ms: float = 0.0
    peak_memory_bytes: Optional[int] = None
    cpu_time_ms: Optional[float] = None


class DocumentProcessingResult(BaseModel):
    document_id: str
    processing_run_id: str
    status: ProcessingStatus
    page_count: int = 0
    pages: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[ProcessingError] = None
    resource_usage: ResourceUsage = Field(default_factory=ResourceUsage)
    completed_stages: List[str] = Field(default_factory=list)
    failed_stages: List[str] = Field(default_factory=list)

    def to_schema_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "processing_run_id": self.processing_run_id,
            "status": self.status.value,
            "page_count": self.page_count,
            "pages": self.pages,
            "error": self.error.model_dump() if self.error else None,
            "resource_usage": self.resource_usage.model_dump(),
            "completed_stages": self.completed_stages,
            "failed_stages": self.failed_stages,
        }


class BenchmarkRecord(BaseModel):
    benchmark_id: str
    run_id: str
    work_package: str = "WP-05"
    capability: str
    dataset_id: str
    dataset_version: str = "1.0"
    partition_id: Optional[str] = None
    manifest_id: Optional[str] = None
    pipeline_version: str = "1.0.0"
    configuration_hash: str
    software_versions: Dict[str, str] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    resource_metrics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    execution_status: str = "COMPLETED"

    def to_schema_dict(self) -> Dict[str, Any]:
        return self.model_dump()
