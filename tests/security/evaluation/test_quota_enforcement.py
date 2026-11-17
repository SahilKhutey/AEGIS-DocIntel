"""
AEGIS Evaluation Security Tests — Server-Side Atomic Quota Enforcement (PROT-04 WP-04.06)
Tests:
- QUOTA-001: Operations within quota succeed
- QUOTA-002: Exceeding daily quota returns HTTP 429 Too Many Requests
- QUOTA-003: High-concurrency parallel requests crossing quota boundary are strictly enforced without race leaks
- QUOTA-004: Files exceeding 10 MB payload limit are rejected
"""

import concurrent.futures
import io
import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.quotas import quota_manager


def test_quota_001_request_within_quota_accepted(client: TestClient, valid_eval_license):
    """QUOTA-001: Initial queries within quota succeed."""
    headers = valid_eval_license["headers"]
    res = client.post("/v1/evaluation/query", headers=headers, json={"query": "TFLOPS specifications"})
    assert res.status_code == 200
    assert "citations" in res.json()


def test_quota_002_request_exceeds_quota_rejected_429(client: TestClient, valid_eval_license):
    """QUOTA-002: Exceeding daily query limit (20) returns HTTP 429."""
    headers = valid_eval_license["headers"]

    # Send 20 queries (limit is 20)
    for i in range(20):
        res = client.post("/v1/evaluation/query", headers=headers, json={"query": f"Query #{i+1}"})
        assert res.status_code == 200

    # 21st query must be rejected
    res_exceeded = client.post("/v1/evaluation/query", headers=headers, json={"query": "Query #21"})
    assert res_exceeded.status_code == 429
    data = res_exceeded.json()
    assert data["error"] == "QUOTA_EXCEEDED"
    assert data["resource"] == "queries"


def test_quota_003_parallel_requests_cross_quota_boundary_strictly_enforced(client: TestClient, valid_eval_license):
    """
    QUOTA-003: Race condition attack test.
    When a license has only 3 remaining slots and 10 simultaneous threads fire concurrently,
    exactly 3 must succeed and 7 must be rejected with 429 (no race-condition over-granting).
    """
    headers = valid_eval_license["headers"]
    lic_id = valid_eval_license["license_id"]

    # Pre-fill 17 queries so exactly 3 remain out of 20
    for _ in range(17):
        quota_manager.record_query(lic_id, max_limit=20)

    results = []

    def fire_request(req_idx):
        res = client.post(
            "/v1/evaluation/query",
            headers=headers,
            json={"query": f"Parallel query {req_idx}"},
        )
        return res.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fire_request, i) for i in range(10)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    successes = results.count(200)
    rejections = results.count(429)

    # Exactly 3 must succeed, 7 must be rejected
    assert successes == 3, f"Expected exactly 3 successful queries, got {successes}"
    assert rejections == 7, f"Expected exactly 7 rejected queries with 429, got {rejections}"


def test_quota_004_oversized_upload_rejected(client: TestClient, valid_eval_license):
    """QUOTA-004: Files exceeding 10 MB payload limit are rejected with 413."""
    headers = valid_eval_license["headers"]
    # 11 MB dummy buffer
    large_payload = b"A" * (11 * 1024 * 1024)

    res = client.post(
        "/v1/evaluation/documents",
        headers=headers,
        files={"file": ("oversized_document.txt", io.BytesIO(large_payload), "text/plain")},
    )
    assert res.status_code in (413, 400)
    assert res.json()["error"] == "FILE_TOO_LARGE"
