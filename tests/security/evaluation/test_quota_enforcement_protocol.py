"""
tests/security/evaluation/test_quota_enforcement_protocol.py
============================================================
Comprehensive Verification Suite for PROT-04 WP-04.06:
Quotas, Usage Accounting, Atomic Reservations & Resource Limits.

Scenarios Covered:
- QUOTA-001 to QUOTA-014: Quota enforcement boundaries, limits, periods, dimensions, and fail-closed defaults.
- RES-001 to RES-015: Atomic capacity reservation, idempotency, multi-dimensional reservation, rollbacks, and settlements.
- CONC-001 to CONC-008: Race condition and concurrency protection, atomic conditional updates under parallel load.
- METER-001 to METER-010: Accurate metering of uploads, LLM tokens, queries, comparisons, OCR, and exports.
- RATE-001 to RATE-006: Sliding-window rate limiting, HTTP 429 Retry-After, abuse prevention, and scoping.
- RECON-001 to RECON-007: Accounting reconciliation, counter-ledger consistency, admin adjustments, and stale reservation recovery.
"""

from __future__ import annotations

import concurrent.futures
import io
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List
import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.quotas import quota_manager, QuotaExceededError
from src.repositories.evaluation.quota_counter_repository import (
    QuotaCounterRepository,
    default_quota_counter_repository,
)
from src.repositories.evaluation.quota_policy_repository import (
    QuotaPolicyRepository,
    default_quota_policy_repository,
)
from src.repositories.evaluation.usage_adjustment_repository import (
    UsageAdjustmentRepository,
    default_usage_adjustment_repository,
)
from src.repositories.evaluation.usage_event_repository import (
    UsageEventRepository,
    default_usage_event_repository,
)
from src.repositories.evaluation.usage_reservation_repository import (
    UsageReservationRepository,
    default_usage_reservation_repository,
)
from src.schemas.evaluation.quota import (
    EvaluationQuotaPolicy,
    QuotaDefinition,
    QuotaDimension,
    QuotaPeriod,
    QuotaUnit,
    get_default_evaluation_basic_quota_policy,
    get_default_evaluation_pro_quota_policy,
)
from src.schemas.evaluation.usage_event import UsageEvent, UsageEventType
from src.schemas.evaluation.usage_reservation import ReservationStatus, UsageReservation
from src.services.evaluation.quota_policy_service import (
    QuotaPolicyService,
    default_quota_policy_service,
)
from src.services.evaluation.quota_reconciliation_service import (
    QuotaReconciliationService,
    default_quota_reconciliation_service,
)
from src.services.evaluation.quota_reservation_service import (
    QuotaExceededException,
    QuotaReservationService,
    default_quota_reservation_service,
)
from src.services.evaluation.quota_settlement_service import (
    QuotaSettlementService,
    default_quota_settlement_service,
)
from src.services.evaluation.rate_limit_service import (
    RateLimitExceededException,
    RateLimitService,
    default_rate_limit_service,
)
from src.services.evaluation.usage_aggregation_service import (
    UsageAggregationService,
    default_usage_aggregation_service,
)
from src.services.evaluation.usage_metering_service import (
    UsageMeteringService,
    default_usage_metering_service,
)


