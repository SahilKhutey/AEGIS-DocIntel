"""
AEGIS-DocIntel — Normalization Layer Test Suite
===============================================
Comprehensive unit tests for:
  - TextCleaner (src/normalization/cleaner.py)
  - LayoutDetector (src/normalization/layout.py)
  - OCREngine (src/normalization/ocr.py)
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from src.core.normalized_document import (
    BlockType,
    BoundingBox,
    NormalizedBlock,
    NormalizedPage,
)
from src.normalization.cleaner import TextCleaner
from src.normalization.layout import LayoutDetector
from src.normalization.ocr import OCREngine


# ============================================================================
# TextCleaner Tests
# ============================================================================

def test_text_cleaner_whitespace_and_tabs():
    """Verify TextCleaner collapses tabs and consecutive spaces into single spaces."""
    cleaner = TextCleaner()
    dirty = "Hello\t\tworld    from   AEGIS   DocIntel."
    cleaned = cleaner.clean(dirty)
    assert cleaned == "Hello world from AEGIS DocIntel."


def test_text_cleaner_newlines():
    """Verify TextCleaner collapses multiple newlines into single newlines."""
    cleaner = TextCleaner()
    dirty = "Line 1\n\n\n\nLine 2\n\nLine 3"
    cleaned = cleaner.clean(dirty)
    assert cleaned == "Line 1\nLine 2\nLine 3"


def test_text_cleaner_empty_and_whitespace_only():
    """Verify TextCleaner handles empty and whitespace-only strings gracefully."""
    cleaner = TextCleaner()
    assert cleaner.clean("") == ""
    assert cleaner.clean("   \t  \n  ") == ""


# ============================================================================
# LayoutDetector Tests
# ============================================================================

def test_layout_detector_reading_order_and_columns():
    """Verify LayoutDetector sorts blocks into reading order and records column count."""
    detector = LayoutDetector()

    # Create two columns on a 612 x 792 page:
    # Left column: x in [50, 250], Right column: x in [350, 550]
    b1_right = NormalizedBlock(
        text="Right Col Line 1",
        bbox=BoundingBox(350, 100, 550, 120),
        page=1,
    )
    b2_left = NormalizedBlock(
        text="Left Col Line 1",
        bbox=BoundingBox(50, 100, 250, 120),
        page=1,
    )
    b3_left = NormalizedBlock(
        text="Left Col Line 2",
        bbox=BoundingBox(50, 130, 250, 150),
        page=1,
    )

    page = NormalizedPage(
        page_number=1,
        width=612.0,
        height=792.0,
        blocks=[b1_right, b2_left, b3_left],
    )

    analyzed = detector.analyze(page)

    assert analyzed.page_number == 1
    assert analyzed.metadata is not None
    assert "column_count" in analyzed.metadata
    assert len(analyzed.blocks) == 3
    # Left column block should be sorted before right column block at the same vertical offset
    assert analyzed.blocks[0].text == "Left Col Line 1"
    assert analyzed.blocks[1].text == "Right Col Line 1"


def test_layout_detector_empty_page():
    """Verify LayoutDetector handles empty pages without errors."""
    detector = LayoutDetector()
    page = NormalizedPage(page_number=1, width=612.0, height=792.0, blocks=[])
    analyzed = detector.analyze(page)
    assert len(analyzed.blocks) == 0
    assert "column_count" in analyzed.metadata


# ============================================================================
# OCREngine Tests
# ============================================================================

@pytest.mark.asyncio
async def test_ocr_engine_invalid_bytes():
    """Verify OCREngine returns empty string when passed invalid/corrupt image bytes."""
    ocr = OCREngine()
    result = await ocr.recognize(b"not an image byte array")
    assert result == ""


@pytest.mark.asyncio
async def test_ocr_engine_mock_extraction():
    """Verify OCREngine extracts text when pytesseract produces output."""
    ocr = OCREngine()
    fixture_bytes = open("tests/fixtures/sample.png", "rb").read()

    with patch("pytesseract.image_to_string", return_value="TEST 123"):
        result = await ocr.recognize(fixture_bytes)
        assert "TEST 123" in result


@pytest.mark.asyncio
async def test_ocr_engine_real_or_fallback():
    """Verify OCREngine executes without crashing on a valid fixture image."""
    ocr = OCREngine()
    fixture_bytes = open("tests/fixtures/sample.png", "rb").read()
    result = await ocr.recognize(fixture_bytes)
    assert isinstance(result, str)
