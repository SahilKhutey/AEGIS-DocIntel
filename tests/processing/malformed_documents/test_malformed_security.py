"""
tests/processing/malformed_documents/test_malformed_security.py
===============================================================
Tests MAL-001 through MAL-010 verifying malformed document rejection,
resource limits, timeout containment, security sandboxing, and safe error reporting.
"""

import json
import time
from pathlib import Path
import pytest
import jsonschema

from aegis.processing.models import DocumentProcessingResult, ProcessingStatus
from aegis.processing.pipeline import DocumentProcessingPipeline
from aegis.processing.security import ErrorClassifier, ProcessingSandbox
from aegis.processing.validation import FileValidator, ResourceLimitsConfig

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RESULT_SCHEMA_FILE = REPO_ROOT / "schemas" / "processing" / "processing_result.schema.json"


@pytest.fixture
def result_schema():
    with open(RESULT_SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_mal_001_invalid_extension_and_signature(tmp_path):
    """MAL-001: Reject random bytes with .pdf extension as INVALID_FORMAT."""
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"THIS IS NOT A VALID PDF FILE AT ALL!")

    pipeline = DocumentProcessingPipeline()
    res = pipeline.process_document(fake_pdf)

    assert res.status == ProcessingStatus.INVALID_FORMAT
    assert res.error is not None
    assert res.error.code == "INVALID_FILE_SIGNATURE"


def test_mal_002_corrupted_truncated_pdf(tmp_path):
    """MAL-002: Reject truncated PDF structure as CORRUPTED_DOCUMENT."""
    corrupt_pdf = tmp_path / "truncated.pdf"
    corrupt_pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF")

    pipeline = DocumentProcessingPipeline()
    res = pipeline.process_document(corrupt_pdf)

    assert res.status == ProcessingStatus.CORRUPTED_DOCUMENT
    assert res.error is not None
    assert res.error.code == "ZERO_PAGE_PDF" or "PARSING" in res.error.code


def test_mal_003_zero_byte_empty_file(tmp_path):
    """MAL-003: Reject zero-byte file without crashing as CORRUPTED_DOCUMENT."""
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")

    pipeline = DocumentProcessingPipeline()
    res = pipeline.process_document(empty_file)

    assert res.status == ProcessingStatus.CORRUPTED_DOCUMENT
    assert res.error is not None
    assert res.error.code == "EMPTY_FILE"


def test_mal_004_oversized_file_limit(tmp_path):
    """MAL-004: Reject file exceeding configured max size limit before expensive processing."""
    big_file = tmp_path / "large.pdf"
    # Create 2 KB file with 1 KB limit
    big_file.write_bytes(b"%PDF-1.4\n" + b"A" * 2048)

    strict_limits = ResourceLimitsConfig(max_file_size_bytes=1024)
    pipeline = DocumentProcessingPipeline(limits=strict_limits)
    res = pipeline.process_document(big_file)

    assert res.status == ProcessingStatus.RESOURCE_LIMIT_EXCEEDED
    assert res.error.code == "MAX_FILE_SIZE_EXCEEDED"


def test_mal_005_page_count_limit(tmp_path):
    """MAL-005: Reject PDF exceeding page count limit as RESOURCE_LIMIT_EXCEEDED."""
    import fitz
    doc = fitz.open()
    for _ in range(5):
        doc.new_page(width=100, height=100)
    pdf_path = tmp_path / "multipage.pdf"
    doc.save(str(pdf_path))
    doc.close()

    strict_limits = ResourceLimitsConfig(max_pages=3)
    pipeline = DocumentProcessingPipeline(limits=strict_limits)
    res = pipeline.process_document(pdf_path)

    assert res.status == ProcessingStatus.RESOURCE_LIMIT_EXCEEDED
    assert res.error.code == "PAGE_COUNT_EXCEEDED"


def test_mal_006_page_dimension_limit(tmp_path):
    """MAL-006: Reject huge page dimensions (> 10,000 pt) as RESOURCE_LIMIT_EXCEEDED."""
    import fitz
    doc = fitz.open()
    doc.new_page(width=15000, height=15000)
    pdf_path = tmp_path / "huge_page.pdf"
    doc.save(str(pdf_path))
    doc.close()

    strict_limits = ResourceLimitsConfig(max_page_dimension_points=10000.0)
    pipeline = DocumentProcessingPipeline(limits=strict_limits)
    res = pipeline.process_document(pdf_path)

    assert res.status == ProcessingStatus.RESOURCE_LIMIT_EXCEEDED
    assert res.error.code == "PAGE_DIMENSION_EXCEEDED"


def test_mal_007_path_traversal_detection(tmp_path):
    """MAL-007: Reject filenames with illegal traversal sequences as SECURITY_REJECTED."""
    validator = FileValidator()
    res = validator.validate_file(tmp_path / ".." / "traversal.pdf")
    assert res.is_valid is False
    assert res.status == ProcessingStatus.SECURITY_REJECTED


def test_mal_008_processing_timeout_sandbox():
    """MAL-008: Verify sandbox intercepts long-running tasks and returns TIMEOUT status."""
    sandbox = ProcessingSandbox(timeout_seconds=0.1)

    def slow_task():
        time.sleep(0.5)
        return "done"

    res = sandbox.execute_bounded(slow_task, document_id="DOC_SLOW", processing_run_id="RUN_SLOW")
    assert res.status == ProcessingStatus.TIMEOUT
    assert res.error is not None
    assert res.error.code == "TASK_TIMEOUT"


def test_mal_009_sanitized_error_reporting():
    """MAL-009: Error responses sanitize local filesystem paths and stack traces."""
    leak_error = Exception(r"Failed to open C:\Users\Admin\SecretData\confidential.pdf: file corrupt")
    status, err = ErrorClassifier.classify_exception(leak_error)

    assert "C:\\Users" not in err.message
    assert "<REDACTED_PATH>" in err.message
    assert err.code == "DOCUMENT_CORRUPTED"


def test_mal_010_schema_conformance(result_schema, tmp_path):
    """MAL-010: Validate DocumentProcessingResult matches processing_result.schema.json."""
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"not a pdf")
    pipeline = DocumentProcessingPipeline()
    res = pipeline.process_document(fake_pdf)

    jsonschema.validate(res.to_schema_dict(), result_schema)