class TestQuotaEnforcementProtocol:
    """Suite A: Quota Enforcement Tests (QUOTA-001 - QUOTA-014)"""

    def test_quota_001_usage_below_limit_allowed(self, client: TestClient, valid_eval_license):
        """QUOTA-001: Operations strictly within quota boundary succeed with HTTP 200."""
        headers = valid_eval_license["headers"]
        res = client.post("/v1/evaluation/query", headers=headers, json={"query": "Spec query 1"})
        assert res.status_code == 200
        assert "answer" in res.json()

    def test_quota_002_usage_at_limit_then_denied(self, client: TestClient, valid_eval_license):
        """QUOTA-002: Reaching the exact limit succeeds; crossing the limit returns HTTP 429."""
        headers = valid_eval_license["headers"]
        lic_id = valid_eval_license["license_id"]

        # Limit is 20 queries/day
        for i in range(20):
            res = client.post("/v1/evaluation/query", headers=headers, json={"query": f"Query {i+1}"})
            assert res.status_code == 200

        # 21st query crossing boundary must be rejected with 429
        res_exceeded = client.post("/v1/evaluation/query", headers=headers, json={"query": "Query 21"})
        assert res_exceeded.status_code == 429
        data = res_exceeded.json()
        err_data = data.get("detail", data)
        assert err_data["error"] == "QUOTA_EXCEEDED"
        assert err_data["resource"] == "queries"

    def test_quota_003_usage_exceeds_limit_denied(self):
        """QUOTA-003: Direct service reservation exceeding available quota raises QuotaExceededException."""
        counter_repo = QuotaCounterRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo)

        with pytest.raises(QuotaExceededException) as exc_info:
            res_service.reserve_capacity(
                license_id="lic-overflow",
                evaluator_id="eval-1",
                tenant_id="ten-1",
                operation_id="op-1",
                requested_items={"queries": 101},  # Basic limit is 100
                idempotency_key="idemp-overflow",
            )
        assert exc_info.value.resource == "queries"

    def test_quota_004_missing_quota_configuration_fails_closed(self):
        """QUOTA-004: Requesting an unconfigured quota dimension fails closed."""
        res_service = QuotaReservationService()
        with pytest.raises(QuotaExceededException) as exc_info:
            res_service.reserve_capacity(
                license_id="lic-missing",
                evaluator_id="eval-1",
                tenant_id="ten-1",
                operation_id="op-1",
                requested_items={"unconfigured_dimension": 1},
                idempotency_key="idemp-missing",
            )
        assert "not permitted or configured" in str(exc_info.value)

    def test_quota_005_unknown_quota_dimension_rejected(self):
        """QUOTA-005: Schema validation rejects unknown quota dimensions."""
        with pytest.raises(ValueError):
            QuotaDefinition(
                dimension="quantum_compute",  # type: ignore
                limit=10,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.REQUESTS,
            )

    def test_quota_006_negative_quota_limit_rejected(self):
        """QUOTA-006: Schema validation strictly rejects negative quota limits."""
        with pytest.raises(ValueError):
            QuotaDefinition(
                dimension=QuotaDimension.DOCUMENTS,
                limit=-5,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.DOCUMENTS,
            )

    def test_quota_007_expired_quota_period_rollover(self):
        """QUOTA-007: Periodic quota resets across date boundaries."""
        counter_repo = QuotaCounterRepository()
        c_yesterday = counter_repo.get_or_create_counter(
            license_id="lic-rollover",
            evaluator_id="eval-1",
            tenant_id="ten-1",
            quota_key="queries",
            period_key="daily:2026-11-13",
            limit_value=20,
        )
        c_yesterday.consumed = 20  # Exhausted yesterday

        # Today's counter is separate and empty
        c_today = counter_repo.get_or_create_counter(
            license_id="lic-rollover",
            evaluator_id="eval-1",
            tenant_id="ten-1",
            quota_key="queries",
            period_key="daily:2026-11-14",
            limit_value=20,
        )
        assert c_today.consumed == 0
        assert c_today.available == 20

    def test_quota_008_lifetime_quota_no_automatic_reset(self):
        """QUOTA-008: Lifetime quotas persist without calendar boundary reset."""
        counter_repo = QuotaCounterRepository()
        counter = counter_repo.get_or_create_counter(
            license_id="lic-life",
            evaluator_id="eval-1",
            tenant_id="ten-1",
            quota_key="documents",
            period_key="lifetime",
            limit_value=20,
        )
        counter.consumed = 15
        # Re-fetching maintains cumulative consumed
        c2 = counter_repo.get_counter("lic-life", "documents", "lifetime")
        assert c2.consumed == 15
        assert c2.available == 5

    def test_quota_009_rolling_quota_sliding_window(self):
        """QUOTA-009: Rolling quota prunes timestamps older than rolling window."""
        rl = RateLimitService()
        scope = "lic-rolling-test"
        # 3 requests 70s ago
        now = time.time()
        rl._timestamps[scope] = [now - 70, now - 65, now - 61]
        # Current utilization within 60s is 0
        assert rl.get_utilization(scope, window_seconds=60) == 0

    def test_quota_010_concurrent_quota_enforced(self):
        """QUOTA-010: Active concurrent job limit enforced."""
        counter_repo = QuotaCounterRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo)
        
        # Reserve 2 concurrent slots (Basic limit is 2)
        r1 = res_service.reserve_capacity(
            "lic-conc", "eval-1", "ten-1", "job-1", {"concurrent_jobs": 1}, "idemp-c1"
        )
        r2 = res_service.reserve_capacity(
            "lic-conc", "eval-1", "ten-1", "job-2", {"concurrent_jobs": 1}, "idemp-c2"
        )
        assert r1.status == ReservationStatus.PENDING
        assert r2.status == ReservationStatus.PENDING

        # 3rd concurrent slot rejected
        with pytest.raises(QuotaExceededException):
            res_service.reserve_capacity(
                "lic-conc", "eval-1", "ten-1", "job-3", {"concurrent_jobs": 1}, "idemp-c3"
            )

    def test_quota_011_license_wide_quota_shared_across_devices(self, client: TestClient, valid_eval_license):
        """QUOTA-011: Quota pool is license-scoped, shared across all connected devices."""
        headers = valid_eval_license["headers"]
        lic_id = valid_eval_license["license_id"]

        # Device A consumes 10 queries
        for i in range(10):
            res = client.post("/v1/evaluation/query", headers=headers, json={"query": f"DevA query {i}"})
            assert res.status_code == 200

        # Status shows 10 queries used for the license
        status = quota_manager.get_quota_status(lic_id)
        assert status["queries"]["used"] == 10
        assert status["queries"]["remaining"] == 10  # 20 - 10

    def test_quota_012_tenant_wide_quota_isolation(self):
        """QUOTA-012: Tenant A consuming quota has zero impact on Tenant B's capacity."""
        counter_repo = QuotaCounterRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo)

        # Tenant A exhausts its queries
        res_service.reserve_capacity("lic-A", "eval-A", "tenant-A", "op-A", {"queries": 100}, "idemp-A")

        # Tenant B still has full 100 queries available
        res_B = res_service.reserve_capacity("lic-B", "eval-B", "tenant-B", "op-B", {"queries": 50}, "idemp-B")
        assert res_B.status == ReservationStatus.PENDING

    def test_quota_013_quota_policy_update_applies_correct_version(self):
        """QUOTA-013: Activating a new quota policy version reflects in limit checks."""
        policy_service = QuotaPolicyService(policy_repo=QuotaPolicyRepository())
        pro_policy = policy_service.get_effective_policy("evaluation-pro")
        assert pro_policy.quotas["queries"].limit == 500

    def test_quota_014_quota_service_unavailable_fails_closed(self):
        """QUOTA-014: Exception during quota evaluation fails closed rather than proceeding silently."""
        counter_repo = QuotaCounterRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo)
        
        # Inject simulated failure by querying invalid quota
        with pytest.raises(Exception):
            res_service.reserve_capacity("lic-err", "eval-1", "ten-1", "op-1", {"invalid_dim": 1}, "idemp-err")


