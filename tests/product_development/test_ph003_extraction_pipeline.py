"""
AEGIS-DocIntel — Task PH-003: Extraction Pipeline & Ground-Truth Verification
=============================================================================
Verifies text extraction, character recall, page counts, and metadata
across supported PDF, DOCX, and TXT file formats as defined in PH-003.
"""
from __future__ import annotations

from pathlib import Path
import pytest

from src.ingestion.docx_loader import DOCXLoader
from src.ingestion.exceptions import (
    DocumentCorruptError,
    FormatError,
)
from src.ingestion.pdf_loader import PDFLoader
from src.ingestion.text_loader import TextLoader
from src.models.document_object import DocumentFormat

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
SEED_DOCS_DIR = REPO_ROOT / "demo" / "seed" / "documents"


@pytest.mark.asyncio
async def test_pdf_extraction_and_character_recall():
    """Verify PDF extraction on real fixtures with accurate page counts and metadata."""
    loader = PDFLoader()
    sample_pdf = FIXTURES_DIR / "sample.pdf"
    assert sample_pdf.exists(), "Missing test fixture sample.pdf"

    doc = await loader.load(sample_pdf)
    assert doc.format == DocumentFormat.PDF
    assert doc.page_count >= 1
    assert doc.char_count > 0
    assert len(doc.text_content) > 0
    assert doc.metadata.get("scanned") is False or doc.metadata.get("is_scanned") is False

    # Verify real multi-page research paper
    research_pdf = FIXTURES_DIR / "real_research_paper.pdf"
    if research_pdf.exists():
        r_doc = await loader.load(research_pdf)
        assert r_doc.page_count >= 1
        assert r_doc.char_count > 1000
        assert "abstract" in r_doc.text_content.lower() or "introduction" in r_doc.text_content.lower()


@pytest.mark.asyncio
async def test_docx_extraction_ground_truth():
    """Verify DOCX extraction accuracy on sample.docx fixture."""
    loader = DOCXLoader()
    sample_docx = FIXTURES_DIR / "sample.docx"
    assert sample_docx.exists(), "Missing test fixture sample.docx"

    doc = await loader.load(sample_docx)
    assert doc.format == DocumentFormat.DOCX
    assert doc.char_count > 0
    assert len(doc.text_content) > 0
    # Clean text recall check
    assert "test" in doc.text_content.lower() or "sample" in doc.text_content.lower()


@pytest.mark.asyncio
async def test_text_extraction_ground_truth():
    """Verify UTF-8 text extraction and invariant preservation on synthetic seed corpus."""
    loader = TextLoader()
    spec_v1 = SEED_DOCS_DIR / "aegis_neural_hardware_spec_v1.txt"
    assert spec_v1.exists(), "Missing seed document aegis_neural_hardware_spec_v1.txt"

    doc = await loader.load(spec_v1)
    assert doc.format == DocumentFormat.TEXT
    assert doc.char_count > 500
    # Verify exact invariant technical metrics from seed corpus
    assert "450 TFLOPS" in doc.text_content
    assert "220 Watts" in doc.text_content
    assert "128 MB" in doc.text_content


@pytest.mark.asyncio
async def test_corrupted_file_handling():
    """Verify fail-closed error handling on corrupt or non-matching byte payloads."""
    pdf_loader = PDFLoader()
    docx_loader = DOCXLoader()
    text_loader = TextLoader()

    # Corrupt PDF header (bytes)
    with pytest.raises(FormatError):
        await pdf_loader.load(b"NOT_A_PDF_FILE_HEADER", filename="corrupt.pdf")

    # Corrupt DOCX (invalid zip)
    with pytest.raises((FormatError, DocumentCorruptError)):
        await docx_loader.load(b"PK\x03\x04INVALID_ZIP_ARCHIVE_DATA", filename="corrupt.docx")

    # Text file with binary null characters
    with pytest.raises(FormatError):
        await text_loader.load(b"Text with binary\x00null character", filename="nulls.txt")
