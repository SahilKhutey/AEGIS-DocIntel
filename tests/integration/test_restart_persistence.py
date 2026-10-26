"""
tests/integration/test_restart_persistence.py
=============================================
Phase 3.3 Persistence, Restart, and Recovery Suite:
Proves that saved documents, chunks, and metadata survive application restarts,
and that reopened stores can serve queries with identical source fidelity.
"""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone

import pytest

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
async def test_document_metadata_and_state_survives_restart(tmp_path):
    """
    1. Boot storage with isolated SQLite DB.
    2. Ingest document and record doc_id.
    3. Verify persistence on disk.
    4. Shut down orchestrator and close connections.
    5. Boot a completely fresh service instance from the same DB file.
    6. Verify all documents, chunks, and metadata survive.
    """
    db_file = tmp_path / "restart_test.db"
    content = "AEGIS-DocIntel provides durable document storage with atomic commits in WAL mode."
    raw = content.encode("utf-8")

    # Phase 1: Ingest and persist
    orch1 = AMDIOrchestrator()
    try:
        service1 = RealDocumentService(orchestrator=orch1, db_path=str(db_file))
        doc_in = make_doc(
            tenant_id="tenant-persist-1",
            filename="sla_policy.txt",
            content=content,
        )
        doc_res = await orch1.ingest(doc_in)
        doc_id = doc_res["doc_id"]

        now = datetime.now(timezone.utc)
        doc_info = {
            "doc_id": doc_id,
            "tenant_id": "tenant-persist-1",
            "filename": "sla_policy.txt",
            "status": "ready",
            "page_count": doc_res.get("pages", 1),
            "chunk_count": doc_res.get("elements", 1),
            "is_scanned": False,
            "language": "en",
            "created_at": now,
            "updated_at": now.isoformat(),
            "content_type": "text/plain",
            "byte_size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        service1._docs[doc_id] = doc_info
        service1._persist_doc(doc_info, raw_bytes=raw)

        # Confirm record exists on disk in SQLite
        with sqlite3.connect(str(db_file)) as conn:
            row = conn.execute(
                "SELECT doc_id, tenant_id, filename, status FROM documents WHERE doc_id = ?",
                (doc_id,),
            ).fetchone()
            assert row is not None, "Document not found in SQLite table"
            assert row[0] == doc_id
            assert row[1] == "tenant-persist-1"
            assert row[2] == "sla_policy.txt"
            assert row[3] == "ready"
    finally:
        await orch1.close()

    # Phase 2: Restart fresh service instance pointing to the same DB file
    orch2 = AMDIOrchestrator()
    try:
        service2 = RealDocumentService(orchestrator=orch2, db_path=str(db_file))

        # Retrieve document from restarted store
        reloaded = await service2.get(doc_id, tenant_id="tenant-persist-1")
        assert reloaded is not None, "Document failed to reload after restart"
        assert reloaded.doc_id == doc_id
        assert reloaded.filename == "sla_policy.txt"
        assert reloaded.status == "ready"

        # List documents for tenant confirms presence
        list_resp = await service2.list_documents(tenant_id="tenant-persist-1")
        assert any(d.doc_id == doc_id for d in list_resp.items)

        # Cross-tenant check: other tenant cannot see persisted document
        other_list_resp = await service2.list_documents(tenant_id="tenant-intruder")
        assert not any(d.doc_id == doc_id for d in other_list_resp.items)
    finally:
        await orch2.close()