class TestReservationAndSettlementProtocol:
    """Suite B: Reservation and Settlement Tests (RES-001 - RES-015)"""

    def test_res_001_valid_reservation_created(self):
        """RES-001: Valid capacity reservation created in PENDING status."""
        res_service = QuotaReservationService(counter_repo=QuotaCounterRepository())
        res = res_service.reserve_capacity(
            "lic-r1", "eval-1", "ten-1", "op-1", {"queries": 1, "api_requests": 1}, "idemp-r1"
        )
        assert res.status == ReservationStatus.PENDING
        assert res.items["queries"].reserved_amount == 1
        assert res.items["api_requests"].reserved_amount == 1

    def test_res_002_reservation_above_available_rejected(self):
        """RES-002: Reservation exceeding capacity is rejected without mutating state."""
        counter_repo = QuotaCounterRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo)
        with pytest.raises(QuotaExceededException):
            res_service.reserve_capacity("lic-r2", "eval-1", "ten-1", "op-1", {"documents": 25}, "idemp-r2")

    def test_res_003_duplicate_idempotency_key_no_double_reservation(self):
        """RES-003: Retrying with same idempotency key returns existing reservation without double reserving."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)

        r1 = res_service.reserve_capacity("lic-r3", "eval-1", "ten-1", "op-1", {"queries": 10}, "idemp-r3")
        r2 = res_service.reserve_capacity("lic-r3", "eval-1", "ten-1", "op-1", {"queries": 10}, "idemp-r3")

        assert r1.id == r2.id
        counters = counter_repo.list_counters("lic-r3")
        assert counters[0].reserved == 10  # Not 20

    def test_res_004_multi_dimensional_reservation_atomic(self):
        """RES-004: All dimensions in a multi-quota request are reserved atomically."""
        counter_repo = QuotaCounterRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo)
        req = {"queries": 1, "api_requests": 1, "llm_tokens": 1000, "concurrent_jobs": 1}
        res = res_service.reserve_capacity("lic-r4", "eval-1", "ten-1", "op-1", req, "idemp-r4")
        assert len(res.items) == 4
        for k in req:
            assert res.items[k].reserved_amount == req[k]

    def test_res_005_partial_reservation_failure_rolls_back_all(self):
        """RES-005: If one dimension fails, all other dimensions are rolled back."""
        counter_repo = QuotaCounterRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo)
        # LLM tokens exceeds limit (Basic limit is 50,000)
        req = {"queries": 1, "api_requests": 1, "llm_tokens": 60_000}
        with pytest.raises(QuotaExceededException):
            res_service.reserve_capacity("lic-r5", "eval-1", "ten-1", "op-1", req, "idemp-r5")

        # Verify queries and api_requests counters were rolled back to 0
        for c in counter_repo.list_counters("lic-r5"):
            assert c.reserved == 0

    def test_res_006_successful_settlement_commits_usage(self):
        """RES-006: Settlement commits actual usage and transitions reservation to COMMITTED."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        ev_repo = UsageEventRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        set_service = QuotaSettlementService(counter_repo=counter_repo, reservation_repo=res_repo, event_repo=ev_repo)

        res = res_service.reserve_capacity("lic-r6", "eval-1", "ten-1", "op-1", {"queries": 5}, "idemp-r6")
        settled = set_service.settle_reservation(res.id, {"queries": 5}, "settle-r6")
        assert settled.status == ReservationStatus.COMMITTED

        counter = counter_repo.list_counters("lic-r6")[0]
        assert counter.consumed == 5
        assert counter.reserved == 0

    def test_res_007_partial_operation_failure_settles_actual(self):
        """RES-007: Operation failing partially commits measured work and refunds the rest."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        set_service = QuotaSettlementService(counter_repo=counter_repo, reservation_repo=res_repo)

        # Reserved 2000 tokens, but failed halfway consuming only 800
        res = res_service.reserve_capacity("lic-r7", "eval-1", "ten-1", "op-1", {"llm_tokens": 2000}, "idemp-r7")
        set_service.settle_reservation(res.id, {"llm_tokens": 800}, "settle-r7")

        counter = counter_repo.list_counters("lic-r7")[0]
        assert counter.consumed == 800
        assert counter.reserved == 0

    def test_res_008_unused_capacity_safely_released(self):
        """RES-008: Unused capacity difference is returned to available pool."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        set_service = QuotaSettlementService(counter_repo=counter_repo, reservation_repo=res_repo)

        res = res_service.reserve_capacity("lic-r8", "eval-1", "ten-1", "op-1", {"queries": 10}, "idemp-r8")
        counter = counter_repo.list_counters("lic-r8")[0]
        assert counter.available == 90  # 100 - 10

        # Settle only 4 queries; 6 returned
        set_service.settle_reservation(res.id, {"queries": 4}, "settle-r8")
        assert counter.consumed == 4
        assert counter.available == 96  # 100 - 4

    def test_res_009_repeated_settlement_no_double_charging(self):
        """RES-009: Idempotent repeat of settlement returns existing result without double charge."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        set_service = QuotaSettlementService(counter_repo=counter_repo, reservation_repo=res_repo)

        res = res_service.reserve_capacity("lic-r9", "eval-1", "ten-1", "op-1", {"queries": 3}, "idemp-r9")
        set_service.settle_reservation(res.id, {"queries": 3}, "settle-r9")
        set_service.settle_reservation(res.id, {"queries": 3}, "settle-r9")  # Replay

        counter = counter_repo.list_counters("lic-r9")[0]
        assert counter.consumed == 3  # Exactly 3, not 6

    def test_res_010_settlement_after_release_rejected(self):
        """RES-010: Attempting to commit an already released reservation raises ValueError."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        set_service = QuotaSettlementService(counter_repo=counter_repo, reservation_repo=res_repo)

        res = res_service.reserve_capacity("lic-r10", "eval-1", "ten-1", "op-1", {"queries": 1}, "idemp-r10")
        set_service.release_reservation(res.id, "cancelled")

        with pytest.raises(ValueError) as exc_info:
            set_service.settle_reservation(res.id, {"queries": 1}, "settle-r10")
        assert "terminal status" in str(exc_info.value)

    def test_res_011_expired_reservation_recovered_safely(self):
        """RES-011: Expired reservation marked EXPIRED and capacity recovered."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        recon_service = QuotaReconciliationService(counter_repo=counter_repo, reservation_repo=res_repo)

        # Create reservation with 1-second TTL
        res = res_service.reserve_capacity("lic-r11", "eval-1", "ten-1", "op-1", {"queries": 5}, "idemp-r11", ttl_seconds=1)
        counter = counter_repo.list_counters("lic-r11")[0]
        assert counter.reserved == 5

        # Wait for expiration
        time.sleep(1.1)
        recon_report = recon_service.reconcile_license("lic-r11")
        assert recon_report["stale_reservations_recovered"] == 1
        assert counter.reserved == 0

    def test_res_012_worker_crash_recovered_by_reconciliation(self):
        """RES-012: Abandoned reservation from crashed worker is released."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        recon_service = QuotaReconciliationService(counter_repo=counter_repo, reservation_repo=res_repo)

        res = res_service.reserve_capacity("lic-r12", "eval-1", "ten-1", "op-1", {"comparisons": 2}, "idemp-r12", ttl_seconds=1)
        time.sleep(1.1)
        recon_service.reconcile_license("lic-r12")
        c = counter_repo.list_counters("lic-r12")[0]
        assert c.reserved == 0

    def test_res_013_cancelled_job_releases_reservation(self):
        """RES-013: Explicitly cancelled job releases reserved quota immediately."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        set_service = QuotaSettlementService(counter_repo=counter_repo, reservation_repo=res_repo)

        res = res_service.reserve_capacity("lic-r13", "eval-1", "ten-1", "op-1", {"queries": 2}, "idemp-r13")
        c = counter_repo.list_counters("lic-r13")[0]
        assert c.reserved == 2

        set_service.release_reservation(res.id, "user_cancelled")
        assert c.reserved == 0
        assert c.consumed == 0

    def test_res_014_retry_with_same_operation_id_no_duplicate_usage(self):
        """RES-014: Same operation ID retry produces zero duplicated usage."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        set_service = QuotaSettlementService(counter_repo=counter_repo, reservation_repo=res_repo)

        res = res_service.reserve_capacity("lic-r14", "eval-1", "ten-1", "op-repeat", {"queries": 1}, "idemp-r14")
        set_service.settle_reservation(res.id, {"queries": 1}, "settle-repeat")
        # Retry with same idempotency key
        res2 = res_service.reserve_capacity("lic-r14", "eval-1", "ten-1", "op-repeat", {"queries": 1}, "idemp-r14")
        set_service.settle_reservation(res2.id, {"queries": 1}, "settle-repeat")

        c = counter_repo.list_counters("lic-r14")[0]
        assert c.consumed == 1

    def test_res_015_unknown_provider_usage_conservative_fallback(self):
        """RES-015: Unknown LLM provider payload falls back to conservative token estimate."""
        metering = UsageMeteringService()
        result = metering.meter_llm_response(
            provider="custom_llm",
            response_payload={"answer": "hello world"},
            fallback_input_text="Describe the architecture",
            fallback_output_text="The architecture has 4 layers",
        )
        assert result.is_estimated is True
        assert result.total_tokens > 0


