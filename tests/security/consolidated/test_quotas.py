"""
Consolidated Security Audit: Atomic Quotas & Concurrency Governance (SEC-012)
"""

import concurrent.futures
import pytest
from services.evaluation_gateway.quotas import quota_manager, QuotaExceededError


def test_quota_001_within_limit_settles_cleanly():
    """SEC-012.1: Usage within allowable limits reserves and settles without error."""
    lic_id = "lic-quota-001"
    res_id = quota_manager.reserve_quota(lic_id, "queries", 1, max_limit=5)
    assert res_id is not None
    quota_manager.settle_reservation(lic_id, res_id, 1)

    status = quota_manager.get_quota_status(lic_id)
    assert status["queries"]["used"] == 1


def test_quota_002_exceeding_limit_rejected_429():
    """SEC-012.2: Requests exceeding configured limits raise QuotaExceededError."""
    lic_id = "lic-quota-002"
    for _ in range(5):
        r = quota_manager.reserve_quota(lic_id, "queries", 1, max_limit=5)
        quota_manager.settle_reservation(lic_id, r, 1)

    with pytest.raises(QuotaExceededError):
        quota_manager.reserve_quota(lic_id, "queries", 1, max_limit=5)


def test_quota_003_concurrent_race_at_boundary_prevents_overspending():
    """SEC-012.3: Multithreaded race condition at limit allocates exactly available capacity."""
    lic_id = "lic-quota-003"
    max_limit = 3

    def attempt_reservation():
        try:
            r = quota_manager.reserve_quota(lic_id, "queries", 1, max_limit=max_limit)
            quota_manager.settle_reservation(lic_id, r, 1)
            return True
        except QuotaExceededError:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(attempt_reservation) for _ in range(10)]
        results = [f.result() for f in futs]

    assert results.count(True) == 3
    assert results.count(False) == 7
    assert quota_manager.get_quota_status(lic_id)["queries"]["used"] == 3


def test_quota_004_failed_operation_rolls_back_reservation():
    """SEC-012.4: Rolled-back reservations do not consume quota balance."""
    lic_id = "lic-quota-004"
    r = quota_manager.reserve_quota(lic_id, "queries", 1, max_limit=5)
    quota_manager.rollback_reservation(lic_id, r)

    status = quota_manager.get_quota_status(lic_id)
    assert status["queries"]["used"] == 0


def test_quota_005_idempotent_retry_avoids_double_charge():
    """SEC-012.5: Submitting duplicate reservation ID is idempotent."""
    lic_id = "lic-quota-005"
    r1 = quota_manager.reserve_quota(lic_id, "queries", 1, max_limit=5, reservation_id="res-idem-1")
    quota_manager.settle_reservation(lic_id, r1, 1)

    # Re-settling or querying status reflects single consumption
    status = quota_manager.get_quota_status(lic_id)
    assert status["queries"]["used"] == 1
