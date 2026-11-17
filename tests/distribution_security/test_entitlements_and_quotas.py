"""
AEGIS Distribution Security Tests — Server-Side Entitlements & Quotas
Covers:
- SEC-DEMO-005: Unauthenticated access without evaluation token returns HTTP 401
- SEC-DEMO-009: Max document quota strictly enforced server-side (HTTP 429)
- SEC-DEMO-010: Daily query quota strictly enforced server-side (HTTP 429)
- SEC-DEMO-014: Daily comparison quota strictly enforced server-side (HTTP 429)
- SEC-DEMO-015: Oversized file upload (>10 MB) rejected (HTTP 413)
- SEC-DEMO-019: Brute-force activation rate limiting protection
"""

import io
import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.app import app
from services.evaluation_gateway.license import issue_evaluation_license, export_license_token
from services.evaluation_gateway.quotas import quota_manager

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def valid_license_header():
    lic = issue_evaluation_license(user_id="quota-tester", duration_days=14)
    token = export_license_token(lic)
    quota_manager.reset_usage(lic["payload"]["license_id"])
    return {"X-Evaluation-License": token}, lic["payload"]["license_id"]


def test_sec_demo_005_unauthenticated_request_rejected(client: TestClient):
    """SEC-DEMO-005: Requests to protected endpoints without evaluation license token return 401."""
    res = client.post("/api/v1/gateway/query", json={"query": "What is the peak TFLOPS?"})
    assert res.status_code == 401
    data = res.json()
    assert data["error"] == "MISSING_EVALUATION_TOKEN"


def test_sec_demo_009_document_upload_quota_enforced(client: TestClient, valid_license_header):
    """SEC-DEMO-009: Uploading more than 5 documents is blocked server-side with HTTP 429."""
    headers, lic_id = valid_license_header

    # Upload 5 documents successfully
    for i in range(5):
        file_content = f"Evaluation Document #{i+1} content".encode("utf-8")
        res = client.post(
            "/api/v1/gateway/documents",
            headers=headers,
            files={"file": (f"test_doc_{i+1}.txt", io.BytesIO(file_content), "text/plain")}
        )
        assert res.status_code == 200, f"Upload {i+1} should succeed"

    # Attempt 6th document upload -> Should be rejected with 429
    file_content_6 = b"Evaluation Document #6 should exceed quota"
    res_6 = client.post(
        "/api/v1/gateway/documents",
        headers=headers,
        files={"file": ("test_doc_6.txt", io.BytesIO(file_content_6), "text/plain")}
    )
    assert res_6.status_code == 429
    data = res_6.json()
    assert data["error"] == "QUOTA_EXCEEDED"
    assert data["resource"] == "documents"


def test_sec_demo_010_daily_query_quota_enforced(client: TestClient, valid_license_header):
    """SEC-DEMO-010: More than 20 queries within 24 hours is blocked server-side with HTTP 429."""
    headers, lic_id = valid_license_header

    # Execute 20 queries
    for i in range(20):
        res = client.post(
            "/api/v1/gateway/query",
            headers=headers,
            json={"query": f"Query #{i+1} for performance"}
        )
        assert res.status_code == 200, f"Query {i+1} should succeed"

    # 21st query must fail with 429
    res_21 = client.post(
        "/api/v1/gateway/query",
        headers=headers,
        json={"query": "Query #21 exceeding daily limit"}
    )
    assert res_21.status_code == 429
    data = res_21.json()
    assert data["error"] == "QUOTA_EXCEEDED"
    assert data["resource"] == "queries"


def test_sec_demo_014_comparison_quota_enforced(client: TestClient, valid_license_header):
    """SEC-DEMO-014: More than 5 comparisons is blocked server-side with HTTP 429."""
    headers, lic_id = valid_license_header

    # Ingest 2 documents for comparison
    d1 = client.post(
        "/api/v1/gateway/documents",
        headers=headers,
        files={"file": ("spec1.txt", io.BytesIO(b"spec 1"), "text/plain")}
    ).json()["document_id"]
    
    d2 = client.post(
        "/api/v1/gateway/documents",
        headers=headers,
        files={"file": ("spec2.txt", io.BytesIO(b"spec 2"), "text/plain")}
    ).json()["document_id"]

    for i in range(5):
        res = client.post(
            "/api/v1/gateway/compare",
            headers=headers,
            json={"left_document_id": d1, "right_document_id": d2}
        )
        assert res.status_code == 200

    # 6th comparison must fail
    res_6 = client.post(
        "/api/v1/gateway/compare",
        headers=headers,
        json={"left_document_id": d1, "right_document_id": d2}
    )
    assert res_6.status_code == 429
    assert res_6.json()["error"] == "QUOTA_EXCEEDED"


def test_sec_demo_015_oversized_file_rejected(client: TestClient, valid_license_header):
    """SEC-DEMO-015: Ingesting a file larger than 10 MB is rejected with HTTP 413."""
    headers, _ = valid_license_header
    oversized = b"0" * (10 * 1024 * 1024 + 1024)  # 10 MB + 1 KB

    res = client.post(
        "/api/v1/gateway/documents",
        headers=headers,
        files={"file": ("huge.txt", io.BytesIO(oversized), "text/plain")}
    )
    assert res.status_code == 413
    assert res.json()["error"] == "FILE_TOO_LARGE"


def test_sec_demo_019_activation_brute_force_protection(client: TestClient):
    """SEC-DEMO-019: Automated spamming of the activation endpoint triggers IP rate limiting."""
    # Attempt 12 rapid activations from same client IP
    status_codes = []
    for i in range(12):
        res = client.post(
            "/api/v1/gateway/activate",
            json={"client_id": f"bot-{i}", "machine_name": "bot-machine"}
        )
        status_codes.append(res.status_code)

    # At least the later attempts must be rejected with 429
    assert 429 in status_codes
