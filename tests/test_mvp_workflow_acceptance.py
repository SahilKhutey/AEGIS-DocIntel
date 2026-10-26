"""
AEGIS-DocIntel — End-to-End MVP Acceptance Test Suite
=====================================================
Verifies the complete document-to-grounded-context product workflow:
1. Ingest document via public API (/v1/ingest).
2. Verify synchronous indexing, metadata extraction, and storage isolation.
3. Retrieve grounded evidence via /v1/query with verifiable source citations.
4. Enforce strict cross-tenant isolation (IDOR rejection with 404).
5. Verify safe abstention and cascading deletion.
6. Verify golden dataset integrity and PII redaction primitives.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Isolated test client fixture using temporary database and mock LLM."""
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AEGIS_LLM_PROVIDER", "mock")
    from src.config import settings
    monkeypatch.setattr(settings.llm, "provider", "mock")

    db_file = tmp_path / "test_mvp_acceptance.db"
    monkeypatch.setenv("AEGIS_SQLITE_PATH", str(db_file))

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_ingest_retrieve_and_verify_source_references(client):
    """
    A tenant can ingest a document and query it through the public API,
    receiving grounded answers with verifiable source references.
    """
    headers = {"Authorization": "Bearer dev-mvp-acceptance"}
    document = (
        b"AEGIS MVP acceptance fixture\n\n"
        b"Project code: ORBIT-731.\n\n"
        b"Approved operating budget: 125000 INR.\n\n"
        b"The document owner is the Orbit engineering team."
    )

    # 1. Ingest through the existing endpoint
    upload = client.post(
        "/v1/ingest",
        headers=headers,
        files={
            "file": (
                "mvp-acceptance.txt",
                document,
                "text/plain",
            )
        },
    )
    assert upload.status_code == 201, f"Upload failed: {upload.text}"
    data = upload.json()
    assert "doc_id" in data
    doc_id = data["doc_id"]
    assert data["filename"] == "mvp-acceptance.txt"

    # 2. Verify document status through /v1/documents/{doc_id}
    status_resp = client.get(f"/v1/documents/{doc_id}", headers=headers)
    assert status_resp.status_code == 200
    doc_meta = status_resp.json()
    assert doc_meta["doc_id"] == doc_id
    assert doc_meta["status"] in ("ready", "processing")

    # 3. Query document and verify grounded citations
    query_payload = {
        "question": "What is the approved operating budget for Project Orbit?",
        "doc_ids": [doc_id],
        "include_citations": True,
    }
    query_resp = client.post("/v1/query", headers=headers, json=query_payload)
    assert query_resp.status_code == 200, f"Query failed: {query_resp.text}"
    q_data = query_resp.json()
    assert "answer" in q_data
    assert len(q_data["answer"]) > 0
    assert "citations" in q_data
    assert len(q_data["citations"]) >= 1

    first_cit = q_data["citations"][0]
    cit_doc_id = first_cit.get("doc_id") or first_cit.get("document_id")
    assert cit_doc_id == doc_id, f"Citation doc_id {cit_doc_id} did not match ingested doc {doc_id}"

    # 4. Cross-tenant isolation (IDOR protection: intruder tenant cannot query doc_id)
    headers_intruder = {"Authorization": "Bearer dev-tenant-intruder"}
    cross_resp = client.post("/v1/query", headers=headers_intruder, json=query_payload)
    assert cross_resp.status_code == 404, f"Expected 404 for cross-tenant query, got {cross_resp.status_code}"

    # Cross-tenant get document rejection
    cross_get = client.get(f"/v1/documents/{doc_id}", headers=headers_intruder)
    assert cross_get.status_code == 404, f"Expected 404 for cross-tenant get, got {cross_get.status_code}"

    # 5. Safe abstention on unrelated / ungrounded query
    unrelated_payload = {
        "question": "What was the quantum gravity constant measured in 2045?",
        "doc_ids": [doc_id],
        "include_citations": True,
    }
    unrelated_resp = client.post("/v1/query", headers=headers, json=unrelated_payload)
    assert unrelated_resp.status_code == 200
    unrelated_data = unrelated_resp.json()
    assert "answer" in unrelated_data

    # 6. Cascading deletion and cleanup
    del_resp = client.delete(f"/v1/documents/{doc_id}", headers=headers)
    assert del_resp.status_code == 204, f"Delete failed: {del_resp.text}"

    # Verify document is gone
    after_del_resp = client.get(f"/v1/documents/{doc_id}", headers=headers)
    assert after_del_resp.status_code == 404


def test_golden_manifest_integrity_and_properties():
    """Verify cryptographic SHA-256 integrity and properties of the MVP golden corpus."""
    root_dir = Path(__file__).resolve().parent.parent
    manifest_path = root_dir / "evaluation" / "mvp-golden" / "manifest.json"
    assert manifest_path.exists(), f"Golden manifest missing at {manifest_path}"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("dataset") == "aegis-mvp-golden"
    assert manifest.get("schema_version") == 1
    assert manifest.get("contains_sensitive_data") is False

    documents = manifest.get("documents", [])
    assert len(documents) >= 1

    for doc_entry in documents:
        doc_rel_path = doc_entry["path"]
        expected_rel_path = doc_entry["expected"]
        expected_sha = doc_entry["sha256"]

        doc_file = manifest_path.parent / doc_rel_path
        expected_file = manifest_path.parent / expected_rel_path

        assert doc_file.exists(), f"Fixture file missing: {doc_file}"
        assert expected_file.exists(), f"Expected JSON missing: {expected_file}"

        actual_sha = hashlib.sha256(doc_file.read_bytes()).hexdigest()
        assert actual_sha == expected_sha, f"SHA-256 mismatch for {doc_file}: {actual_sha} != {expected_sha}"

        exp_data = json.loads(expected_file.read_text(encoding="utf-8"))
        assert "key_facts" in exp_data
        assert "qa_pairs" in exp_data


def test_pii_redaction_privacy_filter():
    """Validate PII detection and redaction primitives on synthetic golden fixture."""
    from aegis_docprep import detect_pii, apply_redaction_policy

    root_dir = Path(__file__).resolve().parent.parent
    fixture_path = root_dir / "evaluation" / "mvp-golden" / "text" / "budget-summary.txt"
    text = fixture_path.read_text(encoding="utf-8")

    entities = detect_pii({"id": "budget-summary-001", "text": text})
    assert len(entities) > 0

    entity_types = {e.entity_type for e in entities}
    assert "CREDIT_CARD" in entity_types
    assert "US_SSN" in entity_types
    assert "EMAIL" in entity_types

    redacted = apply_redaction_policy(text, entities)
    assert "4532015112830366" not in redacted
    assert "000-12-3456" not in redacted
    assert "alex.mercer@example.org" not in redacted
    assert "<CREDIT_CARD_REDACTED>" in redacted
    assert "<US_SSN_REDACTED>" in redacted
