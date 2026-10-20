"""
Tests for query streaming integration across AMDIOrchestrator, QueryService, and LLMInterface.
Validates:
- Token-by-token streaming response generation
- Scoped streaming retrieval for specific doc_id and tenant_id
- Cross-tenant streaming query permission enforcement
- Document re-hydration during streaming queries after service restart
"""
import pytest
from unittest.mock import MagicMock

from src.core.orchestrator import AMDIOrchestrator
from src.services.container import RealDocumentService
from src.services.query_service import QueryService


@pytest.mark.asyncio
async def test_stream_query_end_to_end_mock(tmp_path):
    db_file = tmp_path / "stream_docs.db"
    dim = 1024
    orchestrator = AMDIOrchestrator(config={"embedding_dim": dim, "llm_provider": "mock"})
    doc_service = RealDocumentService(orchestrator, db_path=str(db_file))
    query_service = QueryService(
        rag_engine=orchestrator,
        memory_engine=None,
        llm_service=MagicMock(),
        embedding_model=orchestrator._embedding,
        document_service=doc_service,
    )

    # 1. Ingest document with >= 2 elements
    content = (
        b"Financial Overview Section:\n\n"
        b"Net earnings increased to $5.2 million for the fiscal quarter, outperforming expectations."
    )
    res = await doc_service.ingest(
        file_bytes=content,
        filename="earnings.txt",
        content_type="text/plain",
        tenant_id="tenant-stream",
    )
    doc_id = res.doc_id

    # 2. Stream query from authorized tenant
    tokens = []
    async for chunk in query_service.stream_query(
        question="What were the net earnings?",
        tenant_id="tenant-stream",
        doc_ids=[doc_id],
    ):
        if chunk.get("type") == "token":
            tokens.append(chunk["content"])

    full_response = "".join(tokens)
    assert len(tokens) > 0
    assert "[MOCK STREAM]" in full_response or "earnings" in full_response.lower()

    # 3. Cross-tenant stream query should fail with PermissionError
    with pytest.raises(PermissionError):
        async for _ in query_service.stream_query(
            question="What were the net earnings?",
            tenant_id="wrong-tenant",
            doc_ids=[doc_id],
        ):
            pass

    await orchestrator.close()


@pytest.mark.asyncio
async def test_stream_query_rehydrates_after_restart(tmp_path):
    db_file = tmp_path / "rehydrate_stream.db"
    dim = 1024

    # 1. Ingest in instance 1 with >= 2 elements
    orch1 = AMDIOrchestrator(config={"embedding_dim": dim, "llm_provider": "mock"})
    doc_service1 = RealDocumentService(orch1, db_path=str(db_file))
    content = (
        b"Policy Update Notice:\n\n"
        b"Annual leave entitlement is updated to 25 working days per calendar year for all staff."
    )
    res = await doc_service1.ingest(
        file_bytes=content,
        filename="policy.txt",
        content_type="text/plain",
        tenant_id="tenant-hr",
    )
    doc_id = res.doc_id
    await orch1.close()

    # 2. Start fresh orchestrator instance simulating server restart
    orch2 = AMDIOrchestrator(config={"embedding_dim": dim, "llm_provider": "mock"})
    assert doc_id not in orch2._doc_state

    doc_service2 = RealDocumentService(orch2, db_path=str(db_file))
    query_service2 = QueryService(
        rag_engine=orch2,
        memory_engine=None,
        llm_service=MagicMock(),
        embedding_model=orch2._embedding,
        document_service=doc_service2,
    )

    # 3. Stream query triggers re-hydration into orch2
    tokens = []
    async for chunk in query_service2.stream_query(
        question="How many days is annual leave?",
        tenant_id="tenant-hr",
        doc_ids=[doc_id],
    ):
        if chunk.get("type") == "token":
            tokens.append(chunk["content"])

    assert len(tokens) > 0
    assert doc_id in orch2._doc_state
    await orch2.close()
