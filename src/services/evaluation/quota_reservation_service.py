"""
AEGIS-DocIntel Quota Reservation Service (PROT-04 WP-04.06)
Performs atomic, multi-dimensional capacity reservation before protected engine execution.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from src.repositories.evaluation.quota_counter_repository import (
    QuotaCounterRepository,
    default_quota_counter_repository,
)
from src.repositories.evaluation.usage_reservation_repository import (
    UsageReservationRepository,
    default_usage_reservation_repository,
)
from src.schemas.evaluation.quota import QuotaPeriod
from src.schemas.evaluation.usage_reservation import (
    ReservationItem,
    ReservationStatus,
    UsageReservation,
)
from src.services.evaluation.quota_policy_service import (
    QuotaPolicyService,
    default_quota_policy_service,
)


class QuotaExceededException(Exception):
    def __init__(self, resource: str, current: int, limit: int, message: Optional[str] = None):
        self.resource = resource
        self.current = current
        self.limit = limit
        msg = (
            message
            or f"Evaluation quota exceeded for {resource}: {current}/{limit}. Upgrade to AEGIS Enterprise for unlimited capacity."
        )
        super().__init__(msg)


class QuotaReservationService:
    def __init__(
        self,
        policy_service: Optional[QuotaPolicyService] = None,
        counter_repo: Optional[QuotaCounterRepository] = None,
        reservation_repo: Optional[UsageReservationRepository] = None,
    ):
        self.policy_service = policy_service or default_quota_policy_service
        self.counter_repo = counter_repo or default_quota_counter_repository
        self.reservation_repo = reservation_repo or default_usage_reservation_repository

    def _compute_period_key(self, period: QuotaPeriod, now: datetime) -> str:
        if period == QuotaPeriod.DAILY:
            return f"daily:{now.strftime('%Y-%m-%d')}"
        elif period == QuotaPeriod.WEEKLY:
            return f"weekly:{now.strftime('%Y-W%W')}"
        elif period == QuotaPeriod.MONTHLY:
            return f"monthly:{now.strftime('%Y-%m')}"
        elif period == QuotaPeriod.CONCURRENT:
            return "concurrent"
        elif period == QuotaPeriod.PER_OPERATION:
            return "per_operation"
        return "lifetime"

    def reserve_capacity(
        self,
        license_id: str,
        evaluator_id: str,
        tenant_id: str,
        operation_id: str,
        requested_items: Dict[str, int],
        idempotency_key: str,
        policy_key: str = "evaluation-basic",
        ttl_seconds: int = 300,
    ) -> UsageReservation:
        """
        Atomically reserves capacity across all requested dimensions.
        Enforces all-or-nothing rollback on any dimension exhaustion.
        """
        # Idempotency check
        existing = self.reservation_repo.get_by_idempotency_key(license_id, idempotency_key)
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        policy = self.policy_service.get_effective_policy(policy_key)

        # Deterministic sorting of quota dimensions to prevent deadlock
        sorted_keys = sorted(requested_items.keys())
        reserved_audit: List[Tuple[str, int]] = []  # [(counter_id, amount)]
        reservation_items: Dict[str, ReservationItem] = {}

        try:
            for q_key in sorted_keys:
                requested_amt = requested_items[q_key]
                if requested_amt <= 0:
                    reservation_items[q_key] = ReservationItem(
                        quota_key=q_key,
                        requested_amount=requested_amt,
                        reserved_amount=0,
                    )
                    continue

                q_def = policy.quotas.get(q_key)
                if not q_def:
                    raise QuotaExceededException(
                        resource=q_key,
                        current=0,
                        limit=0,
                        message=f"Quota dimension '{q_key}' not permitted or configured in policy '{policy_key}'",
                    )

                period_key = self._compute_period_key(q_def.period, now)
                counter = self.counter_repo.get_or_create_counter(
                    license_id=license_id,
                    evaluator_id=evaluator_id,
                    tenant_id=tenant_id,
                    quota_key=q_key,
                    period_key=period_key,
                    limit_value=q_def.limit,
                    period_start=now,
                )

                # Attempt atomic conditional reservation
                success = self.counter_repo.atomic_reserve(counter.id, requested_amt)
                if not success:
                    raise QuotaExceededException(
                        resource=q_key,
                        current=counter.consumed + counter.reserved,
                        limit=counter.limit_value,
                        message=f"Evaluation quota exceeded for {q_key}: {counter.consumed + counter.reserved}/{counter.limit_value}",
                    )

                reserved_audit.append((counter.id, requested_amt))
                reservation_items[q_key] = ReservationItem(
                    quota_key=q_key,
                    requested_amount=requested_amt,
                    reserved_amount=requested_amt,
                )

        except Exception:
            # Atomic rollback: release any capacity reserved before failure
            for cid, amt in reserved_audit:
                self.counter_repo.atomic_release(cid, amt)
            raise

        res_id = str(uuid.uuid4())
        reservation = UsageReservation(
            id=res_id,
            idempotency_key=idempotency_key,
            license_id=license_id,
            evaluator_id=evaluator_id,
            tenant_id=tenant_id,
            operation_id=operation_id,
            items=reservation_items,
            status=ReservationStatus.PENDING,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )

        created_res, _ = self.reservation_repo.create_reservation(reservation)
        return created_res


default_quota_reservation_service = QuotaReservationService()
