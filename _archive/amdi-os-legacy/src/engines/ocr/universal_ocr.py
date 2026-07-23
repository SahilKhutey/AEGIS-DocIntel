"""
universal_ocr.py
================
AEGIS-AMDI-OS  |  Engine Layer  |  Optical Character Recognition

Provides :class:`UniversalOCR`, which inspects every page of a
:class:`~src.core.normalized_document.NormalizedDocument`, identifies
pages that appear to be scanned images (few text blocks / low character
count), and augments them with OCR-derived text blocks.

Engine selection
----------------
* **Default**: pytesseract (wraps Tesseract-OCR).
* **Optional**: PaddleOCR — activated by setting the environment variable
  ``AMDI_OCR_ENGINE=paddleocr``.

If neither engine is available the document is returned unchanged and a
warning is emitted.

Dependencies (optional)
-----------------------
* ``pytesseract`` + Tesseract binary
* ``paddlepaddle`` + ``paddleocr``
* ``Pillow`` (PIL) — required for image handling in both engines
"""

from __future__ import annotations

import io
import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional

# ---------------------------------------------------------------------------
# Optional engine imports
# ---------------------------------------------------------------------------
try:
    import pytesseract
    from PIL import Image as PILImage
    _TESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None  # type: ignore[assignment]
    PILImage = None  # type: ignore[assignment]
    _TESSERACT_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    _PADDLE_AVAILABLE = True
except ImportError:
    PaddleOCR = None  # type: ignore[assignment]
    _PADDLE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Internal imports
# ---------------------------------------------------------------------------
from src.core.normalized_document import (
    BlockType,
    NormalizedBlock,
    NormalizedDocument,
    NormalizedPage,
)

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_SCANNED_BLOCK_THRESHOLD: int = 3
"""Pages with fewer than this many blocks are considered potentially scanned."""

_SCANNED_CHAR_THRESHOLD: int = 50
"""Pages with fewer total characters than this are considered potentially scanned."""

_ENV_ENGINE_KEY: str = "AMDI_OCR_ENGINE"
"""Environment variable name to override the OCR engine selection."""


