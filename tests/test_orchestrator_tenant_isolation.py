"""
Tests for src.core.orchestrator.AMDIOrchestrator's document storage and
tenant-isolation behavior.

Repository Audit, Workstream R follow-up: prior to this fix,
AMDIOrchestrator.ingest() stored elements in flat instance attributes
(`self._elements = elements`, `self._tables = tables`) that were
*overwritten* wholesale on every single ingest() call. This had two
compounding, independently severe effects, both verified directly below by
constructing the failure conditions rather than only reading the code:

1. A correctness bug: ingesting a second document silently discarded the
   first document's elements application-wide, so only the most recently
   ingested document was ever queryable at all (test_second_ingest_does_
   not_evict_first_document below).

2. A data-confidentiality bug: nothing in the query path filtered by
   tenant, so a query with no doc_id searched whichever document happened
   to be most recent *regardless of which tenant ingested it*, and a query
   that supplied a doc_id belonging to a different tenant was honored with
   no ownership check at all (test_cross_tenant_doc_id_access_is_denied
   and test_tenant_scoped_query_does_not_leak_other_tenants_documents
   below). This is a direct, concrete instance of the tenant-isolation
   risk (R1) that the Feasibility and Validation Report's risk register
   flags as Critical priority.

Both are fixed by keying storage per-document (self._doc_elements,
self._doc_tables) and recording each document's owning tenant_id
(self._doc_tenant), enforced in query(), get_document_elements(), and
get_document_tables().
"""
from __future__ import annotations

import pytest

from src.core.document_object import DocumentObject, DocumentFormat
from src.core.orchestrator import AMDIOrchestrator


async def _ingest_text(orchestrator: AMDIOrchestrator, filename: str, text: str, tenant_id: str = "default") -> dict:
    doc = DocumentObject(
        filename=filename,
        raw_bytes=text.encode("utf-8"),
        format=DocumentFormat.TEXT,
        tenant_id=tenant_id,
    )
    return await orchestrator.ingest(doc)


@pytest.mark.asyncio
async def test_second_ingest_does_not_evict_first_document():
    """The original bug: self._elements = elements overwrote the entire
    application's store on every ingest(), so document A's elements were
    silently gone the moment document B was ingested. This test ingests
    two documents and confirms *both* remain independently retrievable —
    it must fail against the pre-fix flat-list implementation and pass
    against the per-document dict implementation."""
    orchestrator = AMDIOrchestrator()
    try:
        stats_a = await _ingest_text(
            orchestrator, "doc_a.txt", "Alpha document unique content marker AAAA."
        )
        stats_b = await _ingest_text(
            orchestrator, "doc_b.txt", "Beta document unique content marker BBBB."
        )
        doc_id_a, doc_id_b = stats_a["doc_id"], stats_b["doc_id"]
        assert doc_id_a != doc_id_b

        elements_a = orchestrator.get_document_elements(doc_id_a)
        elements_b = orchestrator.get_document_elements(doc_id_b)

        assert len(elements_a) > 0, (
            "Document A's elements were evicted by ingesting document B — "
            "this is the original bug this test exists to catch."
        )
        assert len(elements_b) > 0
        assert any("AAAA" in getattr(e, "content", "") for e in elements_a)
        assert any("BBBB" in getattr(e, "content", "") for e in elements_b)
        # And a query scoped to doc A must not be answerable from doc B's
        # content, confirming the two remain genuinely separate, not just
        # both non-empty.
        assert not any("BBBB" in getattr(e, "content", "") for e in elements_a)
    finally:
        await orchestrator.close()


@pytest.mark.asyncio
async def test_cross_tenant_doc_id_access_is_denied():
    """A query supplying a doc_id belonging to a different tenant must be
    refused, not silently honored — the core of the R1 tenant-isolation
    risk applied directly to this component."""
    orchestrator = AMDIOrchestrator()
    try:
        stats = await _ingest_text(
            orchestrator, "confidential.txt", "Tenant A's confidential figures.",
            tenant_id="tenant-a",
        )
        doc_id = stats["doc_id"]

        with pytest.raises(PermissionError):
            await orchestrator.query(
                "What are the figures?", doc_id=doc_id, tenant_id="tenant-b",
            )

        with pytest.raises(PermissionError):
            orchestrator.get_document_elements(doc_id, tenant_id="tenant-b")

        with pytest.raises(PermissionError):
            orchestrator.get_document_tables(doc_id, tenant_id="tenant-b")

        # The owning tenant, by contrast, must still be able to access it.
        elements = orchestrator.get_document_elements(doc_id, tenant_id="tenant-a")
        assert len(elements) > 0
    finally:
        await orchestrator.close()


@pytest.mark.asyncio
async def test_tenant_scoped_query_does_not_leak_other_tenants_documents():
    """A query with tenant_id set but no doc_id (a "search across my
    documents" query) must only ever search the calling tenant's own
    documents — not the whole application's document store, and not
    merely "whichever document was ingested most recently" regardless of
    owner."""
    orchestrator = AMDIOrchestrator()
    try:
        await _ingest_text(
            orchestrator, "a.txt", "Marker content ONLY_TENANT_A_SHOULD_SEE_THIS.",
            tenant_id="tenant-a",
        )
        await _ingest_text(
            orchestrator, "b.txt", "Marker content ONLY_TENANT_B_SHOULD_SEE_THIS.",
            tenant_id="tenant-b",
        )

        result = await orchestrator.query(
            "What markers are present?", tenant_id="tenant-a",
        )

        assert "ONLY_TENANT_B_SHOULD_SEE_THIS" not in result.get("answer", ""), (
            "Tenant A's unscoped query surfaced tenant B's document content — "
            "tenant isolation failure."
        )
    finally:
        await orchestrator.close()


@pytest.mark.asyncio
async def test_unscoped_query_backward_compatibility_preserved():
    """Callers that omit tenant_id entirely (pre-fix call signature) must
    continue to work exactly as before — this fix must not break existing
    single-tenant callers that have not yet been updated to pass
    tenant_id."""
    orchestrator = AMDIOrchestrator()
    try:
        stats = await _ingest_text(orchestrator, "solo.txt", "Solo document content.")
        doc_id = stats["doc_id"]
        result = await orchestrator.query("What is this about?", doc_id=doc_id)
        assert result is not None
        assert "answer" in result
    finally:
        await orchestrator.close()


@pytest.mark.asyncio
async def test_element_level_tenant_id_is_populated_not_dangling():
    """GeometricElement gained a tenant_id field as part of this fix. A
    field that is declared but never actually set by the only code path
    that constructs elements (_to_elements) is dead weight that looks like
    a defense-in-depth measure without being one — this test confirms it
    is genuinely wired through from the ingested document's own tenant_id,
    not left at its unpopulated default on every element."""
    orchestrator = AMDIOrchestrator()
    try:
        stats = await _ingest_text(
            orchestrator, "tagged.txt", "Content for element-level tenant tagging.",
            tenant_id="tenant-c",
        )
        elements = orchestrator.get_document_elements(stats["doc_id"], tenant_id="tenant-c")
        assert len(elements) > 0
        assert all(e.tenant_id == "tenant-c" for e in elements), (
            "GeometricElement.tenant_id was not populated during ingestion — "
            "it exists as a field but is dangling, not actually enforced."
        )
    finally:
        await orchestrator.close()
