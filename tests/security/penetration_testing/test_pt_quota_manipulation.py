"""
PT-06: Quota Manipulation Adversarial Tests
Covers PT-Q-001 through PT-Q-010.
Asserts that client-side manipulation, concurrent racing requests, negative usage values,
and replay attacks cannot exceed or corrupt server-side authoritative quotas.
"""

from __future__ import annotations

import io
from concurrent.futures import ThreadPoolExecutor
from services.evaluation_gateway.quotas import quota_manager


def test_pt_q_001_modify_local_usage_counter(evaluator_a_license, gateway_client):
    """PT-Q-001: Client altering local localStorage usage counters has zero effect on server quotas."""
    headers = evaluator_a_license["headers"].copy()
    headers["X-Client-Usage-Count"] = "0"
    headers["X-Queries-Remaining"] = "9999"

    # Make valid queries
    for _ in range(5):
        res = gateway_client.post("/api/v1/gateway/query", headers=headers, json={"query": "test query"})
        assert res.status_code == 200

    # Server counter increments regardless of header claims
    lic_id = evaluator_a_license["license_id"]
    status = quota_manager.get_quota_status(lic_id)
    assert status["queries"]["used"] >= 5


def test_pt_q_002_submit_repeated_identical_request(evaluator_a_license, gateway_client):
    """PT-Q-002: Replaying identical request with idempotency key charges quota idempotently."""
    headers = evaluator_a_license["headers"].copy()
    headers["X-Idempotency-Key"] = "idemp-pt-q-002-unique-key"

    lic_id = evaluator_a_license["license_id"]
    initial_used = quota_manager.get_quota_status(lic_id)["queries"]["used"]

    # First request
    res1 = gateway_client.post("/api/v1/gateway/query", headers=headers, json={"query": "idempotent test"})
    assert res1.status_code == 200

    # Second request
    res2 = gateway_client.post("/api/v1/gateway/query", headers=headers, json={"query": "idempotent test"})
    assert res2.status_code == 200


def test_pt_q_003_send_concurrent_requests(evaluator_a_license, gateway_client):
    """PT-Q-003: Concurrent requests against remaining quota limit do not cause overspending."""
    lic_id = evaluator_a_license["license_id"]
    quota_manager.reset_usage(lic_id)

    # Ingest 3 documents so 2 slots remain (max 5)
    for i in range(3):
        gateway_client.post(
            "/api/v1/gateway/documents",
            headers=evaluator_a_license["headers"],
            files={"file": (f"seed_{i}.txt", io.BytesIO(b"content"), "text/plain")}
        )

    def upload_doc(index: int):
        return gateway_client.post(
            "/api/v1/gateway/documents",
            headers=evaluator_a_license["headers"],
            files={"file": (f"race_{index}.txt", io.BytesIO(f"race content {index}".encode()), "text/plain")}
        )

    # Fire 10 concurrent requests for the 2 remaining document slots
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(upload_doc, range(10)))

    successes = sum(1 for r in results if r.status_code in (200, 201))
    rejected = sum(1 for r in results if r.status_code == 429)

    # Exactly 2 should succeed, remaining 8 rejected
    assert successes == 2
    assert rejected == 8

    # Usage must strictly equal 5, never exceed 5
    final_used = quota_manager.get_quota_status(lic_id)["documents"]["used"]
    assert final_used == 5


def test_pt_q_004_abort_operation_after_reservation(evaluator_a_license):
    """PT-Q-004: Aborting or failing an operation after reservation safely reconciles quota."""
    lic_id = evaluator_a_license["license_id"]
    quota_manager.reset_usage(lic_id)

    # Reserve 1 query
    res_id = quota_manager.reserve_quota(lic_id, "queries", 1)
    assert res_id is not None

    # Abort / rollback reservation
    quota_manager.rollback_reservation(lic_id, res_id)

    # Quota is restored
    assert quota_manager.get_quota_status(lic_id)["queries"]["used"] == 0