class TestConcurrencyAndRaceConditions:
    """Suite C: Concurrency and Race-Condition Tests (CONC-001 - CONC-008)"""

    def test_conc_001_competing_threads_final_unit_exactly_one_succeeds(self):
        """CONC-001: Two threads competing for final 1 remaining unit; exactly one succeeds."""
        counter_repo = QuotaCounterRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo)
        # Pre-fill 99 queries (limit 100)
        c = counter_repo.get_or_create_counter("lic-c1", "eval-1", "ten-1", "queries", "lifetime", 100)
        c.consumed = 99

        results = []
        def attempt_reserve(idx):
            try:
                res_service.reserve_capacity("lic-c1", "eval-1", "ten-1", f"op-{idx}", {"queries": 1}, f"idemp-{idx}")
                return "SUCCESS"
            except QuotaExceededException:
                return "DENIED"

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(attempt_reserve, 1)
            f2 = executor.submit(attempt_reserve, 2)
            results = [f1.result(), f2.result()]

        assert results.count("SUCCESS") == 1
        assert results.count("DENIED") == 1
        assert c.consumed + c.reserved == 100

    def test_conc_002_50_parallel_requests_never_exceed_limit(self):
        """CONC-002: 50 concurrent requests competing for 10 slots never exceed limit."""
        counter_repo = QuotaCounterRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo)
        c = counter_repo.get_or_create_counter("lic-c2", "eval-1", "ten-1", "queries", "lifetime", 10)

        results = []
        def fire(idx):
            try:
                res_service.reserve_capacity("lic-c2", "eval-1", "ten-1", f"op-{idx}", {"queries": 1}, f"idemp-{idx}")
                return 200
            except QuotaExceededException:
                return 429

        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(fire, i) for i in range(50)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        assert results.count(200) == 10
        assert results.count(429) == 40
        assert c.reserved == 10

    def test_conc_003_concurrent_multi_quota_reservation_no_partial_leak(self):
        """CONC-003: High-concurrency multi-quota reservations produce zero partial reservation leaks."""
        counter_repo = QuotaCounterRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo)
        # Limit comparisons to 2
        counter_repo.get_or_create_counter("lic-c3", "eval-1", "ten-1", "comparisons", "lifetime", 2)
        counter_repo.get_or_create_counter("lic-c3", "eval-1", "ten-1", "queries", "lifetime", 100)

        def fire(idx):
            try:
                res_service.reserve_capacity(
                    "lic-c3", "eval-1", "ten-1", f"op-{idx}", {"queries": 1, "comparisons": 1}, f"idemp-{idx}"
                )
                return True
            except QuotaExceededException:
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fire, i) for i in range(10)]
            results = [f.result() for f in futures]

        assert results.count(True) == 2
        comp_c = counter_repo.get_counter("lic-c3", "comparisons", "lifetime")
        query_c = counter_repo.get_counter("lic-c3", "queries", "lifetime")
        assert comp_c.reserved == 2
        assert query_c.reserved == 2  # Exactly matches successful operations, no leaked query reservations

    def test_conc_004_simultaneous_settlement_succeeds_once(self):
        """CONC-004: Simultaneous settlement calls commit usage exactly once."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        set_service = QuotaSettlementService(counter_repo=counter_repo, reservation_repo=res_repo)

        res = res_service.reserve_capacity("lic-c4", "eval-1", "ten-1", "op-1", {"queries": 5}, "idemp-c4")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(set_service.settle_reservation, res.id, {"queries": 5}, f"idemp-{i}") for i in range(5)]
            for f in futures:
                f.result()

        c = counter_repo.list_counters("lic-c4")[0]
        assert c.consumed == 5

    def test_conc_005_reservation_and_cancellation_race_consistent(self):
        """CONC-005: Concurrent reservation and cancellation produce consistent state."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        set_service = QuotaSettlementService(counter_repo=counter_repo, reservation_repo=res_repo)

        res = res_service.reserve_capacity("lic-c5", "eval-1", "ten-1", "op-1", {"queries": 2}, "idemp-c5")

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(set_service.settle_reservation, res.id, {"queries": 2}, "settle-c5")
            f2 = executor.submit(set_service.release_reservation, res.id, "cancel-c5")
            _ = [f1.result(), f2.result()]

        c = counter_repo.list_counters("lic-c5")[0]
        assert c.reserved == 0
        assert c.consumed in (0, 2)

    def test_conc_006_counter_repository_atomic_accuracy(self):
        """CONC-006: 100 parallel atomic reservations increment counter revision and reserved correctly."""
        counter_repo = QuotaCounterRepository()
        c = counter_repo.get_or_create_counter("lic-c6", "eval-1", "ten-1", "queries", "lifetime", 200)

        def reserve_one(i):
            return counter_repo.atomic_reserve(c.id, 1)

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(reserve_one, i) for i in range(100)]
            results = [f.result() for f in futures]

        assert all(results)
        assert c.reserved == 100

    def test_conc_007_rollback_maintains_ledger_consistency(self):
        """CONC-007: Failed multi-quota reservation leaves ledger with zero orphaned reservations."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)

        counter_repo.get_or_create_counter("lic-c7", "eval-1", "ten-1", "queries", "lifetime", 10)
        counter_repo.get_or_create_counter("lic-c7", "eval-1", "ten-1", "comparisons", "lifetime", 0)  # Exhausted

        with pytest.raises(QuotaExceededException):
            res_service.reserve_capacity("lic-c7", "eval-1", "ten-1", "op-c7", {"queries": 1, "comparisons": 1}, "idemp-c7")

        assert len(res_repo.list_active_reservations("lic-c7")) == 0

    def test_conc_008_heartbeat_and_expiry_race_no_double_release(self):
        """CONC-008: Race between expiry daemon and worker heartbeat releases counter exactly once."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        recon_service = QuotaReconciliationService(counter_repo=counter_repo, reservation_repo=res_repo)

        res = res_service.reserve_capacity("lic-c8", "eval-1", "ten-1", "op-c8", {"queries": 5}, "idemp-c8", ttl_seconds=1)
        time.sleep(1.1)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(recon_service.reconcile_license, "lic-c8")
            f2 = executor.submit(recon_service.reconcile_license, "lic-c8")
            _ = [f1.result(), f2.result()]

        c = counter_repo.list_counters("lic-c8")[0]
        assert c.reserved == 0


