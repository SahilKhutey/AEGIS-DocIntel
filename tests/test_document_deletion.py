"""
test_document_deletion.py
==========================
Regression tests asserting real cascading document deletion:
Asserts that document deletion clears:
1. Primary document index (_docs dictionary in RealDocumentService)
2. Vector store (FAISS / NumPy index in AMDIOrchestrator._vector_store)
3. Semantic cache (SemanticCache in ServiceContainer.memory_engine)
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock

from src.core.orchestrator import AMDIOrchestrator
from src.services.container import RealDocumentService
from src.memory_engine.semantic_cache import SemanticCache
from src.engines.vector_db.faiss_store import FAISSStore


@pytest.mark.asyncio
async def test_cascading_document_deletion_all_three_stores(monkeypatch):
    """Verify document deletion cascades to vector store and semantic cache."""
    monkeypatch.setenv("AMDI_MOCK_EMBEDDINGS", "true")

    dim = 1024
    orchestrator = AMDIOrchestrator(config={"embedding_dim": dim})
    cache = SemanticCache(redis_client=None)
    orchestrator.semantic_cache = cache
    doc_service = RealDocumentService(orchestrator)

    tenant_id = "test-tenant-compliance"
    other_tenant = "other-tenant"

    # 1. Ingest a multi-paragraph document (ensuring >= 2 elements for topology analysis)
    doc_content = (
        b"Patient Record: John Doe\n\n"
        b"Treatment Plan: Annual physical examination and laboratory testing.\n\n"
        b"Clinical Assessment: All vital signs normal, scheduled for routine follow-up."
    )
    doc_resp = await doc_service.ingest(
        file_bytes=doc_content,
        filename="patient_record.txt",
        content_type="text/plain",
        tenant_id=tenant_id,
    )
    doc_id = doc_resp.doc_id

    # Verify primary index has document
    assert doc_id in doc_service._docs
    assert str(doc_service._docs[doc_id]["tenant_id"]) == tenant_id

    # Verify orchestrator has state
    assert doc_id in orchestrator._doc_state

    # Verify vector store has active vectors
    vstore = orchestrator.vector_store
    assert vstore is not None
    initial_vector_count = vstore.count()
    assert initial_vector_count > 0

    # 2. Add an entry into semantic cache referencing this document
    dummy_vec = np.ones(dim, dtype=np.float32)
    await cache.cache_response(
        question="What is John Doe's treatment plan?",
        embedding=dummy_vec,
        response={"answer": "Annual physical examination"},
        tenant_id=tenant_id,
        doc_ids=[doc_id],
    )

    # Verify cache has entry
    assert tenant_id in cache._entries
    assert len(cache._entries[tenant_id]) == 1

    # 3. Test Cross-Tenant Deletion Rejection (Tenant Isolation)
    del_other = await doc_service.delete(doc_id=doc_id, tenant_id=other_tenant)
    assert del_other is False
    # Ensure all stores remain untouched after rejected deletion
    assert doc_id in doc_service._docs
    assert doc_id in orchestrator._doc_state
    assert vstore.count() == initial_vector_count
    assert len(cache._entries[tenant_id]) == 1

    # 4. Perform Authorized Cascading Deletion
    del_success = await doc_service.delete(doc_id=doc_id, tenant_id=tenant_id)
    assert del_success is True

    # STORE 1: Primary document index cleared
    assert doc_id not in doc_service._docs
    assert await doc_service.get(doc_id=doc_id, tenant_id=tenant_id) is None

    # STORE 2: Vector store cleared (vectors for doc_id lazy-deleted)
    assert vstore.count() < initial_vector_count
    # Verify vector search no longer returns vectors for this doc_id
    search_res = await vstore.search(dummy_vec, top_k=10)
    matching = [r for r in search_res if r["metadata"].get("doc_id") == doc_id]
    assert len(matching) == 0

    # STORE 3: Semantic cache cleared
    assert len(cache._entries[tenant_id]) == 0

    # Orchestrator document state cleared
    assert doc_id not in orchestrator._doc_state

    # Repeated deletion should return False
    del_again = await doc_service.delete(doc_id=doc_id, tenant_id=tenant_id)
    assert del_again is False


@pytest.mark.asyncio
async def test_cascading_deletion_resilience_to_store_failures():
    """Verify document deletion succeeds even if vector store or cache fails."""
    mock_orchestrator = MagicMock(spec=AMDIOrchestrator)
    mock_vector_store = AsyncMock()
    mock_vector_store.delete.side_effect = RuntimeError("Vector DB connection timeout")
    mock_orchestrator.vector_store = mock_vector_store

    mock_cache = AsyncMock()
    mock_cache.invalidate.side_effect = ConnectionError("Redis cache down")
    mock_orchestrator.semantic_cache = mock_cache

    service = RealDocumentService(mock_orchestrator)
    doc_id = "doc-fail-resilience"
    service._docs[doc_id] = {"doc_id": doc_id, "tenant_id": "t1"}

    # Should catch errors, log warnings, and still remove doc from primary index
    res = await service.delete(doc_id, tenant_id="t1")
    assert res is True
    assert doc_id not in service._docs
    mock_vector_store.delete.assert_called_once_with(doc_id=doc_id)
    mock_cache.invalidate.assert_called_once_with(doc_id=doc_id)
