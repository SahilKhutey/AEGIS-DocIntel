"""
AEGIS Evaluation Security Tests — REM-04: Quota Accounting & Resource Limits
Verifies acceptance criteria QTA-REM-001 through QTA-REM-012:
- QTA-REM-001: Capacity reservation (atomic hold)
- QTA-REM-002: Two-phase reservation commit (atomic settlement)
- QTA-REM-003: Two-phase reservation rollback on failure
- QTA-REM-004: Document upload limit enforcement (overdraft prevention)
- QTA-REM-005: File size limit enforcement (max 10MB)
- QTA-REM-006: Total storage limit enforcement (max 100MB)
- QTA-REM-007: Query quota limit enforcement (sliding window / daily limit)
- QTA-REM-008: Comparison quota limit enforcement
- QTA-REM-009: Concurrency race condition protection under parallel load
- QTA-REM-010: Idempotent settlement deduplication
- QTA-REM-011: Evaluator usage summary reporting (/v1/evaluation/usage)
- QTA-REM-012: Ledger auditability and counter reconciliation
"""

import concurrent.futures
import io
import uuid
import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.quotas import (
    quota_manager,
    QuotaExceededError,
)
from src.services.evaluation.quota_service import quota_service
from src.schemas.evaluation.usage_reservation import ReservationStatus


def test_qta_rem_001_capacity_reservation_holds_units():
    """QTA-REM-001: Two-phase reservation atomically holds capacity before execution."""
    lic_id = f"lic-res-{uuid.uuid4().hex[:8]}"
    quota_service.reset_usage(lic_id)

    res_id = quota_service.reserve_quota(lic_id, metric="queries", amount=3, max_limit=5)
    assert res_id is not None

    # Reserving 3 more when limit is 5 should fail because 3 are pending
    with pytest.raises(QuotaExceededError):
        quota_service.reserve_quota(lic_id, metric="queries", amount=3, max_limit=5)

    quota_service.reset_usage(lic_id)


def test_qta_rem_002_reservation_commit_settles_atomically():
    """QTA-REM-002: Settling a reservation commits actual usage into permanent accounting."""
    lic_id = f"lic-res-{uuid.uuid4().hex[:8]}"
    quota_service.reset_usage(lic_id)

    res_id = quota_service.reserve_quota(lic_id, metric="queries", amount=2, max_limit=10)
    quota_service.settle_quota(lic_id, reservation_id=res_id, actual_amount=2)

    status = quota_service.get_quota_status(lic_id, {"max_queries_per_day": 10})
    assert status["queries"]["used"] == 2
    assert status["queries"]["remaining"] == 8

    quota_service.reset_usage(lic_id)


def test_qta_rem_003_reservation_rollback_restores_capacity():
    """QTA-REM-003: Rolling back a failed operation releases reserved units."""
    lic_id = f"lic-res-{uuid.uuid4().hex[:8]}"
    quota_service.reset_usage(lic_id)

    res_id = quota_service.reserve_quota(lic_id, metric="queries", amount=5, max_limit=5)

    # Next reservation should fail
    with pytest.raises(QuotaExceededError):
        quota_service.reserve_quota(lic_id, metric="queries", amount=1, max_limit=5)

    # Roll back reservation
    quota_service.rollback_quota(lic_id, res_id)

    # Now reserving should succeed again
    res_id_2 = quota_service.reserve_quota(lic_id, metric="queries", amount=5, max_limit=5)
    assert res_id_2 is not None

    quota_service.reset_usage(lic_id)


def test_qta_rem_004_document_upload_limit_enforced():
    """QTA-REM-004: Exceeding document upload limit raises QuotaExceededError."""
    lic_id = f"lic-doc-{uuid.uuid4().hex[:8]}"
    quota_service.reset_usage(lic_id)

    # Upload max 3 documents
    for i in range(3):
        quota_service.record_document_upload(lic_id, doc_id=f"doc-{i}", file_size_bytes=1000, max_limit=3)

    # 4th upload must raise QuotaExceededError
    with pytest.raises(QuotaExceededError):
        quota_service.record_document_upload(lic_id, doc_id="doc-4", file_size_bytes=1000, max_limit=3)

    quota_service.reset_usage(lic_id)


def test_qta_rem_005_oversized_file_rejected():
    """QTA-REM-005: File exceeding maximum file size limit (10MB) is rejected."""
    lic_id = f"lic-file-{uuid.uuid4().hex[:8]}"
    quota_service.reset_usage(lic_id)

    oversized = 11 * 1024 * 1024  # 11 MB
    with pytest.raises(ValueError) as exc:
        quota_service.record_document_upload(lic_id, doc_id="doc-big", file_size_bytes=oversized)
    assert "exceeds maximum" in str(exc.value)

    quota_service.reset_usage(lic_id)