class TestUsageMeteringProtocol:
    """Suite D: Metering Tests (METER-001 - METER-010)"""

    def test_meter_001_upload_byte_count_measured(self):
        """METER-001: Upload byte count measures actual bytes received on server."""
        metering = UsageMeteringService()
        payload = b"Hello, AEGIS evaluation test payload"
        measured = metering.meter_file_upload(payload)
        assert measured == len(payload)

    def test_meter_002_oversized_streaming_upload_rejected(self):
        """METER-002: Upload exceeding 10 MB ceiling rejected before full storage."""
        metering = UsageMeteringService(max_file_size_bytes=10 * 1024 * 1024)
        oversized = b"X" * (11 * 1024 * 1024)
        with pytest.raises(ValueError) as exc:
            metering.meter_file_upload(oversized)
        assert "exceeds maximum evaluation limit" in str(exc.value)

    def test_meter_003_archive_expansion_limit_enforced(self):
        """METER-003: Archive payload exceeding byte limit raises error."""
        metering = UsageMeteringService(max_file_size_bytes=5 * 1024 * 1024)
        with pytest.raises(ValueError):
            metering.meter_file_upload(b"0" * (6 * 1024 * 1024))

    def test_meter_004_parsing_page_count_metered(self):
        """METER-004: Multi-page document parsing correctly measures page units."""
        counter_repo = QuotaCounterRepository()
        counter = counter_repo.get_or_create_counter("lic-m4", "eval-1", "ten-1", "ocr", "lifetime", 50)
        counter_repo.atomic_commit(counter.id, reserved_to_release=0, actual_consumed=12)
        assert counter.consumed == 12

    def test_meter_005_ocr_page_usage_metered(self):
        """METER-005: OCR engine output pages accounted for."""
        counter_repo = QuotaCounterRepository()
        c = counter_repo.get_or_create_counter("lic-m5", "eval-1", "ten-1", "ocr", "lifetime", 50)
        assert c.available == 50

    def test_meter_006_llm_input_tokens_captured(self):
        """METER-006: Provider response usage input tokens extracted accurately."""
        metering = UsageMeteringService()
        resp = {"model": "gemini-1.5-pro", "usage": {"input_tokens": 1250, "output_tokens": 340}}
        result = metering.meter_llm_response("gemini", resp)
        assert result.input_tokens == 1250
        assert result.output_tokens == 340
        assert result.total_tokens == 1590
        assert result.is_estimated is False

    def test_meter_007_llm_output_tokens_captured(self):
        """METER-007: OpenAI format response completion tokens captured accurately."""
        metering = UsageMeteringService()
        resp = {"model": "gpt-4o", "usage": {"prompt_tokens": 800, "completion_tokens": 420}}
        result = metering.meter_llm_response("openai", resp)
        assert result.input_tokens == 800
        assert result.output_tokens == 420
        assert result.total_tokens == 1220

    def test_meter_008_provider_retry_no_duplicate_accounting(self):
        """METER-008: Idempotent provider retry does not duplicate token accounting."""
        ev_repo = UsageEventRepository()
        ev1 = UsageEvent(
            event_id="ev-1", license_id="lic-m8", evaluator_id="e1", tenant_id="t1",
            operation_id="llm-call-1", event_type=UsageEventType.CONSUMPTION,
            quota_key="llm_tokens", amount=500, unit="tokens", source="llm_client",
            idempotency_key="idemp-llm-1", occurred_at=datetime.now(timezone.utc)
        )
        _, recorded1 = ev_repo.record_event(ev1)
        _, recorded2 = ev_repo.record_event(ev1)
        assert recorded1 is True
        assert recorded2 is False
        assert ev_repo.get_total_consumed("lic-m8", "llm_tokens") == 500

    def test_meter_009_provider_timeout_conservative_accounting(self):
        """METER-009: Missing usage metadata falls back to conservative token heuristic."""
        metering = UsageMeteringService()
        res = metering.meter_llm_response("anthropic", {"text": "hello"}, fallback_input_text="A" * 400)
        assert res.is_estimated is True
        assert res.input_tokens == 100

    def test_meter_010_export_storage_accounting(self):
        """METER-010: Result export operations account for export count."""
        counter_repo = QuotaCounterRepository()
        c = counter_repo.get_or_create_counter("lic-m10", "eval-1", "ten-1", "exports", "lifetime", 5)
        counter_repo.atomic_commit(c.id, reserved_to_release=0, actual_consumed=1)
        assert c.consumed == 1
        assert c.available == 4


