"""
AEGIS-DocIntel — IngestWorkflow Comprehensive Integration Test Suite
====================================================================
Tests multi-format ingestion pipelines across PDF, DOCX, PPTX, XLSX, IMAGE, and TEXT,
and validates failure modes against corrupted inputs.
"""
from __future__ import annotations

import pytest
from src.ingestion.exceptions import IngestionError
from src.models.document_object import DocumentFormat, DocumentObject
from src.workflows.ingest_workflow import IngestWorkflow


@pytest.fixture
def workflow():
    return IngestWorkflow(llm_provider="mock")


@pytest.mark.parametrize(
    "fmt,fixture_path",
    [
        (DocumentFormat.PDF, "tests/fixtures/sample.pdf"),
        (DocumentFormat.DOCX, "tests/fixtures/sample.docx"),
        (DocumentFormat.PPTX, "tests/fixtures/sample.pptx"),
        (DocumentFormat.XLSX, "tests/fixtures/sample.xlsx"),
        (DocumentFormat.IMAGE, "tests/fixtures/sample.png"),
        (DocumentFormat.TEXT, "tests/fixtures/sample.txt"),
    ],
)
@pytest.mark.asyncio
async def test_ingest_produces_valid_master_state(workflow, fmt, fixture_path):
    """
    Exercises every _normalize_* branch in ingest_workflow.py — one real fixture
    per format branch rather than a single happy-path test.
    """
    with open(fixture_path, "rb") as f:
        raw_bytes = f.read()

    doc = DocumentObject(filename=fixture_path, format=fmt, raw_bytes=raw_bytes)
    state = await workflow.ingest(doc)

    assert state.doc_id == doc.doc_id
    assert len(state.pages) > 0
    assert state.pages_status.is_hardened

    # Format-specific checks
    if fmt == DocumentFormat.XLSX:
        assert state.tables is not None and len(state.tables) > 0
    if fmt == DocumentFormat.IMAGE:
        assert len(state.pages[0].elements) > 0
        assert state.pages[0].elements[0].element_type in ("text", "figure")

    # Verify underlying MasterState
    master_state = workflow.get_master_state()
    assert master_state.doc_id == doc.doc_id
    assert master_state.pages_status.is_hardened
    assert master_state.matrix_status.is_hardened
    assert master_state.geometric_status.is_hardened


@pytest.mark.asyncio
async def test_ingest_handles_corrupt_file_gracefully(workflow):
    """Real failure-mode test: corrupt file binary structure raises IngestionError."""
    doc = DocumentObject(filename="corrupt.pdf", format=DocumentFormat.PDF, raw_bytes=b"not a real pdf")
    with pytest.raises(IngestionError):
        await workflow.ingest(doc)


@pytest.mark.asyncio
async def test_ingest_lifecycle_methods(workflow):
    """Verify async initialize and shutdown methods complete cleanly."""
    await workflow.initialize()
    await workflow.shutdown()
