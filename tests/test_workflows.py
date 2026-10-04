"""
AEGIS-DocIntel — Workflows Unit Test Suite
===========================================
Dedicated unit tests for:
  - IngestWorkflow (src/workflows/ingest_workflow.py)
  - QueryWorkflow (src/workflows/query_workflow.py)
  - ExportWorkflow (src/workflows/export_workflow.py)
  - BatchWorkflow (src/workflows/batch_workflow.py)
Closes the workflow coverage gap identified in STATUS.md.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest

from src.models.document_object import DocumentFormat, DocumentObject
from src.workflows.batch_workflow import BatchWorkflow
from src.workflows.export_workflow import ExportWorkflow
from src.workflows.ingest_workflow import IngestWorkflow
from src.workflows.query_workflow import QueryWorkflow


@pytest.fixture
def sample_document():
    """Create a sample DocumentObject with text content for workflow processing."""
    content = (
        "# Executive Summary\n\n"
        "Project Aegis demonstrated a 65% token reduction across document processing.\n"
        "Revenue grew by 24% year over year reaching $12.4 million.\n\n"
        "## Performance Metrics\n"
        "System latency was measured under 250ms per query.\n"
    )
    return DocumentObject(
        filename="executive_summary.txt",
        format=DocumentFormat.TEXT,
        raw_bytes=content.encode("utf-8"),
        text_content=content,
    )


# ============================================================================
# IngestWorkflow Tests
# ============================================================================

@pytest.mark.asyncio
async def test_ingest_workflow_lifecycle(sample_document):
    """Test full IngestWorkflow execution from initialization to state retrieval."""
    workflow = IngestWorkflow(llm_provider="mock")

    # Ingest document
    result = await workflow.ingest(sample_document)

    assert "doc_id" in result
    assert result["filename"] == "executive_summary.txt"
    assert result["pages"] >= 1
    assert result["blocks"] >= 1
    assert "timings" in result
    assert "phase1_load_s" in result["timings"]
    assert "phase2_normalize_s" in result["timings"]

    # Verify state snapshot
    state = workflow.get_state()
    assert state["filename"] == "executive_summary.txt"
    assert len(state["elements"]) > 0
    assert state["geometry"] is not None
    assert state["matrix"] is not None
    assert state["recurrence"] is not None
    assert state["template"] is not None

    await workflow.shutdown()


@pytest.mark.asyncio
async def test_ingest_workflow_from_bytes():
    """Test IngestWorkflow ingesting directly from raw bytes."""
    workflow = IngestWorkflow(llm_provider="mock")
    data = b"Quarterly review data: Product Alpha grew 15%."

    result = await workflow.ingest(data, filename="quarterly.txt")
    assert result["filename"] == "quarterly.txt"
    assert result["blocks"] >= 1

    await workflow.shutdown()


# ============================================================================
# QueryWorkflow Tests
# ============================================================================

@pytest.mark.asyncio
async def test_query_workflow_execution(sample_document):
    """Test QueryWorkflow query and response structure."""
    ingest_wf = IngestWorkflow(llm_provider="mock")
    await ingest_wf.ingest(sample_document)

    query_wf = QueryWorkflow(ingest=ingest_wf, llm_provider="mock")

    res = await query_wf.query("What was the token reduction percentage?", top_k=4)

    assert res["question"] == "What was the token reduction percentage?"
    assert "answer" in res
    assert "query_type" in res
    assert "dominant_layer" in res
    assert "weights" in res
    assert "latency_s" in res
    assert res["selected_elements"] >= 0

    await ingest_wf.shutdown()


@pytest.mark.asyncio
async def test_query_workflow_raises_without_ingest():
    """Verify QueryWorkflow raises error if queried before document ingestion."""
    empty_ingest = IngestWorkflow(llm_provider="mock")
    query_wf = QueryWorkflow(ingest=empty_ingest, llm_provider="mock")

    with pytest.raises(RuntimeError) as excinfo:
        await query_wf.query("What is the status?")
    assert "No document ingested" in str(excinfo.value)


# ============================================================================
# ExportWorkflow Tests
# ============================================================================

@pytest.mark.asyncio
async def test_export_workflow_build_ueo(sample_document):
    """Test ExportWorkflow UEO construction."""
    ingest_wf = IngestWorkflow(llm_provider="mock")
    await ingest_wf.ingest(sample_document)
    query_wf = QueryWorkflow(ingest=ingest_wf, llm_provider="mock")

    export_wf = ExportWorkflow(ingest=ingest_wf, query=query_wf)

    # List agents
    agents = export_wf.list_agents()
    assert isinstance(agents, list)
    assert len(agents) > 0
    assert "chatgpt" in agents or "claude" in agents or "gemini" in agents

    # Build UEO
    ueo = export_wf.build_ueo("Summarize revenue growth")
    assert ueo.metadata.document_name == "executive_summary.txt"
    assert ueo.query == "Summarize revenue growth"
    assert ueo.confidence.overall > 0.0
    assert isinstance(ueo.key_points, list)

    await ingest_wf.shutdown()


@pytest.mark.asyncio
async def test_export_workflow_export_mocked(sample_document):
    """Test ExportWorkflow export execution with mocked connector."""
    ingest_wf = IngestWorkflow(llm_provider="mock")
    await ingest_wf.ingest(sample_document)
    query_wf = QueryWorkflow(ingest=ingest_wf, llm_provider="mock")

    export_wf = ExportWorkflow(ingest=ingest_wf, query=query_wf)

    mock_send = AsyncMock(return_value={"status": "success", "content": "Verified answer"})
    with patch("src.workflows.export_workflow.get_connector") as mock_get_conn:
        mock_connector = AsyncMock()
        mock_connector.send = mock_send
        mock_get_conn.return_value = mock_connector

        res = await export_wf.export("What is the token reduction?", agent="chatgpt")
        assert res.get("status") == "success" or "raw_response" in res or "error" not in res

    await ingest_wf.shutdown()


# ============================================================================
# BatchWorkflow Tests
# ============================================================================

def test_batch_workflow_detect_format():
    """Test BatchWorkflow static format detector."""
    assert BatchWorkflow._detect_format(Path("doc.pdf")) == DocumentFormat.PDF
    assert BatchWorkflow._detect_format(Path("doc.docx")) == DocumentFormat.DOCX
    assert BatchWorkflow._detect_format(Path("doc.xlsx")) == DocumentFormat.XLSX
    assert BatchWorkflow._detect_format(Path("doc.pptx")) == DocumentFormat.PPTX
    assert BatchWorkflow._detect_format(Path("doc.png")) == DocumentFormat.IMAGE
    assert BatchWorkflow._detect_format(Path("doc.txt")) == DocumentFormat.TEXT
    assert BatchWorkflow._detect_format(Path("doc.unknown_ext")) is None


@pytest.fixture
def local_tmp_path():
    """Create local workspace temporary directory for sandboxed file operations."""
    p = Path("tests/temp_workflow_dir")
    p.mkdir(parents=True, exist_ok=True)
    yield p
    if p.exists():
        import shutil
        shutil.rmtree(p, ignore_errors=True)


@pytest.mark.asyncio
async def test_batch_workflow_process_files(local_tmp_path):
    """Test BatchWorkflow processing multiple files in parallel."""
    # Create two temporary text files
    f1 = local_tmp_path / "batch_file_1.txt"
    f1.write_text("Alpha report: metric score is 92%.", encoding="utf-8")

    f2 = local_tmp_path / "batch_file_2.txt"
    f2.write_text("Beta report: metric score is 88%.", encoding="utf-8")

    batch = BatchWorkflow(max_concurrent=2, llm_provider="mock")

    results = await batch.process_files([str(f1), str(f2)])
    assert len(results) == 2
    assert results[0]["status"] == "indexed"
    assert results[1]["status"] == "indexed"
    assert results[0]["filename"] == "batch_file_1.txt"
    assert results[1]["filename"] == "batch_file_2.txt"

    await batch.close_all()