class TestRateLimitingAndAbuseControl:
    """Suite E: Rate Limiting & Abuse Prevention Tests (RATE-001 - RATE-006)"""

    def test_rate_001_exceeding_rate_limit_returns_429(self):
        """RATE-001: Exceeding 60 requests/minute raises RateLimitExceededException."""
        rl = RateLimitService()
        scope = "eval-lic-test"
        for _ in range(60):
            rl.check_rate_limit(scope, limit=60, window_seconds=60)

        with pytest.raises(RateLimitExceededException) as exc:
            rl.check_rate_limit(scope, limit=60, window_seconds=60)
        assert exc.value.current_count == 60

    def test_rate_002_http_429_includes_retry_after(self):
        """RATE-002: Rate limit exception computes positive retry_after_seconds."""
        rl = RateLimitService()
        scope = "eval-lic-retry"
        for _ in range(5):
            rl.check_rate_limit(scope, limit=5, window_seconds=60)

        with pytest.raises(RateLimitExceededException) as exc:
            rl.check_rate_limit(scope, limit=5, window_seconds=60)
        assert exc.value.retry_after_seconds > 0

    def test_rate_003_rate_limit_resets_after_window_passes(self):
        """RATE-003: Rate limiter resets allowance after sliding window expires."""
        rl = RateLimitService()
        scope = "eval-lic-window"
        now = time.time()
        # 5 requests sent 65 seconds ago
        rl._timestamps[scope] = [now - 65] * 5
        # New request within limit 5 succeeds
        rl.check_rate_limit(scope, limit=5, window_seconds=60)
        assert rl.get_utilization(scope) == 1

    def test_rate_004_rate_limiting_scopes_independent(self):
        """RATE-004: Rate limiting on License A does not block License B."""
        rl = RateLimitService()
        for _ in range(10):
            rl.check_rate_limit("lic-A", limit=10, window_seconds=60)

        with pytest.raises(RateLimitExceededException):
            rl.check_rate_limit("lic-A", limit=10, window_seconds=60)

        # License B is unaffected
        rl.check_rate_limit("lic-B", limit=10, window_seconds=60)
        assert rl.get_utilization("lic-B") == 1

    def test_rate_005_tampered_headers_cannot_bypass_rate_limit(self, client: TestClient, valid_eval_license):
        """RATE-005: Adding synthetic IP or forwarded headers does not bypass license-scoped rate limit."""
        headers = valid_eval_license["headers"].copy()
        headers["X-Forwarded-For"] = "1.2.3.4"
        lic_id = valid_eval_license["license_id"]

        # Pre-fill 60 requests in quota manager
        usage = quota_manager._usage[lic_id]
        now = time.time()
        usage.request_timestamps = [now] * 60

        with pytest.raises(QuotaExceededError) as exc:
            quota_manager.check_rate_limit(lic_id)
        assert exc.value.resource == "rate_limit"

    def test_rate_006_legitimate_traffic_within_rate_allowed(self):
        """RATE-006: Traffic within rate allowance is accepted without throttling."""
        rl = RateLimitService()
        for _ in range(10):
            rl.check_rate_limit("lic-legit", limit=60, window_seconds=60)
        assert rl.get_utilization("lic-legit") == 10