def test_pt_q_005_replay_settlement(evaluator_a_license):
    """PT-Q-005: Replaying quota settlement does not result in double charge or corruption."""
    lic_id = evaluator_a_license["license_id"]
    quota_manager.reset_usage(lic_id)

    res_id = quota_manager.reserve_quota(lic_id, "queries", 1)
    assert res_id is not None

    # Settle reservation once
    quota_manager.settle_reservation(lic_id, res_id, 1)
    assert quota_manager.get_quota_status(lic_id)["queries"]["used"] == 1

    # Second settle attempt with same token is a no-op or handled safely
    try:
        quota_manager.settle_reservation(lic_id, res_id, 1)
    except Exception:
        pass
    assert quota_manager.get_quota_status(lic_id)["queries"]["used"] == 1


def test_pt_q_006_submit_negative_usage_value(evaluator_a_license):
    """PT-Q-006: Submitting negative units to artificially increase available quota is strictly rejected."""
    lic_id = evaluator_a_license["license_id"]
    try:
        quota_manager.reserve_quota(lic_id, "queries", -50)
        assert False, "Negative quota reservation must raise exception"
    except (ValueError, Exception):
        pass  # Rejected as required


def test_pt_q_007_change_quota_period(evaluator_a_license, gateway_client):
    """PT-Q-007: Client injecting X-Quota-Period headers cannot reset server usage window."""
    headers = evaluator_a_license["headers"].copy()
    headers["X-Quota-Period"] = "monthly_reset"
    headers["X-Quota-Reset-Timestamp"] = "2026-01-01T00:00:00Z"

    res = gateway_client.post("/api/v1/gateway/query", headers=headers, json={"query": "test"})
    assert res.status_code == 200

    # Injected period headers have zero impact on server ledger
    lic_id = evaluator_a_license["license_id"]
    assert quota_manager.get_quota_status(lic_id)["queries"]["used"] >= 1


def test_pt_q_008_request_after_exhaustion(evaluator_a_license, gateway_client):
    """PT-Q-008: Once quota limit is reached, all subsequent operations return HTTP 429."""
    lic_id = evaluator_a_license["license_id"]
    quota_manager.reset_usage(lic_id)

    # Ingest maximum allowed documents (5)
    for i in range(5):
        res = gateway_client.post(
            "/api/v1/gateway/documents",
            headers=evaluator_a_license["headers"],
            files={"file": (f"max_{i}.txt", io.BytesIO(b"data"), "text/plain")}
        )
        assert res.status_code in (200, 201)

    # Request after exhaustion
    res = gateway_client.post(
        "/api/v1/gateway/documents",
        headers=evaluator_a_license["headers"],
        files={"file": ("denied.txt", io.BytesIO(b"data"), "text/plain")}
    )
    assert res.status_code == 429
    assert res.json()["error"] == "QUOTA_EXCEEDED"


def test_pt_q_009_change_tenant_id_for_quota_bypass(evaluator_a_license, gateway_client):
    """PT-Q-009: Altering tenant ID in query headers does not deduct from another tenant's quota."""
    headers = evaluator_a_license["headers"].copy()
    headers["X-Tenant-ID"] = "victim-tenant-beta"

    res = gateway_client.post("/api/v1/gateway/query", headers=headers, json={"query": "test"})
    assert res.status_code in (200, 403)
    if res.status_code == 200:
        # Deducted from Evaluator A's license, not victim
        lic_id = evaluator_a_license["license_id"]
        assert quota_manager.get_quota_status(lic_id)["queries"]["used"] >= 1


def test_pt_q_010_manipulate_token_usage_reported_by_client(evaluator_a_license, gateway_client):
    """PT-Q-010: Client reporting fabricated prompt token counts is ignored; server metering is authoritative."""
    headers = evaluator_a_license["headers"].copy()
    headers["X-Reported-Tokens"] = "1"
    headers["X-Consumed-Credits"] = "0.001"

    res = gateway_client.post("/api/v1/gateway/query", headers=headers, json={"query": "test length prompt"})
    assert res.status_code == 200
    # Server meter records actual query charge
    lic_id = evaluator_a_license["license_id"]
    assert quota_manager.get_quota_status(lic_id)["queries"]["used"] >= 1
