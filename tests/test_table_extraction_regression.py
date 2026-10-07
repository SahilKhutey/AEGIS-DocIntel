"""
Regression tests for Table Extraction and Silent Failure Guards.
=================================================================
Ensures table extraction runs real PyMuPDF + pdfplumber extraction
without encountering the former AttributeError (page_obj.parent.to_bytes)
or TypeError (pdfplumber.open(stream=...)) bugs that were swallowed
silently by bare `except Exception: pass`.
"""
from __future__ import annotations

from pathlib import Path
import pytest

from src.workflows.ingest_workflow import IngestWorkflow
from src.models.document_object import DocumentObject, DocumentFormat
from src.core.normalized_document import BlockType

TABLE_CURVES_PDF = Path("production/benchmark-dataset-real/pdf-corpus/table-curves-example.pdf")
FEDERAL_REGISTER_PDF = Path("production/benchmark-dataset-real/pdf-corpus/federal-register-2020-17221.pdf")
NO_TABLES_PDF = Path("production/benchmark-dataset-real/pdf-corpus/issue-982-example.pdf")


@pytest.mark.asyncio
async def test_table_extraction_regression_table_curves():
    """Verify table-curves-example.pdf detects at least 1 table.

    Formerly failed with:
    - AttributeError: 'Document' object has no attribute 'to_bytes'
    - TypeError: pdfplumber.open() got an unexpected keyword argument 'stream'
    both swallowed silently, returning 0 tables.
    """
    assert TABLE_CURVES_PDF.exists(), f"Corpus fixture missing: {TABLE_CURVES_PDF}"
    raw = TABLE_CURVES_PDF.read_bytes()
    doc = DocumentObject(filename="table-curves-example.pdf", format=DocumentFormat.PDF, raw_bytes=raw)

    wf = IngestWorkflow(llm_provider="mock")
    norm = await wf._normalize_pdf(doc)

    tables = [b for p in norm.pages for b in p.blocks if b.type == BlockType.TABLE]
    assert len(tables) >= 1, (
        f"Expected at least 1 table in {TABLE_CURVES_PDF.name}, found 0. "
        "Table extraction silent-failure regression detected."
    )
    assert len(tables[0].text.strip()) > 0, "Extracted table markdown content should not be empty"


@pytest.mark.asyncio
async def test_table_extraction_federal_register():
    """Verify federal-register-2020-17221.pdf detects real tabular structures."""
    assert FEDERAL_REGISTER_PDF.exists(), f"Corpus fixture missing: {FEDERAL_REGISTER_PDF}"
    raw = FEDERAL_REGISTER_PDF.read_bytes()
    doc = DocumentObject(filename="federal-register-2020-17221.pdf", format=DocumentFormat.PDF, raw_bytes=raw)

    wf = IngestWorkflow(llm_provider="mock")
    norm = await wf._normalize_pdf(doc)

    tables = [b for p in norm.pages for b in p.blocks if b.type == BlockType.TABLE]
    assert len(tables) >= 1, (
        f"Expected tables in {FEDERAL_REGISTER_PDF.name}, found 0."
    )


@pytest.mark.asyncio
async def test_table_extraction_negative_case():
    """Verify issue-982-example.pdf correctly reports 0 tables (not false positives)."""
    assert NO_TABLES_PDF.exists(), f"Corpus fixture missing: {NO_TABLES_PDF}"
    raw = NO_TABLES_PDF.read_bytes()
    doc = DocumentObject(filename="issue-982-example.pdf", format=DocumentFormat.PDF, raw_bytes=raw)

    wf = IngestWorkflow(llm_provider="mock")
    norm = await wf._normalize_pdf(doc)

    tables = [b for p in norm.pages for b in p.blocks if b.type == BlockType.TABLE]
    assert len(tables) == 0, f"Expected 0 tables in non-table document, found {len(tables)}"
