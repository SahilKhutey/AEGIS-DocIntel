"""tests/test_mvp2_index_lifecycle.py
==================================
MVP 2 tests for index lifecycle:
1. Ingestion -> searchable
2. Exact phrase retrieval
3. Document restriction filter
4. Update / reindex -> no stale chunk content returned
5. Deletion -> immediate exclusion from retrieval
6. Failed / empty input safety
7. Evidence provenance and citation mapping
8. Multi-tenant isolation across overlapping phrases
"""

from __future__ import annotations

import pytest

from src.core.orchestrator import AMDIOrchestrator
from src.models.document_object import DocumentObject, DocumentFormat
from src.models.evidence_object import validate_citations, RetrievedEvidence


@pytest.mark.asyncio
async def test_index_lifecycle_ingest_search_update_delete() -> None:
    """End-to-end index lifecycle: ingest -> search -> update -> delete."""
    orchestrator = AMDIOrchestrator(config={"embedding_dim": 64})
    try:
        # 1. Ingest document v1 (with at least 2 elements for multi-modal analysis)
        doc_v1 = DocumentObject(
            doc_id="doc-life-001",
            filename="financials_v1.txt",
            raw_bytes=b"Quarterly consolidated EBITDA reached 42 million USD.\n\nExecutive financial overview summary.",
            format=DocumentFormat.TEXT,
            tenant_id="tenant-acme",
        )
        ingest_res = await orchestrator.ingest(doc_v1)
        assert ingest_res.get("doc_id") == "doc-life-001"
        assert "doc-life-001" in orchestrator._doc_state

        # 2. Search exact phrase
        query_res = await orchestrator.query(
            question="What was EBITDA?",
            tenant_id="tenant-acme",
        )
        assert query_res["grounded"] is True
        assert "42 million" in str(query_res.get("answer", "")) or "EBITDA" in str(query_res.get("citations", ""))

        # 3. Document filter scoping
        filtered_res = await orchestrator.query(
            question="What was EBITDA?",
            doc_id="doc-life-001",
            tenant_id="tenant-acme",
        )
        assert filtered_res["grounded"] is True

        # Restricting to a foreign document owned by another tenant raises PermissionError
        with pytest.raises(PermissionError):
            await orchestrator.query(
                question="What was EBITDA?",
                doc_id="doc-life-001",
                tenant_id="tenant-other",
            )

        # 4. Update: Re-ingest with updated content
        doc_v2 = DocumentObject(
            doc_id="doc-life-001",
            filename="financials_v2.txt",
            raw_bytes=b"Revised EBITDA was corrected to 55 million USD.\n\nExecutive financial overview summary.",
            format=DocumentFormat.TEXT,
            tenant_id="tenant-acme",
        )
        update_res = await orchestrator.ingest(doc_v2)
        assert update_res.get("doc_id") == "doc-life-001"

        # Stale content ("42 million") should no longer be present in active document elements
        elements = orchestrator.get_document_elements("doc-life-001", tenant_id="tenant-acme")
        all_text = " ".join(e.content for e in elements)
        assert "55 million" in all_text
        assert "42 million" not in all_text

        # 5. Delete document
        deleted = await orchestrator.delete_document("doc-life-001", tenant_id="tenant-acme")
        assert deleted is True
        assert "doc-life-001" not in orchestrator._doc_state

        # Query after deletion should abstain gracefully
        post_del_res = await orchestrator.query(
            question="What was EBITDA?",
            tenant_id="tenant-acme",
        )
        assert post_del_res["grounded"] is False
        assert "do not have sufficient evidence" in str(post_del_res.get("answer", ""))
    finally:
        await orchestrator.close()


@pytest.mark.asyncio
async def test_multi_tenant_isolation_with_overlapping_content() -> None:
    """Ingest identical keywords for two tenants; verify complete isolation."""
    orchestrator = AMDIOrchestrator(config={"embedding_dim": 64})
    try:
        # Tenant 1: Project Apollo
        doc_t1 = DocumentObject(
            doc_id="doc-apollo",
            filename="apollo.txt",
            raw_bytes=b"Project code APOLLO budget is 100000 dollars.\n\nProject schedule and milestones.",
            format=DocumentFormat.TEXT,
            tenant_id="tenant-1",
        )
        await orchestrator.ingest(doc_t1)

        # Tenant 2: Project Apollo (overlapping keyword, different secret budget)
        doc_t2 = DocumentObject(
            doc_id="doc-apollo-t2",
            filename="apollo_t2.txt",
            raw_bytes=b"Project code APOLLO confidential budget is 999999 euros.\n\nProject schedule and milestones.",
            format=DocumentFormat.TEXT,
            tenant_id="tenant-2",
        )
        await orchestrator.ingest(doc_t2)

        # Query from Tenant 1
        res_t1 = await orchestrator.query("What is the budget for APOLLO?", tenant_id="tenant-1")
        res_t1_str = str(res_t1.get("answer", "")) + str(res_t1.get("citations", ""))
        assert "999999" not in res_t1_str
        assert "euros" not in res_t1_str

        # Query from Tenant 2
        res_t2 = await orchestrator.query("What is the budget for APOLLO?", tenant_id="tenant-2")
        res_t2_str = str(res_t2.get("answer", "")) + str(res_t2.get("citations", ""))
        assert "100000 dollars" not in res_t2_str
    finally:
        await orchestrator.close()


@pytest.mark.asyncio
async def test_citation_integrity_against_assembled_evidence() -> None:
    """Verify citations mapped to real retrieved evidence validate cleanly."""
    evidence = [
        RetrievedEvidence(
            document_id="doc-10",
            chunk_id="chunk-10-1",
            text="Operating expenses decreased by 5 percent.",
            page_number=3,
            section_path=("Financial Statements", "Operating Expenses"),
            retrieval_score=0.94,
            tenant_id="tenant-corp",
        ),
    ]

    valid_cit = [{"doc_id": "doc-10", "chunk_id": "chunk-10-1"}]
    res = validate_citations(valid_cit, evidence, tenant_id="tenant-corp")
    assert res.is_valid is True
    assert res.total_citations == 1
    assert res.valid_citations == 1

    # Cross-tenant citation rejection
    cross_tenant_res = validate_citations(valid_cit, evidence, tenant_id="tenant-rogue")
    assert cross_tenant_res.is_valid is False
    assert "unauthorized" in cross_tenant_res.invalid_citations[0]["reason"]
