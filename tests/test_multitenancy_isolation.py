"""
Tests for cross-tenant query isolation and data separation.
Permanent regression tests for the tenant-isolation fixes in AMDIOrchestrator.
"""
from __future__ import annotations

import pytest

from src.core.orchestrator import AMDIOrchestrator
from src.models.document_object import DocumentFormat, DocumentObject


def make_document(
    tenant_id: str,
    filename: str = "doc.txt",
    content: str = "Confidential tenant content data payload.",
) -> DocumentObject:
    return DocumentObject(
        filename=filename,
        raw_bytes=content.encode("utf-8"),
        format=DocumentFormat.TEXT,
        tenant_id=tenant_id,
    )


@pytest.mark.asyncio
async def test_cross_tenant_query_isolation():
    """
    Regression test for the fix noted in orchestrator.py: a query must
    never return another tenant's document, whether or not a doc_id is
    supplied.
    """
    orch = AMDIOrchestrator()
    try:
        doc_a = await orch.ingest(
            make_document(tenant_id="tenant-a", filename="doc_a.txt", content="Tenant A quarterly earnings")
        )
        doc_b = await orch.ingest(
            make_document(tenant_id="tenant-b", filename="doc_b.txt", content="Tenant B secret merger info")
        )

        # No doc_id supplied — must not silently return the most-recent
        # document regardless of which tenant is asking.
        result = await orch.query("earnings query", tenant_id="tenant-a")
        assert result.doc_id != doc_b.doc_id

        # Explicit doc_id belonging to a different tenant must be rejected,
        # not silently honored.
        with pytest.raises(PermissionError):
            await orch.query("test query", tenant_id="tenant-a", doc_id=doc_b.doc_id)

        # Direct accessor calls for a different tenant's doc_id must also raise PermissionError
        with pytest.raises(PermissionError):
            orch.get_document_elements(doc_b.doc_id, tenant_id="tenant-a")

        with pytest.raises(PermissionError):
            orch.get_document_tables(doc_b.doc_id, tenant_id="tenant-a")

        with pytest.raises(PermissionError):
            orch.get_master_state(doc_b.doc_id, tenant_id="tenant-a")

        # Owner can access their own document state
        state_a = orch.get_master_state(doc_a.doc_id, tenant_id="tenant-a")
        assert state_a is not None
        assert state_a.doc_id == doc_a.doc_id
    finally:
        await orch.close()
