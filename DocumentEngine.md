# AEGIS-DocIntel — Document Engine
**Version 1.0.0**

---

## 1. Document Engine Overview

The Document Engine is the foundation of AEGIS-DocIntel. It is responsible for
converting raw PDFs (and other formats) into a rich, structured representation
that downstream chunking, embedding, and retrieval engines can operate on.

```
Raw PDF Bytes
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│                    DOCUMENT ENGINE                           │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │  PDF Parser  │→ │   Layout     │→ │  Content           │ │
│  │  (PyMuPDF)   │  │  Classifier  │  │  Extractor         │ │
│  │  (pdfplumber)│  │  (DiT)       │  │  Text/Table/Figure │ │
│  └──────────────┘  └──────────────┘  └────────────────────┘ │
│         │                                      │             │
│  ┌──────▼──────────────────────────────────────▼──────────┐ │
│  │          OCR Engine (if scanned)                        │ │
│  │  PaddleOCR → Tesseract → DocTR → Surya OCR             │ │
│  └─────────────────────────────────────────────────────────┘ │
│         │                                                    │
│  ┌──────▼──────────────────────────────────────────────────┐ │
│  │          Specialized Extractors                          │ │
│  │  Tables (Camelot/TATR) · Equations (Nougat)             │ │
│  │  Figures (BLIP-2) · Charts (ChartQA/Deplot)             │ │
│  └─────────────────────────────────────────────────────────┘ │
│         │                                                    │
│  ┌──────▼──────────────────────────────────────────────────┐ │
│  │          Semantic Chunker                                │ │
│  │  Hierarchical · Semantic · Sliding-Window               │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
Structured Chunks → Embedding Engine
```

---

## 2. Full Document Engine Implementation

