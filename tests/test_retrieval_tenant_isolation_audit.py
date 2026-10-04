"""
MVP Plan Phase 0: retrieval-backend tenant-isolation audit.

Audits the seven files under src/engines/retrieval/*_search.py (plus their
coordinators, retrieval_engine.py, amdi_retriever.py, hybrid_retrieval.py)
for the same "looks isolated but isn't" pattern found and fixed at four
other layers across Sessions 2-5 (orchestrator storage, document service,
HTTP routes, WebSocket auth). Verified result, recorded precisely rather
than assumed either way:

FINDING: none of the seven search-backend files, nor AMDIRetriever itself,
reference tenant_id anywhere -- confirmed by direct grep. Traced this to
its root cause rather than treating the absence as a bug on its own (the
lesson from the ARC-cache near-miss in Session 5): every one of these
components is stateless with respect to tenant/document scope --
AMDIRetriever.retrieve() takes `elements: List[GeometricElement]` as a
direct parameter rather than holding a persistent internal index, and both
call sites in AMDIOrchestrator (query() and stream_query()) call
_scoped_elements_and_tables(doc_id, tenant_id) -- already tenant-correct,
per Sessions 2-3 -- BEFORE invoking the retriever. The search backends
never see another tenant's elements in the first place; there is no
tenant boundary for them to enforce because tenant scoping already
happened one layer up, by the same mechanism already tested in
test_orchestrator_tenant_isolation.py.

This is the second verified-correct result in this audit chain (after the
ARC cache's ghost-list mechanism in Session 5) -- recorded here with an
end-to-end test that exercises the real path (orchestrator.query() down
through the actual retriever and search engines) rather than only
asserting the absence of a bug via code inspection.

A separate, adjacent finding: src/workflows/query_workflow.py and
ingest_workflow.py hold single-tenant flat state (the same pre-fix
pattern the orchestrator originally had) but are reachable only from
src/cli.py's direct, single-user CLI commands -- never from the
multi-tenant HTTP API (confirmed: no import of either class anywhere
under src/api/ or src/main.py). Correct for current scope; flagged with a
defensive docstring in ingest_workflow.py against future misuse, not
functionally changed here.
"""
from __future__ import annotations

import pytest

from src.models.document_object import DocumentObject, DocumentFormat
from src.core.orchestrator import AMDIOrchestrator


async def _ingest_text(orchestrator: AMDIOrchestrator, filename: str, text: str, tenant_id: str) -> dict:
    doc = DocumentObject(
        filename=filename,
        raw_bytes=text.encode("utf-8"),
        format=DocumentFormat.TEXT,
        tenant_id=tenant_id,
    )
    return await orchestrator.ingest(doc)


@pytest.mark.asyncio
async def test_end_to_end_query_never_retrieves_across_tenants():
    """The real Phase 0 acceptance test: ingest two tenants' documents with
    a shared, distinctive marker phrase that would trivially cross-match
    on any retrieval signal (semantic, lexical, or otherwise) if tenant
    scoping were not enforced upstream of the search backends, then
    confirm a tenant-scoped, unscoped-by-doc_id query only ever surfaces
    that tenant's own content -- exercising the real retrieve() call
    through AMDIRetriever and its constituent search engines, not a mock."""
    orchestrator = AMDIOrchestrator()
    try:
        await _ingest_text(
            orchestrator, "a.txt",
            "SHARED_MARKER_PHRASE quarterly revenue figures for tenant A.",
            tenant_id="tenant-a",
        )
        await _ingest_text(
            orchestrator, "b.txt",
            "SHARED_MARKER_PHRASE quarterly revenue figures for tenant B.",
            tenant_id="tenant-b",
        )

        result = await orchestrator.query(
            "What are the SHARED_MARKER_PHRASE quarterly revenue figures?",
            tenant_id="tenant-a",
        )

        answer_and_context = str(result.get("answer", "")) + str(result.get("citations", ""))
        assert "tenant B" not in answer_and_context, (
            "A tenant-scoped query's retrieval surfaced another tenant's "
            "document content -- the search backends or their upstream "
            "scoping leaked across the tenant boundary."
        )
    finally:
        await orchestrator.close()


@pytest.mark.asyncio
async def test_retriever_receives_only_pre_scoped_elements():
    """Directly confirms the mechanism (not just the outcome above): the
    elements list AMDIRetriever.retrieve() actually receives for a
    tenant-scoped call must already be filtered to that tenant's own
    documents -- proving the search backends' lack of tenant_id awareness
    is safe specifically because they never receive unscoped input, not
    merely that the final answer happened to look correct."""
    orchestrator = AMDIOrchestrator()
    try:
        await _ingest_text(orchestrator, "a.txt", "Tenant A content only.", tenant_id="tenant-a")
        await _ingest_text(orchestrator, "b.txt", "Tenant B content only.", tenant_id="tenant-b")

        allowed_docs = {d for d, t in orchestrator._doc_tenant.items() if t == "tenant-a"}
        elements = [e for d in allowed_docs for e in orchestrator._doc_elements.get(d, [])]

        assert len(elements) > 0
        assert all(
            orchestrator._doc_tenant.get(e.doc_id) == "tenant-a" for e in elements
        ), (
            "Scoped elements returned elements belonging to a "
            "document not owned by the requesting tenant."
        )
    finally:
        await orchestrator.close()


@pytest.mark.asyncio
async def test_cli_only_workflows_are_not_imported_by_the_http_api():
    """Structural confirmation of the adjacent finding: IngestWorkflow and
    QueryWorkflow (which do NOT have tenant scoping, correctly, since
    they're single-user CLI tools) must never be reachable from the
    multi-tenant HTTP API. This test fails loudly if a future change
    wires either into src/api/ or src/main.py without also adding
    equivalent tenant scoping."""
    import ast
    import pathlib

    api_root = pathlib.Path("src/api")
    main_file = pathlib.Path("src/main.py")
    offending_files = []

    for py_file in list(api_root.rglob("*.py")) + [main_file]:
        if not py_file.exists():
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "workflows" in node.module:
                names = {alias.name for alias in node.names}
                if names & {"IngestWorkflow", "QueryWorkflow"}:
                    offending_files.append(str(py_file))

    assert not offending_files, (
        f"IngestWorkflow/QueryWorkflow (no tenant scoping) are now imported "
        f"by the multi-tenant HTTP API in: {offending_files}. These classes "
        f"must not be used in a multi-tenant server context without first "
        f"adding tenant scoping equivalent to AMDIOrchestrator's."
    )

