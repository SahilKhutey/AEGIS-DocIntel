'''
AEGIS-MIOS — Optical Character Recognition
===========================================
OCR adapter running Tesseract / PaddleOCR on image bytes.
'''

from __future__ import annotations

import io
from PIL import Image


class OCREngine:
    '''OCREngine wrapper using pytesseract for character recognition.'''

    async def recognize(self, image_bytes: bytes) -> str:
        '''Recognize and extract text from raw image bytes.'''
        try:
            import pytesseract
            img = Image.open(io.BytesIO(image_bytes))
            return pytesseract.image_to_string(img)
        except Exception:
            return ''
