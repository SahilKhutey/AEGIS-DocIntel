"""
tests/processing/extraction/test_ocr_extraction.py
==================================================
Tests OCR-001 through OCR-007 verifying native PDF extraction, OCR pipelines,
CER/WER error metrics, confidence calibration, and schema conformance.
"""

import json
from pathlib import Path
import pytest
import jsonschema

from aegis.processing.benchmarking.metrics import TextExtractionMetrics, levenshtein_distance
from aegis.processing.extraction import (
    ConfidenceEvaluator,
    NativePDFExtractor,
    OCRExtractor,
    TextNormalizer,
)
from aegis.processing.models import ExtractionMethod, PageTextExtraction

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXTRACTION_SCHEMA_FILE = REPO_ROOT / "schemas" / "processing" / "extraction.schema.json"


@pytest.fixture
def extraction_schema():
    with open(EXTRACTION_SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_ocr_001_native_pdf_extraction(extraction_schema):
    """OCR-001: Extract text from real digital PDF and verify structured blocks."""
    fixtures_dir = REPO_ROOT / "tests" / "fixtures"
    sample_pdf = fixtures_dir / "sample.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample.pdf missing from fixtures")

    extractor = NativePDFExtractor()
    results = extractor.extract_document(sample_pdf, document_id="DOC_SAMPLE_001")

    assert len(results) >= 1
    page1 = results[0]
    assert page1.page_number == 1
    assert page1.extraction_method == ExtractionMethod.NATIVE_PDF
    assert page1.engine == "PyMuPDF"
    assert len(page1.text) > 0
    assert page1.confidence is None  # explicitly null as per specification

    # Schema validation
    jsonschema.validate(page1.to_schema_dict(), extraction_schema)


def test_ocr_002_cer_wer_metrics():
    """OCR-002: Verify CER and WER metric calculations against known reference/hypothesis pairs."""
    # Case 1: Identical strings
    ref = "Invoice Total: $1,250.00"
    hyp = "Invoice Total: $1,250.00"
    cer_res = TextExtractionMetrics.calculate_cer(ref, hyp)
    wer_res = TextExtractionMetrics.calculate_wer(ref, hyp)
    assert cer_res["cer"] == 0.0
    assert wer_res["wer"] == 0.0
    assert wer_res["word_accuracy"] == 1.0

    # Case 2: One substitution ('0' instead of 'O')
    ref = "WORD"
    hyp = "W0RD"
    cer_res = TextExtractionMetrics.calculate_cer(ref, hyp)
    assert cer_res["cer"] == 0.25
    assert cer_res["substitutions"] == 1

    # Case 3: One deletion, one insertion in words
    ref_words = "The quick brown fox jumps"
    hyp_words = "The fast brown fox"
    wer_res = TextExtractionMetrics.calculate_wer(ref_words, hyp_words)
    # ref: 5 words. hyp has 4 words (1 sub 'quick'->'fast', 1 del 'jumps')
    assert wer_res["wer"] == 2 / 5
    assert wer_res["word_accuracy"] == 3 / 5


def test_ocr_003_exact_field_matching():
    """OCR-003: Verify exact field match ratio calculation on structured fields."""
    predictions = ["INV-001", "2024-05-12", "$500.00", "Paid"]
    ground_truths = ["INV-001", "2024-05-12", "$500.00", "Unpaid"]

    res = TextExtractionMetrics.calculate_exact_match(predictions, ground_truths)
    assert res["total"] == 4
    assert res["correct"] == 3
    assert res["exact_match_ratio"] == 0.75


def test_ocr_004_text_normalizer():
    """OCR-004: Verify Unicode normalization, ligature decomposition, and hyphen cleanup."""
    # Ligatures: fi (\ufb01), fl (\ufb02)
    ligature_text = "The \ufb01rst \ufb02oor"
    cleaned = TextNormalizer.decompose_ligatures(ligature_text)
    assert cleaned == "The first floor"

    # Soft hyphen (\u00ad) and non-breaking hyphen (\u2011)
    hyphen_text = "multi\u00adlingual cross\u2011document"
    cleaned_hyphen = TextNormalizer.normalize_hyphens(hyphen_text)
    assert cleaned_hyphen == "multilingual cross-document"

    # Whitespace cleanup with non-breaking space (\u00a0)
    dirty_ws = "  Hello \u00a0 World!   \n\n  Line 2   "
    cleaned_ws = TextNormalizer.normalize_whitespace(dirty_ws, preserve_newlines=True)
    assert cleaned_ws == "Hello World!\n\nLine 2"


def test_ocr_005_confidence_calibration_ece():
    """OCR-005: Verify confidence distribution tracking and Expected Calibration Error (ECE)."""
    # 5 samples: perfectly calibrated (conf 0.9 with acc 1.0, conf 0.2 with acc 0.0, etc.)
    confidences = [0.95, 0.90, 0.50, 0.20, 0.10]
    accuracies = [1.0, 1.0, 1.0, 0.0, 0.0]

    dist = ConfidenceEvaluator.compute_distribution(confidences)
    assert dist["recorded_count"] == 5
    assert dist["missing_count"] == 0
    assert dist["mean"] == 0.53

    ece, bins = ConfidenceEvaluator.compute_ece(confidences, accuracies, n_bins=5)
    assert ece >= 0.0
    assert isinstance(bins, dict)


def test_ocr_006_empty_and_corrupt_page_handling(tmp_path, extraction_schema):
    """OCR-006: Verify empty PDF page yields EMPTY_PAGE status without crashing."""
    import fitz
    # Create empty 1-page PDF
    doc = fitz.open()
    doc.new_page(width=612, height=792)
    empty_pdf = tmp_path / "blank.pdf"
    doc.save(str(empty_pdf))
    doc.close()

    extractor = NativePDFExtractor()
    results = extractor.extract_document(empty_pdf, document_id="DOC_BLANK")
    assert len(results) == 1
    blank_page = results[0]
    assert blank_page.processing_status == "EMPTY_PAGE"
    assert blank_page.text == ""

    jsonschema.validate(blank_page.to_schema_dict(), extraction_schema)


def test_ocr_007_schema_conformance(extraction_schema):
    """OCR-007: Verify PageTextExtraction model output against JSON schema."""
    page = PageTextExtraction(
        document_id="DOC-999",
        page_number=2,
        extraction_method=ExtractionMethod.OCR,
        engine="Tesseract",
        engine_version="5.3.0",
        language=["en", "es"],
        text="Extracted text block",
        confidence=0.88,
        blocks=[
            {
                "block_id": "BLOCK-001",
                "text": "Extracted text block",
                "bbox": [50.0, 100.0, 200.0, 140.0],
                "confidence": 0.88,
            }
        ],
        processing_status="SUCCESS",
    )
    jsonschema.validate(page.to_schema_dict(), extraction_schema)
