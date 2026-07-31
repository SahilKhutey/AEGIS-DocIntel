"""
AEGIS-AMDI-OS — OCR Engine
=============================
Tiered OCR: PaddleOCR → Tesseract → empty fallback.
"""
from __future__ import annotations

import asyncio
import io
import logging
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


class OCREngine:
    """
    Multi-tier OCR engine.
    
    Tries in order:
    1. PaddleOCR (high accuracy, multilingual)
    2. Tesseract (fast fallback)
    3. Empty string (graceful failure)
    """

    SUPPORTED_LANGUAGES = ["en", "ch", "fr", "de", "es", "pt", "ru", "ja", "ko"]

    def __init__(self, primary: str = "paddleocr", lang: str = "en", device: str = "cpu"):
        self.primary = primary
        self.lang = lang
        self.device = device
        self._paddle = None
        self._tesseract = None

    async def recognize(self, image_bytes: bytes) -> str:
        """Recognize text from image bytes. Returns extracted text."""
        if not image_bytes:
            return ""
        try:
            return await asyncio.get_running_loop().run_in_executor(
                None, self._recognize_sync, image_bytes,
            )
        except Exception as e:
            logger.error(f"OCR failed completely: {e}")
            return ""

    def _recognize_sync(self, image_bytes: bytes) -> str:
        """Synchronous OCR processing."""
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            logger.warning(f"Cannot open image for OCR: {e}")
            return ""

        # Try PaddleOCR first (better accuracy)
        if self.primary == "paddleocr" and self._ensure_paddle():
            text = self._recognize_paddle(img)
            if text:
                return text

        # Fallback to Tesseract
        if self._ensure_tesseract():
            text = self._recognize_tesseract(img)
            if text:
                return text

        return ""

    def _ensure_paddle(self) -> bool:
        """Lazy-load PaddleOCR."""
        if self._paddle is not None:
            return True
        try:
            from paddleocr import PaddleOCR
            self._paddle = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang if self.lang in ("ch", "en", "fr", "german", "korean", "japan") else "en",
                show_log=False,
                use_gpu=(self.device == "cuda"),
            )
            logger.info("PaddleOCR loaded successfully")
            return True
        except Exception as e:
            logger.warning(f"PaddleOCR unavailable: {e}")
            return False

    def _ensure_tesseract(self) -> bool:
        """Lazy-load Tesseract."""
        if self._tesseract is not None:
            return True
        try:
            import pytesseract
            self._tesseract = pytesseract
            logger.info("Tesseract loaded successfully")
            return True
        except Exception as e:
            logger.warning(f"Tesseract unavailable: {e}")
            return False

    def _recognize_paddle(self, img: Image.Image) -> str:
        """Recognize using PaddleOCR."""
        try:
            import numpy as np
            result = self._paddle.ocr(np.array(img), cls=True)
            if not result or not result[0]:
                return ""
            lines = []
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0] if line[1] else ""
                    if text and text.strip():
                        lines.append(text)
            return "\n".join(lines)
        except Exception as e:
            logger.warning(f"PaddleOCR processing failed: {e}")
            return ""

    def _recognize_tesseract(self, img: Image.Image) -> str:
        """Recognize using Tesseract."""
        try:
            lang_map = {"en": "eng", "ch": "chi_sim", "fr": "fra",
                        "de": "deu", "es": "spa", "pt": "por", "ru": "rus"}
            tesseract_lang = lang_map.get(self.lang, "eng")
            return self._tesseract.image_to_string(img, lang=tesseract_lang)
        except Exception as e:
            logger.warning(f"Tesseract processing failed: {e}")
            return ""

    def get_confidence(self, image_bytes: bytes) -> float:
        """Estimate OCR confidence (0-1)."""
        text = self._recognize_sync(image_bytes)
        if not text:
            return 0.0
        # Simple heuristic: more text = higher confidence
        words = text.split()
        if len(words) < 5:
            return 0.3
        elif len(words) < 20:
            return 0.6
        return 0.85
