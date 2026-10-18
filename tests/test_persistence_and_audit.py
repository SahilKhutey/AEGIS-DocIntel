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