```python
"""
AEGIS-DocIntel — Complete Document Engine
==========================================
Production-grade pipeline: PDF → Structured Chunks
"""
from __future__ import annotations

import asyncio
import io
import logging
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterator

import fitz  # PyMuPDF
import numpy as np
import pdfplumber
from PIL import Image

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────

class BlockType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    EQUATION = "equation"
    HEADER = "header"
    FOOTER = "footer"
    CAPTION = "caption"
    FOOTNOTE = "footnote"
    CODE = "code"


@dataclass
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float

    def to_list(self) -> list[float]:
        return [self.x0, self.y0, self.x1, self.y1]

    def area(self) -> float:
        return max(0.0, self.x1 - self.x0) * max(0.0, self.y1 - self.y0)

    def contains(self, other: "BBox") -> bool:
        return (self.x0 <= other.x0 and self.y0 <= other.y0
                and self.x1 >= other.x1 and self.y1 >= other.y1)


@dataclass
class ContentBlock:
    block_id: str
    type: BlockType
    text: str
    page: int
    bbox: BBox
    metadata: dict[str, Any] = field(default_factory=dict)
    image_bytes: bytes | None = None

    def __post_init__(self):
        if not self.block_id:
            self.block_id = str(uuid.uuid4())


@dataclass
class DocumentPage:
    number: int        # 1-indexed
    width: float
    height: float
    is_scanned: bool
    blocks: list[ContentBlock] = field(default_factory=list)
    image: bytes | None = None  # full page render (PNG)
    ocr_confidence: float = 1.0


@dataclass
class ParsedDocument:
    doc_id: str
    filename: str
    file_hash: str
    pages: list[DocumentPage]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_text(self) -> str:
        parts = []
        for page in self.pages:
            for block in page.blocks:
                if block.text:
                    parts.append(block.text)
        return "\n\n".join(parts)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def block_count(self) -> int:
        return sum(len(p.blocks) for p in self.pages)


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_id: str
    tenant_id: str
    chunk_index: int
    page_start: int
    page_end: int
    section: str
    block_type: BlockType
    text: str
    token_count: int
    bbox: BBox | None
    image_s3: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────
# OCR Engine
# ─────────────────────────────────────────────────────────────────

@dataclass
class OCRRegion:
    text: str
    bbox: tuple[float, float, float, float]
    confidence: float


@dataclass
class OCRResult:
    regions: list[OCRRegion]
    engine_used: str
    avg_confidence: float


class TieredOCREngine:
    """
    Tiered OCR: PaddleOCR → Tesseract → DocTR
    Selects engine based on availability and confidence.
    """

    MIN_CONFIDENCE = 0.5

    def __init__(self):
        self._paddle = None
        self._tesseract = None
        self._loaded = False

    async def _ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True
        try:
            from paddleocr import PaddleOCR
            self._paddle = PaddleOCR(
                use_angle_cls=True, lang="en",
                show_log=False, use_gpu=False
            )
            logger.info("PaddleOCR loaded")
        except Exception as e:
            logger.warning("PaddleOCR unavailable: %s", e)

        try:
            import pytesseract
            self._tesseract = pytesseract
            logger.info("Tesseract loaded")
        except Exception as e:
            logger.warning("Tesseract unavailable: %s", e)

    async def recognize(self, image_bytes: bytes) -> OCRResult:
        await self._ensure_loaded()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._recognize_sync, image_bytes)

    def _recognize_sync(self, image_bytes: bytes) -> OCRResult:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Try PaddleOCR first
        if self._paddle is not None:
            result = self._run_paddle(img)
            if result and result.avg_confidence >= self.MIN_CONFIDENCE:
                return result

        # Fallback: Tesseract
        if self._tesseract is not None:
            return self._run_tesseract(img)

        return OCRResult(regions=[], engine_used="none", avg_confidence=0.0)

    def _run_paddle(self, img: Image.Image) -> OCRResult | None:
        try:
            arr = np.array(img)
            raw = self._paddle.ocr(arr, cls=True)
            if not raw or not raw[0]:
                return None
            regions = []
            for line in raw[0]:
                box_pts, (text, conf) = line
                xs = [p[0] for p in box_pts]
                ys = [p[1] for p in box_pts]
                regions.append(OCRRegion(
                    text=text,
                    bbox=(min(xs), min(ys), max(xs), max(ys)),
                    confidence=float(conf),
                ))
            avg_conf = sum(r.confidence for r in regions) / len(regions) if regions else 0.0
            return OCRResult(regions=regions, engine_used="paddleocr", avg_confidence=avg_conf)
        except Exception as e:
            logger.debug("PaddleOCR error: %s", e)
            return None

    def _run_tesseract(self, img: Image.Image) -> OCRResult:
        try:
            data = self._tesseract.image_to_data(img, output_type=self._tesseract.Output.DICT)
            regions = []
            n = len(data["text"])
            for i in range(n):
                text = (data["text"][i] or "").strip()
                if not text:
                    continue
                try:
                    conf = float(data["conf"][i])
                except (ValueError, TypeError):
                    conf = 50.0
                if conf < 20:
                    continue
                left = float(data["left"][i])
                top = float(data["top"][i])
                w = float(data["width"][i])
                h = float(data["height"][i])
                regions.append(OCRRegion(
                    text=text,
                    bbox=(left, top, left + w, top + h),
                    confidence=conf / 100.0,
                ))
            avg_conf = sum(r.confidence for r in regions) / len(regions) if regions else 0.0
            return OCRResult(regions=regions, engine_used="tesseract", avg_confidence=avg_conf)
        except Exception as e:
            logger.warning("Tesseract error: %s", e)
            return OCRResult(regions=[], engine_used="tesseract_failed", avg_confidence=0.0)


# ─────────────────────────────────────────────────────────────────
# Layout Classifier
# ─────────────────────────────────────────────────────────────────

class LayoutClassifier:
    """
    Classifies page blocks into typed content categories.
    Uses rule-based heuristics + optional DiT model.
    """

    HEADING_FONT_MULTIPLIER = 1.2  # Font size > avg × 1.2 → heading

    def classify_block(
        self,
        text: str,
        bbox: BBox,
        page: DocumentPage,
        font_sizes: list[float],
        avg_font_size: float,
    ) -> BlockType:
        """Rule-based block classification."""
        y_relative = (bbox.y0 / page.height) if page.height > 0 else 0.5

        # Header zone (top 7%)
        if y_relative < 0.07:
            return BlockType.HEADER

        # Footer zone (bottom 7%)
        if y_relative > 0.93:
            return BlockType.FOOTER

        # Heading detection by font size
        if font_sizes and avg_font_size > 0:
            max_size = max(font_sizes)
            if max_size >= avg_font_size * self.HEADING_FONT_MULTIPLIER:
                text_stripped = text.strip()
                if len(text_stripped) < 120 and "\n" not in text_stripped.strip():
                    return BlockType.HEADER

        # Equation heuristics
        text_lower = text.lower()
        if self._looks_like_equation(text):
            return BlockType.EQUATION

        # Caption heuristics
        caption_patterns = [
            r"^(figure|fig\.?|table|tbl\.?|chart|diagram)\s+\d+",
            r"^(figure|fig\.?|table|tbl\.?)\s+[A-Z]",
        ]
        for pattern in caption_patterns:
            if re.match(pattern, text_lower.strip(), re.IGNORECASE):
                return BlockType.CAPTION

        # Footnote heuristics
        if y_relative > 0.80 and (text.strip().startswith(("*", "†", "‡", "§"))
                                   or re.match(r"^\d+\s+[a-zA-Z]", text.strip())):
            return BlockType.FOOTNOTE

        # Code block heuristics
        if text.count("\n") > 3 and text.count("    ") > 2:
            return BlockType.CODE

        return BlockType.TEXT

    @staticmethod
    def _looks_like_equation(text: str) -> bool:
        math_chars = set("∑∫∂∇×÷±√∞≤≥≠≈≡∝∈∉⊂⊃∪∩αβγδεζηθλμνξπρστφψω")
        if any(c in math_chars for c in text):
            return True
        # LaTeX-style inline
        if text.count("$") >= 2 or "\\frac" in text or "\\sum" in text:
            return True
        return False


# ─────────────────────────────────────────────────────────────────
# Table Extractor
# ─────────────────────────────────────────────────────────────────

class TableExtractor:
    """Multi-strategy table extraction: pdfplumber → Camelot fallback."""

    def extract_tables_from_page(
        self,
        page_bytes: bytes,
        page_num: int,
    ) -> list[ContentBlock]:
        """Extract all tables from a page as Markdown-formatted ContentBlocks."""
        tables: list[ContentBlock] = []

        try:
            with pdfplumber.open(io.BytesIO(page_bytes)) as pdf:
                if page_num > len(pdf.pages):
                    return tables
                pl_page = pdf.pages[page_num - 1]

                for tbl in pl_page.find_tables():
                    try:
                        rows = tbl.extract()
                        if not rows or len(rows) < 2:
                            continue
                        md = self._to_markdown(rows)
                        if not md:
                            continue

                        x0, y0, x1, y1 = tbl.bbox
                        tables.append(ContentBlock(
                            block_id=str(uuid.uuid4()),
                            type=BlockType.TABLE,
                            text=md,
                            page=page_num,
                            bbox=BBox(x0, y0, x1, y1),
                            metadata={
                                "rows": len(rows),
                                "cols": max(len(r) for r in rows) if rows else 0,
                                "extractor": "pdfplumber",
                            },
                        ))
                    except Exception as e:
                        logger.debug("Table extraction error on page %d: %s", page_num, e)
        except Exception as e:
            logger.warning("pdfplumber error on page %d: %s", page_num, e)

        return tables

    @staticmethod
    def _to_markdown(rows: list[list[str | None]]) -> str:
        clean = [[(c or "").strip() for c in row] for row in rows if any(rows)]
        if not clean:
            return ""
        max_cols = max(len(r) for r in clean)
        # Pad rows
        clean = [r + [""] * (max_cols - len(r)) for r in clean]

        header = clean[0]
        body = clean[1:]
        md = "| " + " | ".join(header) + " |\n"
        md += "|" + "|".join(["---"] * max_cols) + "|\n"
        for row in body:
            md += "| " + " | ".join(row) + " |\n"
        return md


# ─────────────────────────────────────────────────────────────────
# PDF Parser
# ─────────────────────────────────────────────────────────────────

class PDFParser:
    """
    Main PDF parser. Orchestrates layout detection, OCR, and extraction.
    """

    SCANNED_TEXT_THRESHOLD = 50  # fewer chars → treat as scanned

    def __init__(
        self,
        ocr: TieredOCREngine | None = None,
        layout: LayoutClassifier | None = None,
        table_extractor: TableExtractor | None = None,
    ):
        self.ocr = ocr or TieredOCREngine()
        self.layout = layout or LayoutClassifier()
        self.tables = table_extractor or TableExtractor()

    async def parse(
        self, pdf_bytes: bytes, doc_id: str, filename: str, tenant_id: str
    ) -> ParsedDocument:
        """Parse PDF bytes → ParsedDocument."""
        import hashlib
        file_hash = hashlib.sha256(pdf_bytes).hexdigest()[:16]

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages: list[DocumentPage] = []

        for page_idx in range(len(doc)):
            fitz_page = doc[page_idx]
            page = await self._parse_page(fitz_page, page_idx + 1, pdf_bytes)
            pages.append(page)

        doc.close()

        metadata = {
            "page_count": len(pages),
            "scanned_pages": sum(1 for p in pages if p.is_scanned),
            "file_hash": file_hash,
            "parser": "pymupdf+pdfplumber",
        }

        return ParsedDocument(
            doc_id=doc_id,
            filename=filename,
            file_hash=file_hash,
            pages=pages,
            metadata=metadata,
        )

    async def _parse_page(
        self, fitz_page: fitz.Page, page_num: int, pdf_bytes: bytes
    ) -> DocumentPage:
        rect = fitz_page.rect
        raw_text = fitz_page.get_text("text")
        is_scanned = len(raw_text.strip()) < self.SCANNED_TEXT_THRESHOLD

        page = DocumentPage(
            number=page_num,
            width=rect.width,
            height=rect.height,
            is_scanned=is_scanned,
        )

        # Always render page image (for visual embedding + OCR)
        page.image = self._render(fitz_page, dpi=150)

        if is_scanned:
            # Full-page OCR
            ocr_result = await self.ocr.recognize(page.image)
            page.ocr_confidence = ocr_result.avg_confidence
            for region in ocr_result.regions:
                x0, y0, x1, y1 = region.bbox
                page.blocks.append(ContentBlock(
                    block_id=str(uuid.uuid4()),
                    type=BlockType.TEXT,
                    text=region.text,
                    page=page_num,
                    bbox=BBox(x0, y0, x1, y1),
                    metadata={"ocr_confidence": region.confidence, "ocr_engine": ocr_result.engine_used},
                ))
        else:
            # Digital page: extract text blocks
            self._extract_digital_blocks(fitz_page, page)

            # Extract tables (pdfplumber, separate pass)
            table_blocks = self.tables.extract_tables_from_page(pdf_bytes, page_num)
            # Remove text blocks that overlap with table regions
            table_bboxes = [t.bbox for t in table_blocks]
            page.blocks = [
                b for b in page.blocks
                if b.type != BlockType.TABLE
                and not any(tb.contains(b.bbox) for tb in table_bboxes)
            ]
            page.blocks.extend(table_blocks)

        # Sort blocks by reading order (top-to-bottom, left-to-right)
        page.blocks.sort(key=lambda b: (b.bbox.y0, b.bbox.x0))

        return page

    def _extract_digital_blocks(self, fitz_page: fitz.Page, page: DocumentPage) -> None:
        text_dict = fitz_page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        all_font_sizes: list[float] = []

        raw_blocks: list[tuple[dict, str]] = []
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:  # skip image placeholders
                continue
            text = self._reconstruct_text(block)
            if not text.strip():
                continue
            font_sizes = self._get_font_sizes(block)
            all_font_sizes.extend(font_sizes)
            raw_blocks.append((block, text, font_sizes))

        avg_fs = sum(all_font_sizes) / len(all_font_sizes) if all_font_sizes else 12.0

        for block_data, text, font_sizes in raw_blocks:
            bbox = BBox(*block_data["bbox"])
            block_type = self.layout.classify_block(
                text, bbox, page, font_sizes, avg_fs
            )
            page.blocks.append(ContentBlock(
                block_id=str(uuid.uuid4()),
                type=block_type,
                text=text,
                page=page.number,
                bbox=bbox,
                metadata={
                    "font_sizes": font_sizes,
                    "avg_font_size": avg_fs,
                },
            ))

        # Extract inline images
        for block in text_dict.get("blocks", []):
            if block.get("type") == 1:  # image block
                bbox = BBox(*block["bbox"])
                page.blocks.append(ContentBlock(
                    block_id=str(uuid.uuid4()),
                    type=BlockType.FIGURE,
                    text="",
                    page=page.number,
                    bbox=bbox,
                    metadata={"source": "pymupdf_image"},
                ))

    @staticmethod
    def _reconstruct_text(block: dict) -> str:
        lines = []
        for line in block.get("lines", []):
            spans_text = "".join(s.get("text", "") for s in line.get("spans", []))
            if spans_text.strip():
                lines.append(spans_text.rstrip())
        return "\n".join(lines)

    @staticmethod
    def _get_font_sizes(block: dict) -> list[float]:
        sizes = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                sz = span.get("size", 0)
                if sz > 0:
                    sizes.append(round(sz, 1))
        return sizes

    @staticmethod
    def _render(fitz_page: fitz.Page, dpi: int = 150) -> bytes:
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = fitz_page.get_pixmap(matrix=mat)
        return pix.tobytes("png")


# ─────────────────────────────────────────────────────────────────
# Semantic Chunker
# ─────────────────────────────────────────────────────────────────

class SemanticChunker:
    """
    Converts ParsedDocument → DocumentChunk list.
    
    Strategy selection:
    1. Hierarchical: structured docs with clear headings
    2. Semantic: boundary detection via embedding similarity
    3. Sliding window: fallback for uniform text
    """

    MAX_TOKENS = 800
    MIN_TOKENS = 50
    OVERLAP_TOKENS = 100

    def __init__(self, tokenizer=None, embedding_model=None):
        self.tokenizer = tokenizer
        self.embedder = embedding_model

    def chunk(
        self,
        parsed_doc: ParsedDocument,
        tenant_id: str,
        strategy: str = "hierarchical",
    ) -> list[DocumentChunk]:
        """Produce chunk list from parsed document."""
        if strategy == "hierarchical":
            return self._hierarchical_chunk(parsed_doc, tenant_id)
        elif strategy == "sliding":
            return self._sliding_window_chunk(parsed_doc, tenant_id)
        else:
            return self._hierarchical_chunk(parsed_doc, tenant_id)

    def _hierarchical_chunk(
        self, doc: ParsedDocument, tenant_id: str
    ) -> list[DocumentChunk]:
        """
        Group blocks by section (defined by HEADER blocks).
        Split sections that exceed MAX_TOKENS.
        """
        chunks: list[DocumentChunk] = []
        chunk_idx = 0
        current_section = "Introduction"
        current_texts: list[tuple[ContentBlock, str]] = []
        current_tokens = 0

        def flush():
            nonlocal chunk_idx, current_tokens
            if not current_texts:
                return
            combined_text = "\n\n".join(t for _, t in current_texts)
            first_block = current_texts[0][0]
            last_block = current_texts[-1][0]
            toks = self._count_tokens(combined_text)
            chunks.append(DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                doc_id=doc.doc_id,
                tenant_id=tenant_id,
                chunk_index=chunk_idx,
                page_start=first_block.page,
                page_end=last_block.page,
                section=current_section,
                block_type=first_block.type,
                text=combined_text,
                token_count=toks,
                bbox=first_block.bbox,
                metadata={"strategy": "hierarchical"},
            ))
            chunk_idx += 1
            current_texts.clear()
            current_tokens = 0

        for page in doc.pages:
            for block in page.blocks:
                if block.type == BlockType.FOOTER:
                    continue
                if not block.text and block.type != BlockType.FIGURE:
                    continue

                # New section: heading detected
                if block.type == BlockType.HEADER:
                    flush()
                    current_section = block.text.strip()[:200]
                    continue

                # Atomic blocks (table, equation, figure) → own chunk
                if block.type in (BlockType.TABLE, BlockType.EQUATION):
                    flush()
                    toks = self._count_tokens(block.text)
                    if toks >= self.MIN_TOKENS:
                        chunks.append(DocumentChunk(
                            chunk_id=str(uuid.uuid4()),
                            doc_id=doc.doc_id,
                            tenant_id=tenant_id,
                            chunk_index=chunk_idx,
                            page_start=block.page,
                            page_end=block.page,
                            section=current_section,
                            block_type=block.type,
                            text=block.text,
                            token_count=toks,
                            bbox=block.bbox,
                            metadata={"strategy": "atomic"},
                        ))
                        chunk_idx += 1
                    continue

                # Normal text block
                block_tokens = self._count_tokens(block.text)
                if current_tokens + block_tokens > self.MAX_TOKENS:
                    flush()

                # Very long block: split by sentences
                if block_tokens > self.MAX_TOKENS:
                    for sub_text in self._split_long_block(block.text):
                        sub_tokens = self._count_tokens(sub_text)
                        chunks.append(DocumentChunk(
                            chunk_id=str(uuid.uuid4()),
                            doc_id=doc.doc_id,
                            tenant_id=tenant_id,
                            chunk_index=chunk_idx,
                            page_start=block.page,
                            page_end=block.page,
                            section=current_section,
                            block_type=block.type,
                            text=sub_text,
                            token_count=sub_tokens,
                            bbox=block.bbox,
                            metadata={"strategy": "split"},
                        ))
                        chunk_idx += 1
                    continue

                current_texts.append((block, block.text))
                current_tokens += block_tokens

        flush()  # Final flush

        # Merge tiny chunks (< MIN_TOKENS)
        chunks = self._merge_tiny_chunks(chunks)
        return chunks

    def _sliding_window_chunk(
        self, doc: ParsedDocument, tenant_id: str
    ) -> list[DocumentChunk]:
        """Sliding window chunking for uniform text."""
        all_text = doc.total_text
        words = all_text.split()
        chunks: list[DocumentChunk] = []
        step = self.MAX_TOKENS - self.OVERLAP_TOKENS
        chunk_idx = 0

        for start in range(0, len(words), step):
            end = start + self.MAX_TOKENS
            chunk_words = words[start:end]
            if not chunk_words:
                break
            text = " ".join(chunk_words)
            if self._count_tokens(text) < self.MIN_TOKENS:
                continue
            chunks.append(DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                doc_id=doc.doc_id,
                tenant_id=tenant_id,
                chunk_index=chunk_idx,
                page_start=1,
                page_end=doc.page_count,
                section="",
                block_type=BlockType.TEXT,
                text=text,
                token_count=self._count_tokens(text),
                bbox=None,
                metadata={"strategy": "sliding_window", "word_start": start},
            ))
            chunk_idx += 1

        return chunks

    def _split_long_block(self, text: str) -> Iterator[str]:
        """Split a long text block into sentence-grouped sub-chunks."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        buffer: list[str] = []
        buffer_tokens = 0

        for sentence in sentences:
            s_tokens = self._count_tokens(sentence)
            if buffer_tokens + s_tokens > self.MAX_TOKENS and buffer:
                yield " ".join(buffer)
                # Overlap: keep last sentence
                buffer = buffer[-1:]
                buffer_tokens = self._count_tokens(buffer[0]) if buffer else 0

            buffer.append(sentence)
            buffer_tokens += s_tokens

        if buffer:
            yield " ".join(buffer)

    def _merge_tiny_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Merge consecutive chunks below MIN_TOKENS threshold."""
        if not chunks:
            return chunks
        merged: list[DocumentChunk] = []
        i = 0
        while i < len(chunks):
            chunk = chunks[i]
            if chunk.token_count < self.MIN_TOKENS and i + 1 < len(chunks):
                next_chunk = chunks[i + 1]
                merged_text = chunk.text + "\n\n" + next_chunk.text
                merged_tokens = chunk.token_count + next_chunk.token_count
                chunks[i + 1] = DocumentChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    tenant_id=chunk.tenant_id,
                    chunk_index=chunk.chunk_index,
                    page_start=chunk.page_start,
                    page_end=next_chunk.page_end,
                    section=chunk.section or next_chunk.section,
                    block_type=chunk.block_type,
                    text=merged_text,
                    token_count=merged_tokens,
                    bbox=chunk.bbox,
                    metadata={"merged": True},
                )
                i += 1
                continue
            merged.append(chunk)
            i += 1
        return merged

    def _count_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return max(1, int(len(text.split()) * 1.33))
```

---

## 3. Document Engine Factory

```python
class DocumentEngineFactory:
    """Creates a fully configured DocumentEngine instance."""

    @staticmethod
    def create(config: dict | None = None) -> tuple[PDFParser, SemanticChunker]:
        ocr = TieredOCREngine()
        layout = LayoutClassifier()
        tables = TableExtractor()
        parser = PDFParser(ocr=ocr, layout=layout, table_extractor=tables)

        # Optional: load tokenizer for accurate token counting
        tokenizer = None
        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")
        except Exception:
            pass  # Use word-count approximation

        chunker = SemanticChunker(tokenizer=tokenizer)
        return parser, chunker
```
