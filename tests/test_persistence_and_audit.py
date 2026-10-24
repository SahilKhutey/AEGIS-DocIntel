"""
Tests for SQLite persistence in RealDocumentService and tamper-evident AuditLogger.
Validates:
- RealDocumentService survives service restart (documents loaded from SQLite)
- RealDocumentService deletion removes records from SQLite
- AuditLogger cryptographic SHA-256 hash chaining
- AuditLogger tamper detection via verify_integrity()
"""
import json
import os
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from src.observability.audit_logger import AuditLogger
from src.services.container import RealDocumentService


def test_audit_logger_chain_and_verification(tmp_path):
    log_file = tmp_path / "test_audit.log"
    logger = AuditLogger(log_path=log_file)

    # Log 5 entries
    e1 = logger.log(action="test.login", tenant_id="tenant-1", user_id="alice", status="SUCCESS")
    e2 = logger.log(action="test.read", tenant_id="tenant-1", user_id="alice", resource_id="doc-123")
    e3 = logger.log(action="test.update", tenant_id="tenant-2", user_id="bob", resource_id="doc-456")
    e4 = logger.log(action="test.delete", tenant_id="tenant-2", user_id="bob", resource_id="doc-456")
    e5 = logger.log(action="test.logout", tenant_id="tenant-1", user_id="alice")

    assert e1["prev_hash"] == "0000000000000000000000000000000000000000000000000000000000000000"
    assert e2["prev_hash"] == e1["entry_hash"]
    assert e3["prev_hash"] == e2["entry_hash"]
    assert e4["prev_hash"] == e3["entry_hash"]
    assert e5["prev_hash"] == e4["entry_hash"]

    is_valid, count, err = logger.verify_integrity()
    assert is_valid is True
    assert count == 5
    assert err is None


def test_audit_logger_tamper_detection(tmp_path):
    log_file = tmp_path / "tampered_audit.log"
    logger = AuditLogger(log_path=log_file)

    logger.log(action="test.event1", tenant_id="t1", user_id="u1")
    logger.log(action="test.event2", tenant_id="t1", user_id="u1")
    logger.log(action="test.event3", tenant_id="t1", user_id="u1")

    # Tamper with the second line's action
    lines = log_file.read_text(encoding="utf-8").splitlines()
    record2 = json.loads(lines[1])
    record2["action"] = "malicious.tamper"
    lines[1] = json.dumps(record2)
    log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Integrity verification must detect hash mismatch
    is_valid, count, err = logger.verify_integrity()
    assert is_valid is False
    assert "Hash mismatch at line 2" in err


