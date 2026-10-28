"""
tests/test_mvp5_api.py
======================
API contract and integration tests for Document Intelligence endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.services.container import ServiceContainer, RealDocumentService
from src.core.orchestrator import AMDIOrchestrator
from src.config import settings
from src.engines.intelligence.fact_store import FactStore
from src.engines.intelligence.service import DocumentIntelligenceService

AUTH_HEADER = {"Authorization": "Bearer dev-test-token"}


@pytest.fixture
def intelligence_app(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    db_file = tmp_path / "test_api_intel.db"
    store_file = tmp_path / "test_store_intel.db"

    app = create_app()
    container = ServiceContainer(settings)
    container._started = True
    container.rag_engine = AMDIOrchestrator()
    container.document_service = RealDocumentService(container.rag_engine, db_path=str(db_file))
    container.intelligence_service = DocumentIntelligenceService(
        fact_store=FactStore(db_path=str(store_file))
    )

    app.state.container = container
    app.state.orchestrator = container.rag_engine
    app.state.intelligence_service = container.intelligence_service
    client = TestClient(app)
    return app, client, container


def test_api_extract_facts_and_retrieve(intelligence_app):
    _, client, _ = intelligence_app

    # Anonymous request must fail with 401
    anon_resp = client.post(
        "/v1/documents/doc-contract-1/extract-facts",
        json={"schema_name": "contract_terms"},
    )
    assert anon_resp.status_code == 401

    # Authenticated extraction request
    payload = {
        "schema_name": "contract_terms",
        "passages": [
            {
                "chunk_id": "c1",
                "text": "The effective date is January 15, 2026. The initial agreement expiration date: December 31, 2028.",
                "page_number": 1,
            },
            {
                "chunk_id": "c2",
                "text": "Total aggregate liability shall not exceed $1,000,000 USD. Notice period of 30 days.",
                "page_number": 2,
            },
        ],
    }
    resp = client.post(
        "/v1/documents/doc-contract-1/extract-facts",
        json=payload,
        headers=AUTH_HEADER,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["document_id"] == "doc-contract-1"
    assert len(data["facts"]) >= 3

    # Retrieve facts via GET endpoint
    get_resp = client.get(
        "/v1/documents/doc-contract-1/facts",
        headers=AUTH_HEADER,
    )
    assert get_resp.status_code == 200
    facts = get_resp.json()
    assert len(facts) >= 3

    # Filter facts by attribute
    filter_resp = client.get(
        "/v1/documents/doc-contract-1/facts?attribute=effective_date",
        headers=AUTH_HEADER,
    )
    assert filter_resp.status_code == 200
    filtered = filter_resp.json()
    assert len(filtered) == 1
    assert filtered[0]["value"] == "2026-01-15"


def test_api_compare_documents_and_detect_conflicts(intelligence_app):
    _, client, _ = intelligence_app

    # Ingest Doc A facts
    payload_a = {
        "schema_name": "contract_terms",
        "passages": [
            {
                "chunk_id": "a1",
                "text": "Total aggregate liability shall not exceed $1,000,000 USD. Termination notice period of 30 days.",
                "page_number": 1,
            }
        ],
    }
    client.post(
        "/v1/documents/doc-sla-a/extract-facts",
        json=payload_a,
        headers=AUTH_HEADER,
    )

    # Ingest Doc B facts
    payload_b = {
        "schema_name": "contract_terms",
        "passages": [
            {
                "chunk_id": "b1",
                "text": "Total aggregate liability shall not exceed $2,500,000 USD. Termination notice period of 60 days.",
                "page_number": 1,
            }
        ],
    }
    client.post(
        "/v1/documents/doc-sla-b/extract-facts",
        json=payload_b,
        headers=AUTH_HEADER,
    )

    # Compare Doc A and Doc B
    comp_resp = client.post(
        "/v1/intelligence/compare",
        json={
            "left_document_id": "doc-sla-a",
            "right_document_id": "doc-sla-b",
        },
        headers=AUTH_HEADER,
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert len(comp_data["comparisons"]) >= 1
    assert comp_data["summary"].get("potential_conflict", 0) >= 1

    # Fetch conflicts
    conflict_resp = client.get(
        "/v1/intelligence/conflicts?document_ids=doc-sla-a&document_ids=doc-sla-b",
        headers=AUTH_HEADER,
    )
    assert conflict_resp.status_code == 200
    conflicts = conflict_resp.json()
    assert len(conflicts) >= 1
    attrs = {c["attribute"] for c in conflicts}
    assert "liability_cap" in attrs or "notice_period" in attrs
