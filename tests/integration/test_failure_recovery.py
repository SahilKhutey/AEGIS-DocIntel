"""
tests/integration/test_failure_recovery.py
==========================================
Phase 3.3 Persistence, Restart, and Recovery Suite:
- Idempotency key handling and duplicate request detection.
- Interrupted or malformed upload cleanup (no orphan state).
- Database lock and storage failure handling without silent corruption.
"""
from __future__ import annotations

import io
import sqlite3
import pytest
from fastapi.testclient import TestClient

from src.core.resilience import (
    IdempotencyConflictError,
    IdempotencyInProgressError,
    IdempotencyStore,
)
from src.main import create_app
from src.services.container import RealDocumentService
from src.services.storage_errors import DocumentStorageError


@pytest.mark.asyncio
async def test_idempotency_store_duplicate_and_in_progress_detection():
    """Verify idempotency store rejects concurrent duplicates and returns completed records."""
    store = IdempotencyStore(ttl_seconds=60.0)
    key = "idem-req-uuid-12345"
    payload = b'{"filename": "contract.pdf"}'
    payload_hash = store.compute_payload_hash(payload)

    # 1. Start request: initial check returns None (request registered as in_progress)
    initial = await store.check_and_start(
        tenant_id="tenant-alpha",
        operation="documents.upload",
        key=key,
        payload_hash=payload_hash,
    )
    assert initial is None

    # 2. In-progress concurrent duplicate must raise IdempotencyInProgressError
    with pytest.raises(IdempotencyInProgressError):
        await store.check_and_start(
            tenant_id="tenant-alpha",
            operation="documents.upload",
            key=key,
            payload_hash=payload_hash,
        )

    # 3. Complete request with response body
    response_body = {"status": "completed", "doc_id": "doc-5555"}
    await store.complete(
        tenant_id="tenant-alpha",
        operation="documents.upload",
        key=key,
        response_code=200,
        response_body=response_body,
    )

    # 4. Subsequent identical request returns existing completed record
    cached_record = await store.check_and_start(
        tenant_id="tenant-alpha",
        operation="documents.upload",
        key=key,
        payload_hash=payload_hash,
    )
    assert cached_record is not None
    assert cached_record.status == "completed"
    assert cached_record.response_body == response_body

    # 5. Same key with different payload raises IdempotencyConflictError
    diff_hash = store.compute_payload_hash(b'{"different": "payload"}')
    with pytest.raises(IdempotencyConflictError):
        await store.check_and_start(
            tenant_id="tenant-alpha",
            operation="documents.upload",
            key=key,
            payload_hash=diff_hash,
        )


def test_malformed_upload_leaves_no_orphan_records(tmp_path, monkeypatch):
    """Verify that uploading an invalid file leaves no orphan records in SQLite."""
    db_file = tmp_path / "orphan_test.db"
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    monkeypatch.setenv("AEGIS_SQLITE_PATH", str(db_file))

    app = create_app()
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer dev-tenant-alpha"}
        # Uploading an empty file or unsupported format
        files = {"file": ("corrupt.bin", io.BytesIO(b""), "application/octet-stream")}

        res = client.post("/v1/documents/upload", headers=headers, files=files)
        # Should be rejected with 400 or 415 or 422
        assert res.status_code in (400, 415, 422)

        # Check database table has 0 records
        if db_file.exists():
            with sqlite3.connect(str(db_file)) as conn:
                count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
                assert count == 0, f"Found {count} orphan records after failed upload"


def test_database_initialization_failure_raises_storage_error(tmp_path):
    """Verify that an invalid or unwritable SQLite directory raises DocumentStorageError."""
    # Using a path where a file exists instead of a directory to force failure
    invalid_file = tmp_path / "not_a_dir"
    invalid_file.write_text("blocker")
    unwritable_path = invalid_file / "subfolder" / "documents.db"

    from src.core.orchestrator import AMDIOrchestrator
    orch = AMDIOrchestrator()
    try:
        with pytest.raises(DocumentStorageError):
            RealDocumentService(orchestrator=orch, db_path=str(unwritable_path))
    finally:
        pass
