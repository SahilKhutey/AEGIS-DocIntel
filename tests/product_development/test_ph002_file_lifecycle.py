"""
AEGIS-DocIntel — Task PH-002: File Lifecycle & Storage Verification
===================================================================
Validates document upload, persistence, lifecycle transitions, checksums,
tenant isolation, and cascading deletion as defined in PH-002.
"""
from __future__ import annotations

import hashlib
import sqlite3
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.models.processing_contract import (
    OpaqueStorageReferenceError,
    validate_opaque_storage_reference,
)
from src.services.container import RealDocumentService


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_docs.db"
    return str(db_file)


@pytest.fixture
def mock_orchestrator():
    orchestrator = MagicMock()
    orchestrator.ingest = AsyncMock(return_value={"pages": 3, "elements": 12})
    orchestrator.vector_store = MagicMock()
    orchestrator.vector_store.delete = AsyncMock(return_value=True)
    orchestrator.semantic_cache = MagicMock()
    orchestrator.semantic_cache.invalidate = AsyncMock(return_value=True)
    return orchestrator


@pytest.fixture
def doc_service(mock_orchestrator, temp_db):
    service = RealDocumentService(orchestrator=mock_orchestrator, db_path=temp_db)
    return service


@pytest.mark.asyncio
async def test_opaque_storage_reference_security():
    """Verify that path traversal attempts in storage references fail closed."""
    # Valid opaque internal identifiers (PROT-FINAL-10 Section 3.3)
    validate_opaque_storage_reference("urn:amdi:blob:550e8400-e29b-41d4-a716-446655440000")
    validate_opaque_storage_reference("s3://tenant-alpha/blobs/ab12cd34ef56")
    validate_opaque_storage_reference("blob://storage-node-1/doc-99")
    validate_opaque_storage_reference("opaque:doc-uuid-12345")
    validate_opaque_storage_reference("sqlite:blob:chunk-456")

    # Path traversal and direct disk paths must fail closed by raising OpaqueStorageReferenceError
    with pytest.raises(OpaqueStorageReferenceError):
        validate_opaque_storage_reference("../../etc/shadow")

    with pytest.raises(OpaqueStorageReferenceError):
        validate_opaque_storage_reference("..\\..\\Windows\\System32\\cmd.exe")

    with pytest.raises(OpaqueStorageReferenceError):
        validate_opaque_storage_reference("/etc/passwd")

    with pytest.raises(OpaqueStorageReferenceError):
        validate_opaque_storage_reference("C:\\data\\documents.db")


@pytest.mark.asyncio
async def test_document_ingestion_and_lifecycle_tracking(doc_service):
    """Verify that document ingestion tracks lifecycle state from VALIDATING to READY."""
    payload = b"Hello AEGIS-DocIntel Document Intelligence Pipeline Test"
    sha256_expected = hashlib.sha256(payload).hexdigest()
    tenant_id = "tenant-prod-alpha"

    doc_resp = await doc_service.ingest(
        file_bytes=payload,
        filename="eval_report.pdf",
        content_type="application/pdf",
        tenant_id=tenant_id,
    )

    assert doc_resp.status == "ready"
    assert doc_resp.lifecycle_state == "READY"
    assert doc_resp.sha256 == sha256_expected
    assert doc_resp.page_count == 3
    assert doc_resp.chunk_count == 12

    # Verify query status returns correct lifecycle state
    status_resp = await doc_service.get_status(doc_id=doc_resp.doc_id, tenant_id=tenant_id)
    assert status_resp is not None
    assert status_resp.status == "ready"
    assert status_resp.lifecycle_state == "READY"
    assert status_resp.progress_percent == 100.0


@pytest.mark.asyncio
async def test_raw_bytes_retrieval_and_checksum_integrity(doc_service):
    """Verify raw bytes persistence and SHA-256 integrity verification."""
    payload = b"Confidential Research Data for Retrieval Benchmark"
    tenant_id = "tenant-integrity-test"

    doc_resp = await doc_service.ingest(
        file_bytes=payload,
        filename="research.txt",
        content_type="text/plain",
        tenant_id=tenant_id,
    )

    retrieved_bytes = doc_service._load_raw_bytes(doc_resp.doc_id, tenant_id=tenant_id)
    assert retrieved_bytes == payload

    # Cross-tenant access to raw bytes returns None (isolated)
    assert doc_service._load_raw_bytes(doc_resp.doc_id, tenant_id="tenant-unauthorized") is None

    # Missing tenant_id raises ValueError
    with pytest.raises(ValueError):
        doc_service._load_raw_bytes(doc_resp.doc_id, tenant_id="")


@pytest.mark.asyncio
async def test_document_deletion_and_store_cleanup(doc_service):
    """Verify cascading document deletion in SQLite, vector store, and cache."""
    payload = b"Temporary Document for Deletion Test"
    tenant_id = "tenant-del-test"

    doc_resp = await doc_service.ingest(
        file_bytes=payload,
        filename="temp_doc.pdf",
        content_type="application/pdf",
        tenant_id=tenant_id,
    )

    doc_id = doc_resp.doc_id
    assert str(doc_id) in doc_service._docs

    # Execute deletion
    success = await doc_service.delete(doc_id=str(doc_id), tenant_id=tenant_id)
    assert success is True
    assert str(doc_id) not in doc_service._docs

    # Subsequent queries must return None
    fetched = await doc_service.get(doc_id=str(doc_id), tenant_id=tenant_id)
    assert fetched is None

    # Underlying stores must have received deletion calls
    doc_service.orchestrator.vector_store.delete.assert_called_with(doc_id=str(doc_id))
    doc_service.orchestrator.semantic_cache.invalidate.assert_called_with(doc_id=str(doc_id))


@pytest.mark.asyncio
async def test_crash_recovery_stale_processing(temp_db, mock_orchestrator):
    """Verify that uncommitted 'processing' documents are transitioned to 'failed' on startup."""
    with sqlite3.connect(temp_db) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                status TEXT NOT NULL,
                page_count INTEGER NOT NULL,
                chunk_count INTEGER NOT NULL,
                is_scanned BOOLEAN NOT NULL,
                language TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                raw_bytes BLOB,
                content_type TEXT,
                byte_size INTEGER,
                sha256 TEXT,
                error_code TEXT,
                lifecycle_state TEXT
            )
        """)
        conn.execute("""
            INSERT INTO documents (doc_id, tenant_id, filename, status, page_count, chunk_count, is_scanned, language, created_at, lifecycle_state)
            VALUES ('stale-001', 'tenant-a', 'crashed.pdf', 'processing', 0, 0, 0, 'en', '2026-11-19T00:00:00Z', 'VALIDATING')
        """)
        conn.commit()

    # Re-instantiate service (simulating service restart)
    RealDocumentService(orchestrator=mock_orchestrator, db_path=temp_db)

    with sqlite3.connect(temp_db) as conn:
        row = conn.execute("SELECT status, error_code FROM documents WHERE doc_id = 'stale-001'").fetchone()
        assert row[0] == "failed"
        assert row[1] == "STALE_PROCESSING_INTERRUPTED"