def test_qta_rem_006_total_storage_limit_enforced():
    """QTA-REM-006: Cumulative storage limit (100MB) is strictly enforced."""
    lic_id = f"lic-stor-{uuid.uuid4().hex[:8]}"
    quota_service.reset_usage(lic_id)

    # Simulate existing cumulative storage at 95MB across previous compliant uploads
    quota_manager._usage[lic_id].uploaded_bytes = 95 * 1024 * 1024

    # Uploading another 8MB (individually valid <= 10MB) will push total to 103MB (> 100MB)
    with pytest.raises(QuotaExceededError) as exc:
        quota_service.record_document_upload(lic_id, doc_id="doc-overflow", file_size_bytes=8 * 1024 * 1024, max_limit=20)
    assert exc.value.resource == "storage"

    quota_service.reset_usage(lic_id)


def test_qta_rem_007_query_quota_limit_enforced(client: TestClient, valid_eval_license):
    """QTA-REM-007: Exceeding daily query quota returns HTTP 429."""
    headers = valid_eval_license["headers"]
    lic_id = valid_eval_license["license_id"]
    quota_service.reset_usage(lic_id)

    # Fill 20 queries (limit is 20)
    for _ in range(20):
        quota_service.record_query(lic_id, max_limit=20)

    # 21st query must fail with 429
    res = client.post("/v1/evaluation/query", headers=headers, json={"query": "Exceeded query"})
    assert res.status_code == 429
    assert res.json()["error"] == "QUOTA_EXCEEDED"

    quota_service.reset_usage(lic_id)


def test_qta_rem_008_comparison_quota_limit_enforced():
    """QTA-REM-008: Comparison quota limit is enforced per evaluation license."""
    lic_id = f"lic-comp-{uuid.uuid4().hex[:8]}"
    quota_service.reset_usage(lic_id)

    for _ in range(5):
        quota_service.record_comparison(lic_id, max_limit=5)

    with pytest.raises(QuotaExceededError) as exc:
        quota_service.record_comparison(lic_id, max_limit=5)
    assert exc.value.resource == "comparisons"

    quota_service.reset_usage(lic_id)


def test_qta_rem_009_concurrency_race_condition_safe():
    """QTA-REM-009: Parallel reservations across quota boundary prevent race condition leaks."""
    lic_id = f"lic-conc-{uuid.uuid4().hex[:8]}"
    quota_service.reset_usage(lic_id)

    limit = 5
    concurrency = 15
    results = []

    def attempt_reserve():
        try:
            r_id = quota_service.reserve_quota(lic_id, metric="queries", amount=1, max_limit=limit)
            return ("SUCCESS", r_id)
        except QuotaExceededError:
            return ("QUOTA_EXCEEDED", None)

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(attempt_reserve) for _ in range(concurrency)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result()[0])

    successes = results.count("SUCCESS")
    exceeded = results.count("QUOTA_EXCEEDED")

    assert successes == limit
    assert exceeded == (concurrency - limit)

    quota_service.reset_usage(lic_id)


def test_qta_rem_010_idempotent_settlement_deduplication():
    """QTA-REM-010: Repeating settlement on the same reservation does not double-charge."""
    lic_id = f"lic-idem-{uuid.uuid4().hex[:8]}"
    quota_service.reset_usage(lic_id)

    res_id = quota_service.reserve_quota(lic_id, metric="queries", amount=1, max_limit=5)
    quota_service.settle_quota(lic_id, reservation_id=res_id, actual_amount=1)

    # Repeat settlement (should be no-op, not add more used queries)
    quota_service.settle_quota(lic_id, reservation_id=res_id, actual_amount=1)

    status = quota_service.get_quota_status(lic_id, {"max_queries_per_day": 5})
    assert status["queries"]["used"] == 1
    assert status["queries"]["remaining"] == 4

    quota_service.reset_usage(lic_id)


def test_qta_rem_011_evaluator_usage_summary_reporting(client: TestClient, valid_eval_license):
    """QTA-REM-011: GET /v1/evaluation/usage returns accurate utilization and limits."""
    headers = valid_eval_license["headers"]
    lic_id = valid_eval_license["license_id"]
    quota_service.reset_usage(lic_id)

    # Record 1 query and 1 upload
    quota_service.record_query(lic_id)
    quota_service.record_document_upload(lic_id, doc_id="doc-report-1", file_size_bytes=1024)

    res = client.get("/v1/evaluation/usage", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "documents" in data
    assert "queries" in data
    assert "comparisons" in data
    assert "storage_bytes" in data

    assert data["documents"]["used"] >= 1
    assert data["queries"]["used"] >= 1

    quota_service.reset_usage(lic_id)


def test_qta_rem_012_usage_ledger_auditability_reconciliation():
    """QTA-REM-012: Ledger events recorded in UsageEventRepository match counter consumption."""
    lic_id = f"lic-audit-{uuid.uuid4().hex[:8]}"
    quota_service.reset_usage(lic_id)

    quota_service.record_query(lic_id, max_limit=10)
    quota_service.record_query(lic_id, max_limit=10)
    quota_service.record_comparison(lic_id, max_limit=5)

    events = quota_manager.event_repo.list_events(lic_id)
    query_events = [e for e in events if e.quota_key == "queries"]
    comp_events = [e for e in events if e.quota_key == "comparisons"]

    assert len(query_events) == 2
    assert len(comp_events) == 1

    quota_service.reset_usage(lic_id)