@pytest.mark.asyncio
async def test_realdocumentservice_sqlite_persistence_and_restart(tmp_path):
    db_file = tmp_path / "documents.db"
    audit_file = tmp_path / "audit.log"

    # Setup orchestrator mock
    orchestrator = MagicMock()
    async def mock_ingest(doc_obj):
        return {
            "doc_id": doc_obj.doc_id,
            "filename": doc_obj.filename,
            "pages": 3,
            "elements": 12,
            "is_scanned": False,
            "language": "en",
        }
    orchestrator.ingest = mock_ingest

    # 1. Start instance 1 and ingest a document
    service1 = RealDocumentService(orchestrator, db_path=str(db_file))
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.services.container.audit_logger", AuditLogger(log_path=audit_file))
        res = await service1.ingest(
            file_bytes=b"%PDF-1.4 test document content",
            filename="quarterly_report.pdf",
            content_type="application/pdf",
            tenant_id="tenant-alpha",
        )

    doc_id = res.doc_id
    assert doc_id is not None

    # Check that doc exists in SQLite
    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.execute("SELECT doc_id, tenant_id, filename, page_count FROM documents WHERE doc_id = ?", (doc_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == doc_id
        assert row[1] == "tenant-alpha"
        assert row[2] == "quarterly_report.pdf"
        assert row[3] == 3

    # 2. Simulate service restart: instantiate fresh RealDocumentService instance 2 pointing to same db
    service2 = RealDocumentService(orchestrator, db_path=str(db_file))
    docs_list = await service2.list_documents("tenant-alpha")
    assert docs_list.total == 1
    loaded_doc = docs_list.items[0]
    assert loaded_doc.doc_id == doc_id
    assert loaded_doc.filename == "quarterly_report.pdf"
    assert loaded_doc.page_count == 3

    # Other tenant cannot see it
    other_list = await service2.list_documents("tenant-beta")
    assert other_list.total == 0

    # 3. Delete document and verify it is removed from SQLite
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.services.container.audit_logger", AuditLogger(log_path=audit_file))
        del_ok = await service2.delete(doc_id, "tenant-alpha")
        assert del_ok is True

    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
        assert cursor.fetchone() is None

    # Verify audit log recorded ingest and delete
    logger = AuditLogger(log_path=audit_file)
    is_valid, count, err = logger.verify_integrity()
    assert is_valid is True
    assert count >= 2


@pytest.mark.asyncio
async def test_realdocumentservice_document_hydration_after_restart(tmp_path):
    db_file = tmp_path / "documents.db"

    # Orchestrator with memory doc_state
    orchestrator = MagicMock()
    orchestrator._doc_state = {}

    async def mock_ingest(doc_obj):
        orchestrator._doc_state[doc_obj.doc_id] = {
            "doc_id": doc_obj.doc_id,
            "filename": doc_obj.filename,
            "raw_bytes": doc_obj.raw_bytes,
        }
        return {
            "doc_id": doc_obj.doc_id,
            "filename": doc_obj.filename,
            "pages": 1,
            "elements": 5,
        }
    orchestrator.ingest = mock_ingest

    # 1. Ingest via service 1
    service1 = RealDocumentService(orchestrator, db_path=str(db_file))
    res = await service1.ingest(
        file_bytes=b"sample doc content bytes",
        filename="hydrated_test.pdf",
        content_type="application/pdf",
        tenant_id="tenant-hydrate",
    )
    doc_id = res.doc_id
    assert doc_id in orchestrator._doc_state

    # 2. Simulate complete memory wipe / server restart with empty orchestrator
    fresh_orchestrator = MagicMock()
    fresh_orchestrator._doc_state = {}
    ingest_called_with = []
    async def fresh_mock_ingest(doc_obj):
        ingest_called_with.append(doc_obj)
        fresh_orchestrator._doc_state[doc_obj.doc_id] = {"doc_id": doc_obj.doc_id}
        return {"doc_id": doc_obj.doc_id, "pages": 1, "elements": 5}
    fresh_orchestrator.ingest = fresh_mock_ingest

    service2 = RealDocumentService(fresh_orchestrator, db_path=str(db_file))
    assert doc_id not in fresh_orchestrator._doc_state

    # 3. Hydrate document into orchestrator
    hydrated = await service2.hydrate_document(doc_id, "tenant-hydrate")
    assert hydrated is True
    assert doc_id in fresh_orchestrator._doc_state
    assert len(ingest_called_with) == 1
    assert ingest_called_with[0].raw_bytes == b"sample doc content bytes"

    # 4. Attempt hydration from wrong tenant should fail
    wrong_tenant = await service2.hydrate_document(doc_id, "wrong-tenant")
    assert wrong_tenant is False



@pytest.mark.asyncio
async def test_realdocumentservice_pagination_and_status_filter(tmp_path):
    db_file = tmp_path / "pagination_test.db"
    audit_file = tmp_path / "pagination_audit.log"
    orchestrator = MagicMock()
    async def mock_ingest(doc_obj):
        return {
            "doc_id": doc_obj.doc_id,
            "filename": doc_obj.filename,
            "pages": 1,
            "elements": 2,
        }
    orchestrator.ingest = mock_ingest

    service = RealDocumentService(orchestrator, db_path=str(db_file))
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.services.container.audit_logger", AuditLogger(log_path=audit_file))
        # Ingest 5 documents for tenant-page
        for i in range(5):
            await service.ingest(
                file_bytes=f"content_{i}".encode(),
                filename=f"doc_{i}.txt",
                content_type="text/plain",
                tenant_id="tenant-page",
            )
        # Manually set 2 to status 'archived' for filtering test
        keys = list(service._docs.keys())
        service._docs[keys[3]]["status"] = "archived"
        service._docs[keys[4]]["status"] = "archived"
        with sqlite3.connect(str(db_file)) as conn:
            conn.execute("UPDATE documents SET status = 'archived' WHERE doc_id IN (?, ?)", (keys[3], keys[4]))
            conn.commit()

    # Test page 1, page_size 2
    p1 = await service.list_documents("tenant-page", page=1, page_size=2)
    assert p1.total == 5
    assert len(p1.items) == 2
    assert p1.page == 1

    # Test page 2, page_size 2
    p2 = await service.list_documents("tenant-page", page=2, page_size=2)
    assert p2.total == 5
    assert len(p2.items) == 2
    assert p2.page == 2
    assert p1.items[0].doc_id != p2.items[0].doc_id

    # Test page 3, page_size 2 (last page, 1 item)
    p3 = await service.list_documents("tenant-page", page=3, page_size=2)
    assert p3.total == 5
    assert len(p3.items) == 1

    # Test status filter: 'ready' (3 docs)
    ready_list = await service.list_documents("tenant-page", status="ready")
    assert ready_list.total == 3
    assert len(ready_list.items) == 3
    for it in ready_list.items:
        assert it.status == "ready"

    # Test status filter: 'archived' (2 docs)
    arch_list = await service.list_documents("tenant-page", status="archived")
    assert arch_list.total == 2
    assert len(arch_list.items) == 2

    # Test invalid page
    with pytest.raises(ValueError, match="page must be >= 1"):
        await service.list_documents("tenant-page", page=0)

    # Test invalid page_size
    with pytest.raises(ValueError, match="page_size must be between 1 and 100"):
        await service.list_documents("tenant-page", page_size=0)


@pytest.mark.asyncio
async def test_realdocumentservice_persistence_failure_propagates_and_cleans_up(tmp_path):
    from src.services.container import DocumentPersistenceError

    db_file = tmp_path / "fail_test.db"
    orchestrator = MagicMock()
    async def mock_ingest(doc_obj):
        return {
            "doc_id": doc_obj.doc_id,
            "filename": doc_obj.filename,
            "pages": 1,
            "elements": 2,
        }
    orchestrator.ingest = mock_ingest

    service = RealDocumentService(orchestrator, db_path=str(db_file))
    
    # Force _persist_doc to fail
    def failing_persist(doc_info, raw_bytes=None):
        raise DocumentPersistenceError("Simulated disk full")

    service._persist_doc = failing_persist

    with pytest.raises(DocumentPersistenceError):
        await service.ingest(
            file_bytes=b"sample",
            filename="fail.txt",
            content_type="text/plain",
            tenant_id="tenant-fail",
        )

    # Ensure document was removed from in-memory cache to prevent phantom successful state
    assert len(service._docs) == 0


# =====================================================================
# P1 Specification: Failure-Injection, Recovery & Lifecycle Tests
# =====================================================================

@pytest.mark.asyncio
async def test_database_initialization_failure_fails_startup(tmp_path, monkeypatch):
    """P1.1: Database initialization failures must fail startup closed with DocumentStorageError."""
    from src.services.storage_errors import DocumentStorageError

    orchestrator = MagicMock()
    # Point db_path to an uncreatable location or simulate sqlite connect error
    db_file = tmp_path / "subfolder_does_not_exist" / "documents.db"

    def broken_connect(*args, **kwargs):
        raise sqlite3.OperationalError("Unable to open database file")

    monkeypatch.setattr(sqlite3, "connect", broken_connect)

    with pytest.raises(DocumentStorageError, match="Database initialization failed"):
        RealDocumentService(orchestrator, db_path=str(db_file))


@pytest.mark.asyncio
async def test_source_checksum_verified_during_hydration(tmp_path):
    """P1.2: SHA-256 byte checksum must be verified during raw-byte rehydration."""
    from src.services.storage_errors import DocumentRecoveryError

    db_file = tmp_path / "checksum_test.db"
    orchestrator = MagicMock()
    orchestrator._doc_state = {}
    async def mock_ingest(d):
        return {"pages": 1, "elements": 1}
    orchestrator.ingest = mock_ingest

    service = RealDocumentService(orchestrator, db_path=str(db_file))
    res = await service.ingest(
        file_bytes=b"authentic uncorrupted content",
        filename="integrity.pdf",
        content_type="application/pdf",
        tenant_id="tenant-security",
    )
    doc_id = res.doc_id

    # Tamper with the raw_bytes in SQLite
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute(
            "UPDATE documents SET raw_bytes = ? WHERE doc_id = ?",
            (b"corrupted or tampered content", doc_id),
        )
        conn.commit()

    # Hydration / raw byte load must detect checksum mismatch
    with pytest.raises(DocumentRecoveryError, match=f"Checksum mismatch for document {doc_id}"):
        service._load_raw_bytes(doc_id, tenant_id="tenant-security")


@pytest.mark.asyncio
async def test_stale_processing_document_reconciled_after_restart(tmp_path):
    """P1.2: Stale 'processing' or 'deleting' documents interrupted by server death are reconciled on startup."""
    db_file = tmp_path / "recovery_test.db"
    orchestrator = MagicMock()

    # 1. Initialize DB and seed interrupted records
    s1 = RealDocumentService(orchestrator, db_path=str(db_file))
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("""
            INSERT INTO documents (doc_id, tenant_id, filename, status, page_count, chunk_count, is_scanned, language, created_at, error_code)
            VALUES 
            ('doc-stale-proc', 'tenant-rec', 'crash_in_flight.pdf', 'processing', 0, 0, 0, 'en', '2026-01-01T00:00:00', NULL),
            ('doc-stale-del', 'tenant-rec', 'crash_during_del.pdf', 'deleting', 2, 5, 0, 'en', '2026-01-01T00:00:00', NULL)
        """)
        conn.commit()

    # 2. Restart service (calls _load_docs which runs recovery reconciliation)
    s2 = RealDocumentService(orchestrator, db_path=str(db_file))

    with sqlite3.connect(str(db_file)) as conn:
        r1 = conn.execute("SELECT status, error_code FROM documents WHERE doc_id = 'doc-stale-proc'").fetchone()
        assert r1[0] == "failed"
        assert r1[1] == "STALE_PROCESSING_INTERRUPTED"

        r2 = conn.execute("SELECT status, error_code FROM documents WHERE doc_id = 'doc-stale-del'").fetchone()
        assert r2[0] == "delete_failed"
        assert r2[1] == "STALE_DELETION_INTERRUPTED"


@pytest.mark.asyncio
async def test_raw_bytes_lookup_is_tenant_scoped(tmp_path):
    """P1.3: Raw bytes lookup must be strictly tenant-scoped."""
    db_file = tmp_path / "tenant_raw_bytes.db"
    orchestrator = MagicMock()
    async def mock_ingest(d):
        return {"pages": 1, "elements": 1}
    orchestrator.ingest = mock_ingest
    service = RealDocumentService(orchestrator, db_path=str(db_file))

    res = await service.ingest(
        file_bytes=b"confidential company payroll data",
        filename="payroll.pdf",
        content_type="application/pdf",
        tenant_id="tenant-owner",
    )
    doc_id = res.doc_id

    # Owner tenant can load raw bytes
    owner_bytes = service._load_raw_bytes(doc_id, tenant_id="tenant-owner")
    assert owner_bytes == b"confidential company payroll data"

    # Attacking/foreign tenant gets None
    attacker_bytes = service._load_raw_bytes(doc_id, tenant_id="tenant-attacker")
    assert attacker_bytes is None


@pytest.mark.asyncio
async def test_database_migration_preserves_records(tmp_path):
    """P1.1: Schema migration from v1 to v2 adds columns and preserves existing document data."""
    db_file = tmp_path / "legacy_v1.db"

    # 1. Create a schema v1 database
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("""
            CREATE TABLE documents (
                doc_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                status TEXT NOT NULL,
                page_count INTEGER NOT NULL,
                chunk_count INTEGER NOT NULL,
                is_scanned BOOLEAN NOT NULL,
                language TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("PRAGMA user_version = 1")
        conn.execute("""
            INSERT INTO documents VALUES (
                'doc-legacy-1', 'tenant-leg', 'legacy_report.txt', 'ready', 5, 20, 0, 'en', '2026-01-01T12:00:00'
            )
        """)
        conn.commit()

    # 2. Boot RealDocumentService on legacy DB
    orchestrator = MagicMock()
    async def mock_ingest(d):
        return {"pages": 1, "elements": 1}
    orchestrator.ingest = mock_ingest
    service = RealDocumentService(orchestrator, db_path=str(db_file))

    # 3. Verify user_version is now 2
    with sqlite3.connect(str(db_file)) as conn:
        v = conn.execute("PRAGMA user_version").fetchone()[0]
        assert v == 2

        # Verify new columns exist
        cols = {r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()}
        assert "byte_size" in cols
        assert "sha256" in cols
        assert "error_code" in cols
        assert "raw_bytes" in cols

    # 4. Verify existing legacy document was preserved and is readable
    doc_list = await service.list_documents("tenant-leg")
    assert doc_list.total == 1
    assert doc_list.items[0].doc_id == "doc-legacy-1"
    assert doc_list.items[0].filename == "legacy_report.txt"


@pytest.mark.asyncio
async def test_delete_partial_failure_is_retryable(tmp_path):
    """P1.4: Partial downstream store failures mark status as delete_failed and are safely retryable."""
    from unittest.mock import AsyncMock

    db_file = tmp_path / "retry_deletion.db"
    orchestrator = MagicMock()
    async def mock_ingest(d):
        return {"pages": 1, "elements": 1}
    orchestrator.ingest = mock_ingest
    
    mock_vector = AsyncMock()
    # First attempt: vector store raises error
    mock_vector.delete.side_effect = ConnectionResetError("Vector DB transient network blip")
    orchestrator.vector_store = mock_vector
    orchestrator.semantic_cache = None

    service = RealDocumentService(orchestrator, db_path=str(db_file))
    res = await service.ingest(
        file_bytes=b"retryable document content",
        filename="resilience.txt",
        content_type="text/plain",
        tenant_id="tenant-retry",
    )
    doc_id = res.doc_id

    # Deletion attempt 1: store fails -> delete returns False, marked delete_failed
    del1 = await service.delete(doc_id, "tenant-retry")
    assert del1 is False

    with sqlite3.connect(str(db_file)) as conn:
        row = conn.execute("SELECT status, error_code FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()
        assert row is not None
        assert row[0] == "delete_failed"
        assert "Vector DB transient network blip" in row[1]

    # Deletion attempt 2: vector store recovers
    mock_vector.delete.side_effect = None
    mock_vector.delete.return_value = None

    del2 = await service.delete(doc_id, "tenant-retry")
    assert del2 is True

    # Record must now be completely removed from SQLite
    with sqlite3.connect(str(db_file)) as conn:
        row = conn.execute("SELECT 1 FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()
        assert row is None
