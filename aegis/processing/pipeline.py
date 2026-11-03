"""
aegis.processing.pipeline
=========================
Central end-to-end document processing pipeline combining validation, extraction,
layout analysis, reading order, table reconstruction, and field-level provenance.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import fitz

from aegis.processing.extraction import NativePDFExtractor, OCRExtractor
from aegis.processing.layout import LayoutDetector
from aegis.processing.models import (
    DocumentProcessingResult,
    ExtractionMethod,
    PageTextExtraction,
    ProcessingError,
    ProcessingStatus,
    ResourceUsage,
)
from aegis.processing.provenance import (
    DocumentLineage,
    FieldProvenanceTracker,
    ProvenanceInvariantValidator,
)
from aegis.processing.reading_order import ReadingOrderResolver
from aegis.processing.security.sandbox import ProcessingSandbox
from aegis.processing.tables import TableExtractor
from aegis.processing.validation import FileValidator, ResourceLimitsConfig


class DocumentProcessingPipeline:
    """Unified document intelligence processing pipeline."""

    def __init__(
        self,
        limits: Optional[ResourceLimitsConfig] = None,
        timeout_seconds: float = 45.0,
        ocr_dpi: int = 300
    ):
        self.limits = limits or ResourceLimitsConfig(timeout_seconds=timeout_seconds)
        self.validator = FileValidator(limits=self.limits)
        self.sandbox = ProcessingSandbox(timeout_seconds=timeout_seconds)
        self.native_extractor = NativePDFExtractor()
        self.ocr_extractor = OCRExtractor(dpi=ocr_dpi)
        self.layout_detector = LayoutDetector()
        self.reading_resolver = ReadingOrderResolver()

    def process_document(
        self,
        file_path: Union[str, Path],
        document_id: Optional[str] = None,
        processing_run_id: Optional[str] = None
    ) -> DocumentProcessingResult:
        """Process document through validation, extraction, layout, reading order, and table stages."""
        p = Path(file_path)
        doc_id = document_id or p.stem.upper().replace("-", "_")
        run_id = processing_run_id or f"RUN-{uuid.uuid4().hex[:12].upper()}"

        # 1. Pre-processing file validation
        val_res = self.validator.validate_file(p)
        if not val_res.is_valid:
            return DocumentProcessingResult(
                document_id=doc_id,
                processing_run_id=run_id,
                status=val_res.status,
                page_count=0,
                pages=[],
                error=val_res.error,
                resource_usage=ResourceUsage(elapsed_ms=0.5),
                completed_stages=[],
                failed_stages=["file_validation"],
            )

        # 2. Execute full pipeline within sandbox
        return self.sandbox.execute_bounded(
            self._execute_pipeline_core,
            doc_id,
            run_id,
            file_path=p,
            page_count=val_res.page_count,
        )

    def _execute_pipeline_core(
        self,
        file_path: Path,
        document_id: str,
        processing_run_id: str,
        page_count: int
    ) -> DocumentProcessingResult:
        """Internal execution core running inside sandbox."""
        completed_stages: List[str] = ["file_validation"]
        failed_stages: List[str] = []
        pages_output: List[Dict[str, Any]] = []

        doc = fitz.open(str(file_path))

        # Provenance tracker
        tracker = FieldProvenanceTracker(processing_run_id=processing_run_id, document_id=document_id)

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            fitz_page = doc[page_idx]
            p_width = fitz_page.rect.width
            p_height = fitz_page.rect.height

            # Stage A: Text Extraction (digital vs scanned)
            if self.native_extractor.is_digital_page(fitz_page):
                extraction = self.native_extractor.extract_page(
                    fitz_page, document_id=document_id, page_number=page_num
                )
            else:
                img = self.ocr_extractor.render_page_image(fitz_page)
                extraction = self.ocr_extractor.extract_image(
                    img, document_id=document_id, page_number=page_num
                )

            # Stage B: Layout Analysis
            regions = self.layout_detector.detect_regions(
                extraction, page_width=p_width, page_height=p_height
            )

            # Stage C: Reading Order
            order_res = self.reading_resolver.resolve(
                regions, document_id=document_id, page_number=page_num
            )

            # Stage D: Table Reconstruction
            tables = TableExtractor.extract_from_fitz_page(
                fitz_page, document_id=document_id, page_number=page_num
            )

            pages_output.append({
                "page_number": page_num,
                "extraction": extraction.to_schema_dict(),
                "layout_regions": [r.to_schema_dict() for r in regions],
                "reading_order": order_res.to_schema_dict(),
                "tables": [t.to_schema_dict() for t in tables],
            })

        doc.close()

        completed_stages.extend(["extraction", "layout_analysis", "reading_order", "table_reconstruction"])

        return DocumentProcessingResult(
            document_id=document_id,
            processing_run_id=processing_run_id,
            status=ProcessingStatus.SUCCESS,
            page_count=len(pages_output),
            pages=pages_output,
            resource_usage=ResourceUsage(),
            completed_stages=completed_stages,
            failed_stages=failed_stages,
        )