# ===========================================================================
# UniversalOCR
# ===========================================================================
class UniversalOCR:
    """
    OCR augmentation engine for :class:`~src.core.normalized_document.NormalizedDocument`.

    Parameters
    ----------
    lang : str
        Tesseract language code(s) passed to pytesseract / PaddleOCR
        (default ``"eng"``).  Multiple languages can be joined with ``+``
        for pytesseract, e.g. ``"eng+fra"``.
    dpi : int
        Resolution hint used when rasterising pages for OCR (default 300).
    tesseract_config : str
        Additional command-line flags forwarded to the Tesseract binary,
        e.g. ``"--psm 6"`` (default ``""``).

    Notes
    -----
    PaddleOCR is initialised lazily on first use to avoid the expensive
    model-loading cost when OCR is not needed.
    """

    def __init__(
        self,
        lang: str = "eng",
        dpi: int = 300,
        tesseract_config: str = "",
    ) -> None:
        self.lang = lang
        self.dpi = dpi
        self.tesseract_config = tesseract_config
        self._paddle_instance: Optional[object] = None

        engine_env = os.environ.get(_ENV_ENGINE_KEY, "").strip().lower()
        self._engine: str = "paddleocr" if engine_env == "paddleocr" else "tesseract"

        log.debug(
            "UniversalOCR initialised (engine=%s, lang=%s, dpi=%d)",
            self._engine,
            lang,
            dpi,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def augment(self, doc: NormalizedDocument) -> NormalizedDocument:
        """
        Detect scanned pages and augment them with OCR text blocks.

        For each page in *doc*, :meth:`_is_scanned_page` is evaluated.
        If the page is scanned and raw image bytes are available, OCR is
        performed and the resulting blocks are appended to the page's
        block list.  Existing blocks are preserved.

        Parameters
        ----------
        doc : NormalizedDocument
            Input document, possibly containing scanned pages.

        Returns
        -------
        NormalizedDocument
            The same document object with OCR blocks injected where needed.
            Original blocks are never removed.

        Notes
        -----
        If no OCR engine is available, the document is returned unchanged
        after emitting a ``WARNING`` log entry.
        """
        if not self._any_engine_available():
            log.warning(
                "No OCR engine available. "
                "Install pytesseract (pip install pytesseract) or "
                "PaddleOCR (pip install paddlepaddle paddleocr) to enable OCR. "
                "Returning document unchanged."
            )
            return doc

        augmented_pages: List[NormalizedPage] = []
        for page in doc.pages:
            if self._is_scanned_page(page):
                log.info(
                    "Page %d detected as scanned – running OCR (engine=%s).",
                    page.page_index,
                    self._engine,
                )
                page_image_bytes = self._extract_page_image(doc, page)
                if page_image_bytes:
                    ocr_blocks = self._ocr_page(page_image_bytes)
                    if ocr_blocks:
                        log.debug(
                            "OCR produced %d blocks for page %d.",
                            len(ocr_blocks),
                            page.page_index,
                        )
                        # Replace the sparse/empty block list with OCR results
                        augmented_pages.append(
                            NormalizedPage(
                                page_index=page.page_index,
                                width=page.width,
                                height=page.height,
                                blocks=page.blocks + ocr_blocks,
                                metadata={
                                    **(page.metadata or {}),
                                    "ocr_augmented": True,
                                    "ocr_engine": self._engine,
                                },
                            )
                        )
                        continue
                    log.warning(
                        "OCR returned no blocks for page %d.", page.page_index
                    )
                else:
                    log.warning(
                        "No image bytes available for page %d; skipping OCR.",
                        page.page_index,
                    )
            augmented_pages.append(page)

        return NormalizedDocument(
            source_id=doc.source_id,
            source_path=doc.source_path,
            format=doc.format,
            pages=augmented_pages,
            metadata=doc.metadata,
        )

    # ------------------------------------------------------------------
    # Scanned-page detection
    # ------------------------------------------------------------------

    def _is_scanned_page(self, page: NormalizedPage) -> bool:
        """
        Heuristically decide whether a page is a scanned image.

        A page is considered scanned when **both** of the following are true:

        1. It contains fewer than :data:`_SCANNED_BLOCK_THRESHOLD` blocks.
        2. The total character count across all blocks is less than
           :data:`_SCANNED_CHAR_THRESHOLD`.

        Parameters
        ----------
        page : NormalizedPage

        Returns
        -------
        bool
            ``True`` if the page appears to be a scanned image.

        Examples
        --------
        >>> ocr = UniversalOCR()
        >>> from src.core.normalized_document import NormalizedPage
        >>> empty_page = NormalizedPage(page_index=0, blocks=[], width=0, height=0)
        >>> ocr._is_scanned_page(empty_page)
        True
        """
        block_count = len(page.blocks)
        total_chars = sum(len(b.text or "") for b in page.blocks)

        is_scanned = (
            block_count < _SCANNED_BLOCK_THRESHOLD
            and total_chars < _SCANNED_CHAR_THRESHOLD
        )

        log.debug(
            "Page %d: blocks=%d, chars=%d → scanned=%s",
            page.page_index,
            block_count,
            total_chars,
            is_scanned,
        )
        return is_scanned

    # ------------------------------------------------------------------
    # OCR execution
    # ------------------------------------------------------------------

    def _ocr_page(self, page_image_bytes: bytes) -> List[NormalizedBlock]:
        """
        Run OCR on raw image bytes and return a list of text blocks.

        Engine dispatch
        ---------------
        * ``self._engine == "paddleocr"`` and PaddleOCR available →
          :meth:`_ocr_with_paddle`
        * Otherwise → :meth:`_ocr_with_tesseract`

        Parameters
        ----------
        page_image_bytes : bytes
            Raw image data (PNG / JPEG / TIFF / BMP).

        Returns
        -------
        list[NormalizedBlock]
            Ordered list of OCR text blocks; empty list on failure.
        """
        if self._engine == "paddleocr" and _PADDLE_AVAILABLE:
            return self._ocr_with_paddle(page_image_bytes)
        return self._ocr_with_tesseract(page_image_bytes)

    def _ocr_with_tesseract(self, page_image_bytes: bytes) -> List[NormalizedBlock]:
        """
        OCR using pytesseract / Tesseract.

        Returns word-level bounding boxes aggregated into line-level blocks
        via Tesseract's ``image_to_data`` output.

        Parameters
        ----------
        page_image_bytes : bytes

        Returns
        -------
        list[NormalizedBlock]
        """
        if not _TESSERACT_AVAILABLE:
            log.error(
                "pytesseract is not installed. "
                "Install it with: pip install pytesseract"
            )
            return []

        try:
            img = PILImage.open(io.BytesIO(page_image_bytes)).convert("RGB")
        except Exception as exc:
            log.error("Failed to open image for Tesseract OCR: %s", exc)
            return []

        try:
            data = pytesseract.image_to_data(
                img,
                lang=self.lang,
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT,
            )
        except Exception as exc:
            log.error("pytesseract.image_to_data failed: %s", exc)
            return []

        blocks: List[NormalizedBlock] = []
        # Group words into lines using (block_num, par_num, line_num)
        line_groups: dict[tuple, dict] = {}
        n = len(data["text"])

        for i in range(n):
            word = (data["text"][i] or "").strip()
            conf = int(data["conf"][i] if data["conf"][i] != "-1" else 0)
            if not word or conf < 30:
                continue

            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            if key not in line_groups:
                line_groups[key] = {
                    "words": [],
                    "x0": data["left"][i],
                    "y0": data["top"][i],
                    "x1": data["left"][i] + data["width"][i],
                    "y1": data["top"][i] + data["height"][i],
                    "conf_sum": 0,
                    "conf_count": 0,
                }
            g = line_groups[key]
            g["words"].append(word)
            g["x0"] = min(g["x0"], data["left"][i])
            g["y0"] = min(g["y0"], data["top"][i])
            g["x1"] = max(g["x1"], data["left"][i] + data["width"][i])
            g["y1"] = max(g["y1"], data["top"][i] + data["height"][i])
            g["conf_sum"] += conf
            g["conf_count"] += 1

        for key in sorted(line_groups.keys()):
            g = line_groups[key]
            text = " ".join(g["words"])
            avg_conf = g["conf_sum"] / g["conf_count"] if g["conf_count"] else 0.0
            blocks.append(
                NormalizedBlock(
                    block_type=BlockType.TEXT,
                    text=text,
                    bbox=(float(g["x0"]), float(g["y0"]),
                          float(g["x1"]), float(g["y1"])),
                    page_index=-1,  # caller sets correct page_index
                    metadata={"ocr_engine": "tesseract", "confidence": avg_conf},
                )
            )

        log.debug("Tesseract produced %d line blocks.", len(blocks))
        return blocks

    def _ocr_with_paddle(self, page_image_bytes: bytes) -> List[NormalizedBlock]:
        """
        OCR using PaddleOCR.

        PaddleOCR returns ``[line, ...]`` where each line is
        ``[[x0,y0], [x1,y0], [x1,y1], [x0,y1]], [text, confidence]``.

        Parameters
        ----------
        page_image_bytes : bytes

        Returns
        -------
        list[NormalizedBlock]
        """
        if not _PADDLE_AVAILABLE:
            log.error(
                "PaddleOCR is not installed. "
                "Install it with: pip install paddlepaddle paddleocr"
            )
            return []

        # Lazy init
        if self._paddle_instance is None:
            try:
                self._paddle_instance = PaddleOCR(use_angle_cls=True, lang=self.lang)
                log.debug("PaddleOCR instance created (lang=%s).", self.lang)
            except Exception as exc:
                log.error("Failed to initialise PaddleOCR: %s", exc)
                return []

        try:
            img_arr = self._bytes_to_numpy(page_image_bytes)
            if img_arr is None:
                return []
            results = self._paddle_instance.ocr(img_arr, cls=True)
        except Exception as exc:
            log.error("PaddleOCR.ocr() failed: %s", exc)
            return []

        blocks: List[NormalizedBlock] = []
        for line_result in (results or []):
            for line in (line_result or []):
                try:
                    quad, (text, conf) = line
                    xs = [pt[0] for pt in quad]
                    ys = [pt[1] for pt in quad]
                    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
                    blocks.append(
                        NormalizedBlock(
                            block_type=BlockType.TEXT,
                            text=str(text).strip(),
                            bbox=(float(x0), float(y0), float(x1), float(y1)),
                            page_index=-1,
                            metadata={"ocr_engine": "paddleocr", "confidence": float(conf)},
                        )
                    )
                except (ValueError, TypeError, IndexError) as exc:
                    log.debug("Skipping malformed PaddleOCR line result: %s", exc)

        log.debug("PaddleOCR produced %d line blocks.", len(blocks))
        return blocks

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _any_engine_available(self) -> bool:
        """Return ``True`` if at least one OCR engine can be used."""
        if self._engine == "paddleocr" and _PADDLE_AVAILABLE:
            return True
        return _TESSERACT_AVAILABLE

    @staticmethod
    def _extract_page_image(
        doc: NormalizedDocument, page: NormalizedPage
    ) -> Optional[bytes]:
        """
        Extract raw image bytes for a given page.

        Strategy
        --------
        1. Look for ``page.metadata["image_bytes"]`` (pre-cached by parser).
        2. Look for ``doc.page_images[page.page_index]``.
        3. If the source is a PDF, rasterise the page via PyMuPDF.
        4. If the source is an image file, return ``doc.raw_content``.

        Parameters
        ----------
        doc : NormalizedDocument
        page : NormalizedPage

        Returns
        -------
        bytes | None
        """
        # 1. Pre-cached in page metadata
        meta = page.metadata or {}
        if "image_bytes" in meta:
            return meta["image_bytes"]

        # 2. Pre-cached at document level
        page_images = getattr(doc, "page_images", None) or {}
        if page.page_index in page_images:
            return page_images[page.page_index]

        # 3. Rasterise PDF page via PyMuPDF
        try:
            import fitz  # type: ignore[import-not-found]
            src_path = doc.source_path or ""
            if src_path.lower().endswith(".pdf"):
                pdf = fitz.open(src_path)
                pg = pdf[page.page_index]
                mat = fitz.Matrix(2.0, 2.0)  # 2× zoom ≈ 144 DPI
                pix = pg.get_pixmap(matrix=mat)
                png_bytes = pix.tobytes("png")
                pdf.close()
                return png_bytes
        except Exception as exc:
            log.debug("PyMuPDF page rasterisation failed: %s", exc)

        # 4. Single-image document
        raw = getattr(doc, "raw_content", None)
        if raw and doc.format in ("image", "png", "jpg", "jpeg", "tiff", "bmp"):
            return raw

        return None

    @staticmethod
    def _bytes_to_numpy(image_bytes: bytes):
        """
        Convert raw image bytes to a NumPy array suitable for PaddleOCR.

        Returns ``None`` on failure.
        """
        try:
            import numpy as np
            from PIL import Image as PILImage  # type: ignore[import-untyped]
            img = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
            return np.array(img)
        except Exception as exc:
            log.error("Failed to convert image bytes to numpy array: %s", exc)
            return None