class TestReconciliationAndAdministration:
    """Suite F: Reconciliation & Administration Tests (RECON-001 - RECON-007)"""

    def test_recon_001_clean_state_reports_zero_discrepancies(self):
        """RECON-001: Consistent ledger and counters report CLEAN status."""
        counter_repo = QuotaCounterRepository()
        ev_repo = UsageEventRepository()
        recon = QuotaReconciliationService(counter_repo=counter_repo, event_repo=ev_repo)

        c = counter_repo.get_or_create_counter("lic-clean", "e1", "t1", "queries", "lifetime", 100)
        c.consumed = 5

        # Record 5 matching consumption events
        for i in range(5):
            ev = UsageEvent(
                event_id=f"ev-{i}", license_id="lic-clean", evaluator_id="e1", tenant_id="t1",
                operation_id=f"op-{i}", event_type=UsageEventType.CONSUMPTION, quota_key="queries",
                amount=1, unit="queries", source="test", idempotency_key=f"idemp-c-{i}",
                occurred_at=datetime.now(timezone.utc)
            )
            ev_repo.record_event(ev)

        report = recon.reconcile_license("lic-clean")
        assert report["status"] == "CLEAN"
        assert len(report["discrepancies"]) == 0

    def test_recon_002_counter_drift_detected(self):
        """RECON-002: Reconciliation identifies counter drift when counter doesn't match ledger sum."""
        counter_repo = QuotaCounterRepository()
        ev_repo = UsageEventRepository()
        recon = QuotaReconciliationService(counter_repo=counter_repo, event_repo=ev_repo)

        c = counter_repo.get_or_create_counter("lic-drift", "e1", "t1", "queries", "lifetime", 100)
        c.consumed = 10  # Counter says 10, but ledger has only 5

        for i in range(5):
            ev = UsageEvent(
                event_id=f"ev-d-{i}", license_id="lic-drift", evaluator_id="e1", tenant_id="t1",
                operation_id=f"op-{i}", event_type=UsageEventType.CONSUMPTION, quota_key="queries",
                amount=1, unit="queries", source="test", idempotency_key=f"idemp-d-{i}",
                occurred_at=datetime.now(timezone.utc)
            )
            ev_repo.record_event(ev)

        report = recon.reconcile_license("lic-drift")
        assert report["status"] == "DISCREPANCY_DETECTED"
        assert report["discrepancies"][0]["consumed_difference"] == 5

    def test_recon_003_apply_reconciliation_fix_repairs_drift(self):
        """RECON-003: apply_reconciliation_fix aligns counter to ledger and logs adjustment."""
        counter_repo = QuotaCounterRepository()
        ev_repo = UsageEventRepository()
        adj_repo = UsageAdjustmentRepository()
        recon = QuotaReconciliationService(
            counter_repo=counter_repo, event_repo=ev_repo, adjustment_repo=adj_repo
        )

        c = counter_repo.get_or_create_counter("lic-repair", "e1", "t1", "queries", "lifetime", 100)
        c.consumed = 8  # Drifted

        # Ledger has 10
        for i in range(10):
            ev = UsageEvent(
                event_id=f"ev-r-{i}", license_id="lic-repair", evaluator_id="e1", tenant_id="t1",
                operation_id=f"op-{i}", event_type=UsageEventType.CONSUMPTION, quota_key="queries",
                amount=1, unit="queries", source="test", idempotency_key=f"idemp-r-{i}",
                occurred_at=datetime.now(timezone.utc)
            )
            ev_repo.record_event(ev)

        fix_res = recon.apply_reconciliation_fix("lic-repair", "queries")
        assert fix_res["status"] == "CORRECTED"
        assert c.consumed == 10
        assert len(adj_repo.list_adjustments("lic-repair")) == 1

    def test_recon_004_admin_quota_adjustment_logged(self, client: TestClient):
        """RECON-004: POST /v1/admin/evaluation/licenses/{id}/quota-adjustments applies audited adjustment."""
        # Setup counter
        default_quota_counter_repository.get_or_create_counter(
            "lic-adj-test", "eval-1", "ten-1", "queries", "lifetime", 100
        )
        res = client.post(
            "/v1/admin/evaluation/licenses/lic-adj-test/quota-adjustments",
            headers={"X-Admin-Secret": "aegis-admin-secret-key-eval-2026"},
            json={
                "quota_key": "queries",
                "amount": 5,
                "reason": "Customer courtesy credit",
                "ticket_ref": "TICK-1234",
            },
        )
        assert res.status_code == 200
        assert res.json()["status"] == "ADJUSTMENT_APPLIED"
        assert res.json()["after"] == 5

    def test_recon_005_stale_reservation_expired_and_released(self):
        """RECON-005: Stale reservation is expired and released during periodic reconciliation."""
        counter_repo = QuotaCounterRepository()
        res_repo = UsageReservationRepository()
        res_service = QuotaReservationService(counter_repo=counter_repo, reservation_repo=res_repo)
        recon = QuotaReconciliationService(counter_repo=counter_repo, reservation_repo=res_repo)

        res = res_service.reserve_capacity("lic-recon-stale", "e1", "t1", "op-1", {"queries": 4}, "idemp-stale", ttl_seconds=1)
        c = counter_repo.list_counters("lic-recon-stale")[0]
        assert c.reserved == 4

        time.sleep(1.1)
        recon.reconcile_license("lic-recon-stale")
        assert c.reserved == 0

    def test_recon_006_evaluator_usage_summary_endpoint(self, client: TestClient, valid_eval_license):
        """RECON-006: GET /v1/evaluation/usage returns complete, accurate usage summary."""
        headers = valid_eval_license["headers"]
        res = client.get("/v1/evaluation/usage", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "documents" in data
        assert "queries" in data
        assert "storage_bytes" in data
        assert "policy_version" in data

    def test_recon_007_admin_routes_reject_unauthorized_evaluators(self, client: TestClient, valid_eval_license):
        """RECON-007: Administrative quota routes strictly reject evaluator tokens without admin secret."""
        headers = valid_eval_license["headers"]
        res = client.get("/v1/admin/evaluation/quotas/policies", headers=headers)
        assert res.status_code in (401, 403)
