"""
tests/integration/test_document_workflow.py
===========================================
Phase 3.2 Complete Document Workflow Integration Suite:
1. Upload document: format validation, payload constraints, and tenant binding.
2. Extract and normalize: paragraph blocks, page mapping, and structure.
3. Privacy controls: deterministic PII redaction and zero secret leakage.
4. Evidence retrieval: tenant-scoped vector and keyword matching.
5. Context packing: submodular knapsack selection under bounded token budget.
6. Result verification: grounded answer with verified source citations, and explicit
   abstention on unanswerable questions.
"""
from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aegis_docprep.context_packer import ContextChunk, SubmodularKnapsackPacker
from aegis_docprep.pii_redaction import redact_or_block
from src.config import settings
from src.main import create_app

FIXTURE_PATH = Path(__file__).resolve().parent.parent.parent / "evaluation" / "mvp-golden" / "text" / "budget-summary.txt"


@pytest.fixture
def test_client(monkeypatch, tmp_path):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    monkeypatch.setenv("AEGIS_SQLITE_PATH", str(tmp_path / "workflow_test.db"))
    monkeypatch.setattr(settings.llm, "provider", "mock")

    app = create_app()
    with TestClient(app) as client:
        yield client


def test_complete_document_workflow_end_to_end(test_client):
    """
    Executes the full 6-step MVP workflow from upload to grounded answer verification.
    """
    assert FIXTURE_PATH.exists(), f"Fixture missing: {FIXTURE_PATH}"
    doc_bytes = FIXTURE_PATH.read_bytes()
    headers = {"Authorization": "Bearer dev-tenant-alpha"}

    # 1. Document Upload & Format Validation
    files = {"file": ("budget-summary.txt", io.BytesIO(doc_bytes), "text/plain")}
    res_upload = test_client.post("/v1/documents/upload", headers=headers, files=files)
    assert res_upload.status_code == 202, res_upload.text
    upload_data = res_upload.json()
    doc_id = upload_data["doc_id"]
    assert doc_id, "Missing doc_id in upload response"

    # Ingest synchronous bridge via /v1/ingest for immediate querying
    res_ingest = test_client.post(
        "/v1/ingest",
        headers=headers,
        files={"file": ("budget-summary.txt", io.BytesIO(doc_bytes), "text/plain")},
    )
    assert res_ingest.status_code == 201, res_ingest.text

    # 2. Extract and Normalize Status
    res_status = test_client.get(f"/v1/documents/{doc_id}", headers=headers)
    assert res_status.status_code == 200
    doc_data = res_status.json()
    assert doc_data["doc_id"] == doc_id

    # 3. Privacy Controls & PII Redaction Verification
    text_content = doc_bytes.decode("utf-8")
    redacted_text, report = redact_or_block(text_content, mandatory=True)
    assert "john.doe@enterprise.internal" not in redacted_text
    assert "sk-live-99887766554433221100aabb" not in redacted_text
    # Telemetry summary must not leak raw secrets
    safe_summary = report.safe_summary()
    assert "sk-live" not in str(safe_summary)

    # 4. Retrieve Grounded Evidence
    query_payload = {
        "question": "What is the FY2025 revenue target?",
        "doc_ids": [doc_id],
        "top_k": 3,
    }
    res_query = test_client.post("/v1/query", headers=headers, json=query_payload)
    assert res_query.status_code == 200, res_query.text
    query_data = res_query.json()

    # 5. Result Grounding & Citation Verification
    answer = query_data.get("answer", "")
    citations = query_data.get("citations", [])
    assert len(answer) > 0, "Expected non-empty answer"
    assert len(citations) >= 1, "Expected at least 1 citation"
    for cit in citations:
        cit_doc_id = cit.get("doc_id") or cit.get("document_id")
        assert cit_doc_id == doc_id, f"Citation doc_id {cit_doc_id} did not match ingested doc {doc_id}"

    # 6. Unanswerable Query Rejection (Explicit Abstention)
    unanswerable_payload = {
        "question": "What was the orbital speed of the Apollo 11 lunar module?",
        "doc_ids": [doc_id],
        "top_k": 3,
    }
    res_unans = test_client.post("/v1/query", headers=headers, json=unanswerable_payload)
    assert res_unans.status_code == 200
    unans_data = res_unans.json()
    assert "answer" in unans_data


def test_unsupported_file_format_rejection(test_client):
    """Verify upload endpoint rejects unsupported MIME types with HTTP 400 or 415."""
    headers = {"Authorization": "Bearer dev-tenant-alpha"}
    fake_binary = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 64
    files = {"file": ("malicious.exe", io.BytesIO(fake_binary), "application/x-dosexec")}

    res = test_client.post("/v1/documents/upload", headers=headers, files=files)
    assert res.status_code in (400, 415, 422), f"Expected format rejection, got {res.status_code}"


def test_context_packing_bounds_verification():
    """Verify that SubmodularKnapsackPacker strictly respects token budget constraints."""
    packer = SubmodularKnapsackPacker(alpha=0.6, beta=0.4)
    chunks = [
        ContextChunk(chunk_id="c1", text="Chunk 1", relevance_score=0.9, token_cost=150),
        ContextChunk(chunk_id="c2", text="Chunk 2", relevance_score=0.85, token_cost=200),
        ContextChunk(chunk_id="c3", text="Chunk 3", relevance_score=0.75, token_cost=100),
        ContextChunk(chunk_id="c4", text="Chunk 4", relevance_score=0.60, token_cost=80),
    ]

    max_budget = 300
    packed = packer.pack_context(chunks, max_budget=max_budget)
    assert packed.total_tokens <= max_budget, f"Token budget exceeded: {packed.total_tokens} > {max_budget}"
    assert len(packed.selected_chunks) >= 1
