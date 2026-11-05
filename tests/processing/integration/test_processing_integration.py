"""
tests/processing/integration/test_processing_integration.py
===========================================================
Integration tests INT-PROC-001 through INT-PROC-010 validating the unified document
processing pipeline, intermediate stage preservation, and performance monitoring.
"""

import json
from pathlib import Path
import pytest
import jsonschema

from aegis.processing import DocumentProcessingPipeline, ProcessingStatus
from aegis.processing.benchmarking.resource_monitor import ResourceMonitor

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RESULT_SCHEMA_FILE = REPO_ROOT / "schemas" / "processing" / "processing_result.schema.json"


@pytest.fixture
def result_schema():
    with open(RESULT_SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_int_proc_001_end_to_end_pipeline_success(result_schema):
    """INT-PROC-001: Process sample digital PDF through full pipeline."""
    pdf_path = REPO_ROOT / "tests" / "fixtures" / "sample.pdf"
    if not pdf_path.exists():
        pytest.skip("sample.pdf missing")

    pipeline = DocumentProcessingPipeline()
    res = pipeline.process_document(pdf_path, document_id="DOC_SAMPLE_INTEG")

    assert res.status == ProcessingStatus.SUCCESS
    assert res.page_count >= 1
    assert "extraction" in res.completed_stages
    assert "layout_analysis" in res.completed_stages
    assert "reading_order" in res.completed_stages
    assert len(res.pages) >= 1

    jsonschema.validate(res.to_schema_dict(), result_schema)


def test_int_proc_002_intermediate_outputs_preserved():
    """INT-PROC-002: Verify intermediate outputs (text, regions, reading order, tables) are preserved."""
    pdf_path = REPO_ROOT / "tests" / "fixtures" / "sample.pdf"
    if not pdf_path.exists():
        pytest.skip("sample.pdf missing")

    pipeline = DocumentProcessingPipeline()
    res = pipeline.process_document(pdf_path)

    page1 = res.pages[0]
    assert "extraction" in page1
    assert "layout_regions" in page1
    assert "reading_order" in page1
    assert "tables" in page1

    assert isinstance(page1["extraction"]["blocks"], list)
    assert isinstance(page1["layout_regions"], list)
    assert isinstance(page1["reading_order"]["reading_order"], list)


def test_int_proc_003_multi_column_paper_integration():
    """INT-PROC-003: Process multi-column research paper fixture."""
    pdf_path = REPO_ROOT / "tests" / "fixtures" / "real_research_paper.pdf"
    if not pdf_path.exists():
        pytest.skip("real_research_paper.pdf missing")

    pipeline = DocumentProcessingPipeline()
    res = pipeline.process_document(pdf_path, document_id="DOC_RESEARCH_PAPER")

    assert res.status == ProcessingStatus.SUCCESS
    assert res.page_count >= 1
    # Check that layout regions are detected across pages
    total_regions = sum(len(p["layout_regions"]) for p in res.pages)
    assert total_regions > 0


def test_int_proc_004_mixed_or_scanned_pdf_handling(tmp_path):
    """INT-PROC-004: Verify scanned PDF or image page invokes OCR path without crash."""
    import fitz
    # Create 1-page PDF with empty text (simulating pure image/scan)
    doc = fitz.open()
    doc.new_page(width=612, height=792)
    scanned_mock = tmp_path / "mock_scan.pdf"
    doc.save(str(scanned_mock))
    doc.close()

    pipeline = DocumentProcessingPipeline()
    res = pipeline.process_document(scanned_mock, document_id="DOC_MOCK_SCAN")

    assert res.status == ProcessingStatus.SUCCESS
    assert res.page_count == 1
    # Check that OCR extraction was selected
    assert res.pages[0]["extraction"]["extraction_method"] == "ocr"


def test_int_proc_005_table_extraction_integration():
    """INT-PROC-005: Verify table extraction stage output structure."""
    pdf_path = REPO_ROOT / "tests" / "fixtures" / "sample.pdf"
    if not pdf_path.exists():
        pytest.skip("sample.pdf missing")

    pipeline = DocumentProcessingPipeline()
    res = pipeline.process_document(pdf_path)

    # Tables list exists on page result
    assert "tables" in res.pages[0]
    assert isinstance(res.pages[0]["tables"], list)


def test_int_proc_006_field_provenance_integration():
    """INT-PROC-006: Verify field-level provenance tracking links to document and run."""
    pipeline = DocumentProcessingPipeline()
    res = pipeline.process_document(REPO_ROOT / "tests" / "fixtures" / "sample.pdf")

    assert res.processing_run_id.startswith("RUN-")
    assert res.document_id.startswith("SAMPLE")


def test_int_proc_007_schema_conformance_full_result(result_schema):
    """INT-PROC-007: Validate full result conforming to processing_result.schema.json."""
    pipeline = DocumentProcessingPipeline()
    res = pipeline.process_document(REPO_ROOT / "tests" / "fixtures" / "sample.pdf")
    jsonschema.validate(res.to_schema_dict(), result_schema)


def test_int_proc_008_resource_monitor_profiling():
    """INT-PROC-008: Verify ResourceMonitor calculates median, p95, p99 latencies."""
    doc_latencies = [10.0, 15.0, 20.0, 25.0, 100.0]
    page_latencies = [5.0, 7.5, 10.0, 12.5, 50.0]

    metrics = ResourceMonitor.summarize(
        doc_latencies_ms=doc_latencies,
        page_latencies_ms=page_latencies,
        total_pages=10,
        total_elapsed_seconds=0.17,
        peak_memory_mb=128.5,
    )

    assert metrics.total_documents == 5
    assert metrics.total_pages == 10
    assert metrics.latency_per_doc_median_ms == 20.0
    assert metrics.latency_per_doc_p95_ms == 100.0
    assert metrics.throughput_pages_per_sec > 0.0


def test_int_proc_009_sandbox_recovery_on_corrupt(tmp_path):
    """INT-PROC-009: Corrupt document failure does not contaminate subsequent pipeline run."""
    bad_file = tmp_path / "bad.pdf"
    bad_file.write_bytes(b"garbage bytes")

    good_file = REPO_ROOT / "tests" / "fixtures" / "sample.pdf"

    pipeline = DocumentProcessingPipeline()
    # 1. Run corrupt file
    res_bad = pipeline.process_document(bad_file)
    assert res_bad.status == ProcessingStatus.INVALID_FORMAT

    # 2. Run valid file immediately after
    res_good = pipeline.process_document(good_file)
    assert res_good.status == ProcessingStatus.SUCCESS


def test_int_proc_010_reproducibility_deterministic_runs():
    """INT-PROC-010: Processing same document twice produces identical structural results."""
    good_file = REPO_ROOT / "tests" / "fixtures" / "sample.pdf"
    pipeline = DocumentProcessingPipeline()

    res_1 = pipeline.process_document(good_file, document_id="DOC_DET")
    res_2 = pipeline.process_document(good_file, document_id="DOC_DET")

    # Identical page count and text
    assert res_1.page_count == res_2.page_count
    assert res_1.pages[0]["extraction"]["text"] == res_2.pages[0]["extraction"]["text"]
    assert res_1.pages[0]["reading_order"]["reading_order"] == res_2.pages[0]["reading_order"]["reading_order"]
