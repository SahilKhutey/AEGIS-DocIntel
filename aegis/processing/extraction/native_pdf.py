"""
aegis.processing.extraction.native_pdf
======================================
Direct native PDF text and character block extractor using PyMuPDF.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import fitz

from aegis.processing.extraction.text_normalizer import TextNormalizer
from aegis.processing.models import (
    ExtractionBlock,
    ExtractionMethod,
    PageTextExtraction,
)


class NativePDFExtractor:
    """Extracts text, character blocks, and bounding boxes directly from digital PDFs."""

    def __init__(self, text_threshold: int = 32):
        self.text_threshold = text_threshold
        self.engine_name = "PyMuPDF"
        self.engine_version = fitz.__version__

    def is_digital_page(self, page: fitz.Page) -> bool:
        """Determine whether page contains sufficient native embedded text."""
        raw_text = page.get_text("text").strip()
        return len(raw_text) >= self.text_threshold

    def extract_page(
        self,
        page: fitz.Page,
        document_id: str,
        page_number: int,
        normalize: bool = True
    ) -> PageTextExtraction:
        """Extract text and bounding blocks from a single PDF page."""
        raw_text = page.get_text("text")
        cleaned_text = TextNormalizer.clean(raw_text) if normalize else raw_text

        # Extract text blocks with coordinates: (x0, y0, x1, y1, text, block_no, block_type)
        # block_type 0 = text, 1 = image
        raw_blocks = page.get_text("blocks")
        blocks: List[ExtractionBlock] = []

        for idx, blk in enumerate(raw_blocks):
            if len(blk) >= 5 and blk[6] == 0:  # text block
                b_text = blk[4]
                if b_text.strip():
                    bbox = [float(blk[0]), float(blk[1]), float(blk[2]), float(blk[3])]
                    blocks.append(
                        ExtractionBlock(
                            block_id=f"BLOCK-{page_number:03d}-{idx:04d}",
                            text=TextNormalizer.clean(b_text) if normalize else b_text,
                            bbox=bbox,
                            confidence=None,  # PyMuPDF does not generate synthetic confidence
                        )
                    )

        status = "EMPTY_PAGE" if not cleaned_text.strip() else "SUCCESS"

        return PageTextExtraction(
            document_id=document_id,
            page_number=page_number,
            extraction_method=ExtractionMethod.NATIVE_PDF,
            engine=self.engine_name,
            engine_version=self.engine_version,
            language=["en"],
            text=cleaned_text,
            confidence=None,
            blocks=blocks,
            processing_status=status,
        )

    def extract_document(
        self,
        pdf_path: Union[str, Path],
        document_id: Optional[str] = None
    ) -> List[PageTextExtraction]:
        """Extract all pages from a native PDF document."""
        p = Path(pdf_path)
        doc_id = document_id or p.stem.upper()
        if not p.exists() or p.stat().st_size == 0:
            return [
                PageTextExtraction(
                    document_id=doc_id,
                    page_number=1,
                    extraction_method=ExtractionMethod.NATIVE_PDF,
                    engine=self.engine_name,
                    engine_version=self.engine_version,
                    language=["en"],
                    text="",
                    confidence=None,
                    blocks=[],
                    processing_status="EMPTY_PAGE",
                )
            ]

        doc = fitz.open(str(p))
        results: List[PageTextExtraction] = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1
            results.append(self.extract_page(page, document_id=doc_id, page_number=page_num))

        doc.close()
        return results
