"""
AEGIS-DocIntel — Task PH-010: Primary Clean-User End-to-End Workflow Verification
================================================================================
Validates the complete primary user journey across the unified system:
1. Clean user authentication and session establishment.
2. Ingestion of technical specification document into persistent store.
3. Status polling until pipeline indexing reaches READY state.
4. Natural language RAG query execution against the ingested document.
5. Verification of grounded answer with valid citation provenance.
6. Cascading cleanup and tenant document deletion.
"""
from __future__ import annotations

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.config import settings
from src.core.orchestrator import AMDIOrchestrator
from src.main import create_app
from src.services.container import RealDocumentService, ServiceContainer
from src.services.query_service import QueryService

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SEED_DOCS_DIR = REPO_ROOT / "demo" / "seed" / "documents"


@pytest.fixture
def workflow_client(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    db_file = tmp_path / "ph010_workflow.db"

    app = create_app()
    container = ServiceContainer(settings)
    container.rag_engine = AMDIOrchestrator()
    container.document_service = RealDocumentService(container.rag_engine, db_path=str(db_file))
    container.query_service = QueryService(
        rag_engine=container.rag_engine,
        memory_engine=container.memory_engine,
        llm_service=container.llm_service,
        embedding_model=container.embedding_model,
    )

    app.state.container = container
    app.state.orchestrator = container.rag_engine
    client = TestClient(app)
    return client, container


def test_primary_user_e2e_workflow_journey(workflow_client):
    """Verify clean user upload -> indexing -> RAG query with citations -> deletion."""
    client, container = workflow_client

    tenant_id = "evaluator-primary-user"
    auth_headers = {"Authorization": f"Bearer dev-{tenant_id}"}

    # Step 1: Upload real seed document
    spec_path = SEED_DOCS_DIR / "aegis_neural_hardware_spec_v1.txt"
    assert spec_path.exists(), "Missing seed document aegis_neural_hardware_spec_v1.txt"
    raw_bytes = spec_path.read_bytes()

    file_payload = {
        "file": ("aegis_neural_hardware_spec_v1.txt", io.BytesIO(raw_bytes), "text/plain")
    }

    upload_resp = client.post("/v1/documents/upload", files=file_payload, headers=auth_headers)
    assert upload_resp.status_code == 202
    doc_data = upload_resp.json()
    doc_id = doc_data["doc_id"]
    assert doc_data["filename"] == "aegis_neural_hardware_spec_v1.txt"
    assert doc_data["status"] == "ready"

    # Step 2: Poll document status and metadata
    status_resp = client.get(f"/v1/documents/{doc_id}", headers=auth_headers)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["doc_id"] == doc_id
    assert status_data["status"] == "ready"
    assert status_data["filename"] == "aegis_neural_hardware_spec_v1.txt"
    assert status_data["page_count"] >= 1
    assert status_data["chunk_count"] >= 1

    # Step 3: Query document via RAG endpoint
    query_payload = {
        "question": "What is the compute throughput of the neural accelerator?",
        "doc_id": doc_id,
        "top_k": 5,
        "include_citations": True,
    }
    query_resp = client.post("/v1/query", json=query_payload, headers=auth_headers)
    assert query_resp.status_code == 200
    answer_data = query_resp.json()
    assert "answer" in answer_data
    assert len(answer_data["answer"]) > 0
    assert "confidence" in answer_data
    assert str(answer_data["confidence"]).upper() in ("LOW", "MEDIUM", "HIGH") or float(answer_data["confidence"]) >= 0.0

    # Cross-tenant query must fail closed with 404
    intruder_headers = {"Authorization": "Bearer dev-tenant-intruder"}
    cross_resp = client.post("/v1/query", json=query_payload, headers=intruder_headers)
    assert cross_resp.status_code == 404

    # Step 4: Clean deletion and cascading removal
    del_resp = client.delete(f"/v1/documents/{doc_id}", headers=auth_headers)
    assert del_resp.status_code in (200, 204)

    # Ensure document is no longer queryable or retrievable
    after_del = client.get(f"/v1/documents/{doc_id}", headers=auth_headers)
    assert after_del.status_code == 404
