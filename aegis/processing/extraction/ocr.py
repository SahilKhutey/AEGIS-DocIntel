"""
aegis.processing.extraction.ocr
===============================
Optical Character Recognition (OCR) pipeline for scanned and image-based documents.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import fitz
from PIL import Image

from aegis.processing.extraction.text_normalizer import TextNormalizer
from aegis.processing.models import (
    ExtractionBlock,
    ExtractionMethod,
    PageTextExtraction,
)

logger = logging.getLogger(__name__)


class OCRExtractor:
    """OCR engine extracting text and bounding boxes from scanned pages and images."""

    def __init__(self, dpi: int = 300, lang: str = "eng"):
        self.dpi = dpi
        self.lang = lang
        self.engine_name = "Tesseract"
        self._tesseract_available: Optional[bool] = None

    def is_engine_available(self) -> bool:
        """Check whether OCR backend engine binary is functional."""
        if self._tesseract_available is not None:
            return self._tesseract_available
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
        except Exception:
            self._tesseract_available = False
        return self._tesseract_available

    def render_page_image(self, page: fitz.Page, dpi: Optional[int] = None) -> Image.Image:
        """Render a PDF page to a PIL Image at specified DPI."""
        target_dpi = dpi or self.dpi
        zoom = target_dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")
        return Image.open(io.BytesIO(img_bytes)).convert("RGB")

    def extract_image(
        self,
        img: Image.Image,
        document_id: str,
        page_number: int = 1,
        normalize: bool = True
    ) -> PageTextExtraction:
        """Extract text from a PIL image using OCR."""
        if not self.is_engine_available():
            # Graceful degraded extraction when external OCR binary is unavailable
            return PageTextExtraction(
                document_id=document_id,
                page_number=page_number,
                extraction_method=ExtractionMethod.OCR,
                engine=f"{self.engine_name}-Unavailable",
                engine_version="0.0.0",
                language=[self.lang],
                text="",
                confidence=None,
                blocks=[],
                processing_status="EXTRACTION_FAILED",
            )

        import pytesseract

        try:
            data = pytesseract.image_to_data(
                img,
                lang=self.lang,
                output_type=pytesseract.Output.DICT
            )
            n_boxes = len(data["text"])
            blocks: List[ExtractionBlock] = []
            extracted_words = []
            confidences = []

            for i in range(n_boxes):
                word = data["text"][i].strip()
                conf_val = float(data["conf"][i])

                if word and conf_val >= 0:
                    x0 = float(data["left"][i])
                    y0 = float(data["top"][i])
                    x1 = x0 + float(data["width"][i])
                    y1 = y0 + float(data["height"][i])

                    norm_conf = conf_val / 100.0  # normalize 0..100 to 0.0..1.0
                    confidences.append(norm_conf)
                    extracted_words.append(word)

                    blocks.append(
                        ExtractionBlock(
                            block_id=f"OCR-{page_number:03d}-{i:04d}",
                            text=word,
                            bbox=[x0, y0, x1, y1],
                            confidence=norm_conf,
                        )
                    )

            full_text = " ".join(extracted_words)
            cleaned_text = TextNormalizer.clean(full_text) if normalize else full_text
            avg_conf = sum(confidences) / len(confidences) if confidences else None

            status = "EMPTY_PAGE" if not cleaned_text.strip() else "SUCCESS"

            return PageTextExtraction(
                document_id=document_id,
                page_number=page_number,
                extraction_method=ExtractionMethod.OCR,
                engine=self.engine_name,
                engine_version="pytesseract",
                language=[self.lang],
                text=cleaned_text,
                confidence=avg_conf,
                blocks=blocks,
                processing_status=status,
            )

        except Exception as exc:
            logger.error(f"OCR execution failed on page {page_number}: {exc}")
            return PageTextExtraction(
                document_id=document_id,
                page_number=page_number,
                extraction_method=ExtractionMethod.OCR,
                engine=self.engine_name,
                engine_version="pytesseract",
                language=[self.lang],
                text="",
                confidence=None,
                blocks=[],
                processing_status="EXTRACTION_FAILED",
            )
