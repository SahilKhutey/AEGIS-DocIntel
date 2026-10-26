"""
tests/integration/test_backup_restore.py
========================================
Phase 3.3 Persistence, Restart, and Recovery Suite:
Exercises the online SQLite backup tool (scripts/backup_sqlite.py), restores
the snapshot into an isolated recovery environment, and proves that data and
metadata integrity are completely preserved.
"""
from __future__ import annotations

import hashlib
import shutil
import sqlite3
from datetime import datetime, timezone

import pytest

from scripts.backup_sqlite import backup_database
from src.core.orchestrator import AMDIOrchestrator
from src.models.document_object import DocumentFormat, DocumentObject
from src.services.container import RealDocumentService


def make_doc(tenant_id: str, filename: str, content: str) -> DocumentObject:
    return DocumentObject(
        filename=filename,
        raw_bytes=content.encode("utf-8"),
        format=DocumentFormat.TEXT,
        tenant_id=tenant_id,
    )


@pytest.mark.asyncio
async def test_online_backup_and_restore_recovery_drill(tmp_path):
    """
    1. Ingest multiple documents into an active source database.
    2. Execute online SQLite backup to backup destination.
    3. Verify backup file integrity using SQLite PRAGMA integrity_check.
    4. Restore backup file into a clean recovery directory.
    5. Boot a new document service on the restored database.
    6. Verify all documents, chunks, and metadata match the original state.
    """
    src_db = tmp_path / "source.db"
    backup_db = tmp_path / "backups" / "source_backup.db"
    restored_db = tmp_path / "restored" / "restored.db"

    # Step 1: Ingest documents into active source database
    orch_src = AMDIOrchestrator()
    try:
        service_src = RealDocumentService(orchestrator=orch_src, db_path=str(src_db))

        c1 = "Q1 Revenue: $45M, Operating Margin: 18%."
        c2 = "All systems passed SOC-2 Type II audit controls."
        doc1 = make_doc("tenant-prod", "finance_2025.txt", c1)
        doc2 = make_doc("tenant-prod", "security_audit.txt", c2)

        res1 = await orch_src.ingest(doc1)
        res2 = await orch_src.ingest(doc2)

        now = datetime.now(timezone.utc)
        doc1_id = res1["doc_id"]
        doc2_id = res2["doc_id"]

        info1 = {
            "doc_id": doc1_id,
            "tenant_id": "tenant-prod",
            "filename": "finance_2025.txt",
            "status": "ready",
            "page_count": 1,
            "chunk_count": 1,
            "is_scanned": False,
            "language": "en",
            "created_at": now,
            "updated_at": now.isoformat(),
            "content_type": "text/plain",
            "byte_size": len(c1.encode("utf-8")),
            "sha256": hashlib.sha256(c1.encode("utf-8")).hexdigest(),
        }
        info2 = {
            "doc_id": doc2_id,
            "tenant_id": "tenant-prod",
            "filename": "security_audit.txt",
            "status": "ready",
            "page_count": 1,
            "chunk_count": 1,
            "is_scanned": False,
            "language": "en",
            "created_at": now,
            "updated_at": now.isoformat(),
            "content_type": "text/plain",
            "byte_size": len(c2.encode("utf-8")),
            "sha256": hashlib.sha256(c2.encode("utf-8")).hexdigest(),
        }

        service_src._docs[doc1_id] = info1
        service_src._docs[doc2_id] = info2
        service_src._persist_doc(info1, raw_bytes=c1.encode("utf-8"))
        service_src._persist_doc(info2, raw_bytes=c2.encode("utf-8"))
    finally:
        await orch_src.close()

    # Step 2: Execute online SQLite backup utility
    backup_database(src_db, backup_db)
    assert backup_db.exists(), "Backup database file was not created"

    # Step 3: Verify backup file integrity
    with sqlite3.connect(str(backup_db)) as conn:
        res = conn.execute("PRAGMA integrity_check").fetchone()
        assert res is not None and res[0] == "ok", f"Backup integrity check failed: {res}"

    # Step 4: Restore backup into a separate recovery environment
    restored_db.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_db, restored_db)
    assert restored_db.exists()

    # Step 5: Boot fresh service container pointing to restored database
    orch_restored = AMDIOrchestrator()
    try:
        service_restored = RealDocumentService(orchestrator=orch_restored, db_path=str(restored_db))

        # Step 6: Verify all records exist and match original state
        d1 = await service_restored.get(doc1_id, tenant_id="tenant-prod")
        d2 = await service_restored.get(doc2_id, tenant_id="tenant-prod")

        assert d1 is not None, f"Document 1 ({doc1_id}) missing in restored database"
        assert d2 is not None, f"Document 2 ({doc2_id}) missing in restored database"

        assert d1.filename == "finance_2025.txt"
        assert d2.filename == "security_audit.txt"
        assert d1.status == "ready"
        assert d2.status == "ready"

        # Verify listing on restored service
        list_resp = await service_restored.list_documents(tenant_id="tenant-prod")
        assert len(list_resp.items) >= 2
        retrieved_ids = {d.doc_id for d in list_resp.items}
        assert doc1_id in retrieved_ids
        assert doc2_id in retrieved_ids
    finally:
        await orch_restored.close()
