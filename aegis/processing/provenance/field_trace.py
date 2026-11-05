"""
aegis.processing.provenance.field_trace
=======================================
Field-level provenance tracker linking normalized extracted fields to raw spans,
page locations, bounding boxes, and versioned normalization rules.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from aegis.processing.models import FieldProvenance


class FieldProvenanceTracker:
    """Manages field-level provenance records across document processing runs."""

    def __init__(self, processing_run_id: str, document_id: str):
        self.processing_run_id = processing_run_id
        self.document_id = document_id
        self.records: List[FieldProvenance] = []

    def record_field(
        self,
        field_name: str,
        raw_value: str,
        normalized_value: Any,
        normalization_rule: str,
        page_number: int,
        region_id: Optional[str] = None,
        text_block_id: Optional[str] = None,
        bbox: Optional[List[float]] = None,
        source_span: Optional[Dict[str, Optional[int]]] = None,
        normalization_status: str = "SUCCESS"
    ) -> FieldProvenance:
        """Create and store a field-level provenance record."""
        field_id = f"FIELD-{self.document_id}-{page_number:02d}-{len(self.records) + 1:04d}"
        prov = FieldProvenance(
            field_id=field_id,
            field_name=field_name,
            raw_value=raw_value,
            normalized_value=normalized_value,
            normalization_rule=normalization_rule,
            document_id=self.document_id,
            page_number=page_number,
            region_id=region_id,
            text_block_id=text_block_id,
            bbox=bbox,
            source_span=source_span,
            processing_run_id=self.processing_run_id,
            normalization_status=normalization_status,
        )
        self.records.append(prov)
        return prov

    def get_records(self) -> List[FieldProvenance]:
        return list(self.records)
