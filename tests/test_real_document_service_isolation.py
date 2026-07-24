import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.container import RealDocumentService

@pytest.mark.asyncio
async def test_real_document_service_tenant_isolation():
    mock_orchestrator = MagicMock()
    mock_orchestrator.ingest = AsyncMock(return_value={"doc_id": "doc-100", "pages": 1, "elements": 2})
    
    doc_service = RealDocumentService(mock_orchestrator)
    
    # Ingest document under tenant-A
    resp = await doc_service.ingest(
        file_bytes=b"sample content",
        filename="test.pdf",
        content_type="application/pdf",
        tenant_id="tenant-A"
    )
    doc_id = resp.doc_id
    
    # 1. Fetching under tenant-A should succeed
    fetched_a = await doc_service.get(doc_id, tenant_id="tenant-A")
    assert fetched_a is not None
    assert fetched_a.filename == "test.pdf"

    # Fetching under tenant-B should return None (simulating 404)
    fetched_b = await doc_service.get(doc_id, tenant_id="tenant-B")
    assert fetched_b is None

    # 2. Get status under tenant-A vs tenant-B
    status_a = await doc_service.get_status(doc_id, tenant_id="tenant-A")
    assert status_a is not None
    status_b = await doc_service.get_status(doc_id, tenant_id="tenant-B")
    assert status_b is None

    # 3. List chunks under tenant-B handling PermissionError from orchestrator
    mock_orchestrator.get_document_elements.side_effect = PermissionError("Access denied")
    chunks_b = await doc_service.list_chunks(doc_id, tenant_id="tenant-B")
    assert len(chunks_b.items) == 0

    # 4. Deleting under tenant-B should fail
    deleted_b = await doc_service.delete(doc_id, tenant_id="tenant-B")
    assert deleted_b is False
    assert (await doc_service.get(doc_id, tenant_id="tenant-A")) is not None

    # 5. Deleting under tenant-A should succeed
    deleted_a = await doc_service.delete(doc_id, tenant_id="tenant-A")
    assert deleted_a is True
    assert (await doc_service.get(doc_id, tenant_id="tenant-A")) is None
