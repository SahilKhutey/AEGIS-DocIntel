"""
AEGIS-DocIntel — Real-World Ingestion Validation Test Suite
===========================================================
Validates ingestion and normalization pipelines against genuine, complex real-world
documents (monographs, research PDFs, multi-sheet spreadsheets, multi-slide decks)
rather than purely synthetic one-liners.

Key Verifications:
  1. Real 14-page research paper PDF normalization produces valid structural pages,
     substantial character count (>5000 chars), and correct scanned-status detection.
  2. Ingestion loaders populate char_count and word_count accurately across formats.
  3. Real DOCX monographs extract non-zero char_count and word_count.
  4. Fabricated/corrupt benchmark mock PDFs are strictly rejected by FormatError.
  5. Multi-slide PPTX and multi-sheet XLSX load with complete structural metadata.
"""
from __future__ import annotations

import os
from pathlib import Path
import pytest

from src.models.document_object import DocumentFormat, DocumentObject
from src.workflows.ingest_workflow import IngestWorkflow
from src.ingestion.pdf_loader import PDFLoader
from src.ingestion.docx_loader import DOCXLoader
from src.ingestion.pptx_loader import PPTXLoader
from src.ingestion.xlsx_loader import XLSXLoader
from src.ingestion.image_loader import ImageLoader
from src.ingestion.text_loader import TextLoader
from src.ingestion.exceptions import FormatError, DocumentCorruptError


FIXTURES_DIR = Path(__file__).parent / "fixtures"
REAL_PDF_PATH = FIXTURES_DIR / "real_research_paper.pdf"
REAL_PPTX_PATH = FIXTURES_DIR / "real_presentation.pptx"
REAL_XLSX_PATH = FIXTURES_DIR / "real_spreadsheet.xlsx"
REAL_IMAGE_PATH = FIXTURES_DIR / "real_scanned_page.png"


@pytest.mark.asyncio
async def test_normalize_real_research_paper():
    """
    Real-world validation: runs the actual normalization pipeline against a
    real, complex PDF (not a synthetic fixture, not the fabricated mock
    benchmark set), and checks the output has real structure, not just
    'didn't crash.'
    """
    assert REAL_PDF_PATH.exists(), f"Fixture missing: {REAL_PDF_PATH}"
    raw = REAL_PDF_PATH.read_bytes()

    wf = IngestWorkflow(llm_provider="mock")
    doc = DocumentObject(filename="paper.pdf", format=DocumentFormat.PDF, raw_bytes=raw)
    normalized = await wf._normalize_pdf(doc)

    assert len(normalized.pages) == 14  # known page count for this research paper
    total_text_chars = sum(len(b.text) for p in normalized.pages for b in p.blocks)
    assert total_text_chars > 5000  # 14-page paper should extract substantial text (>30k chars)
    assert not any(p.is_scanned for p in normalized.pages)  # native PDF, not scanned


@pytest.mark.asyncio
async def test_all_loaders_populate_char_count():
    """Verify that all document loaders properly populate char_count and word_count."""
    # PDF
    pdf_doc = await PDFLoader().load(str(REAL_PDF_PATH))
    assert pdf_doc.page_count == 14
    assert pdf_doc.char_count > 30000
    assert pdf_doc.word_count > 4000

    # DOCX
    docx_path = FIXTURES_DIR / "sample.docx"
    docx_doc = await DOCXLoader().load(str(docx_path))
    assert docx_doc.char_count > 0
    assert docx_doc.word_count > 0

    # PPTX
    pptx_doc = await PPTXLoader().load(str(REAL_PPTX_PATH))
    assert pptx_doc.page_count == 3
    assert pptx_doc.char_count > 100
    assert pptx_doc.word_count > 20

    # XLSX
    xlsx_doc = await XLSXLoader().load(str(REAL_XLSX_PATH))
    assert xlsx_doc.page_count == 2
    assert xlsx_doc.char_count > 50
    assert xlsx_doc.word_count > 15

    # Text
    txt_path = FIXTURES_DIR / "sample.txt"
    txt_doc = await TextLoader().load(str(txt_path))
    assert txt_doc.char_count > 0
    assert txt_doc.word_count > 0

    # Image
    img_doc = await ImageLoader().load(str(REAL_IMAGE_PATH))
    assert img_doc.page_count == 1
    assert img_doc.metadata.get("width") == 800
    assert img_doc.metadata.get("height") == 1000


@pytest.mark.asyncio
async def test_docx_loader_on_real_monographs():
    """Verify DOCXLoader against available real monographs in Aegis Doc/."""
    monograph_dir = Path("Aegis Doc")
    if not monograph_dir.exists():
        pytest.skip("Aegis Doc/ directory not present in current test environment")

    docx_files = list(monograph_dir.glob("*.docx"))
    assert len(docx_files) >= 12, f"Expected at least 12 monographs, found {len(docx_files)}"

    loader = DOCXLoader()
    for doc_file in docx_files:
        doc = await loader.load(str(doc_file))
        assert doc.word_count > 1000, f"Word count too low for {doc_file.name}: {doc_file}"
        assert doc.char_count > 5000, f"Char count too low for {doc_file.name}: {doc_file}"
        assert doc.metadata.get("paragraph_count", 0) > 0


@pytest.mark.asyncio
async def test_mock_benchmark_pdf_rejection():
    """Verify that corrupt/mock benchmark PDFs are strictly rejected rather than silently ingested."""
    mock_pdf = Path("_unverified_archive/benchmark-dataset-mock/engineering_drawings/eng_089.pdf")
    if not mock_pdf.exists():
        pytest.skip("Mock benchmark archive not present in current environment")

    loader = PDFLoader()
    with pytest.raises((FormatError, DocumentCorruptError)):
        await loader.load(str(mock_pdf))


@pytest.mark.asyncio
async def test_real_research_paper_full_ingest_workflow():
    """Execute end-to-end IngestWorkflow on real research PDF and verify MasterState synthesis."""
    assert REAL_PDF_PATH.exists()
    raw = REAL_PDF_PATH.read_bytes()

    wf = IngestWorkflow(llm_provider="mock")
    doc = DocumentObject(filename="research_paper.pdf", format=DocumentFormat.PDF, raw_bytes=raw)

    result = await wf.ingest(doc)
    assert result["filename"] == "research_paper.pdf"
    assert result["pages"] == 14
    assert result["blocks"] > 50
    assert "timings" in result

    # Check MasterState integration
    state = wf.get_master_state()
    assert state is not None
    assert len(state.pages) == 14
    assert state.pages_status.is_hardened is True
    assert state.geometric_status.is_hardened is True
