"""
AEGIS-DocIntel Quota Settlement Service (PROT-04 WP-04.06)
Commits actual measured usage, releases unconsumed reservations, and enforces idempotent settlements.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from src.repositories.evaluation.quota_counter_repository import (
    QuotaCounterRepository,
    default_quota_counter_repository,
)
from src.repositories.evaluation.usage_event_repository import (
    UsageEventRepository,
    default_usage_event_repository,
)
from src.repositories.evaluation.usage_reservation_repository import (
    UsageReservationRepository,
    default_usage_reservation_repository,
)
from src.schemas.evaluation.usage_event import UsageEvent, UsageEventType
from src.schemas.evaluation.usage_reservation import ReservationStatus, UsageReservation


class QuotaSettlementService:
    def __init__(
        self,
        counter_repo: Optional[QuotaCounterRepository] = None,
        reservation_repo: Optional[UsageReservationRepository] = None,
        event_repo: Optional[UsageEventRepository] = None,
    ):
        self.counter_repo = counter_repo or default_quota_counter_repository
        self.reservation_repo = reservation_repo or default_usage_reservation_repository
        self.event_repo = event_repo or default_usage_event_repository

    def settle_reservation(
        self,
        reservation_id: str,
        actual_usage: Dict[str, int],
        idempotency_key: str,
        source: str = "engine_settlement",
    ) -> UsageReservation:
        """
        Settles in-flight capacity reservation:
        - Commits measured actual usage
        - Releases any unconsumed capacity difference
        - Records immutable consumption events in usage ledger
        - Guaranteed idempotent (repeated calls return committed record without double-charging)
        """
        reservation = self.reservation_repo.get_reservation(reservation_id)
        if not reservation:
            raise KeyError(f"Reservation '{reservation_id}' not found")

        # Idempotent repeat: return already-settled reservation
        if reservation.status == ReservationStatus.COMMITTED:
            return reservation

        if reservation.status in (ReservationStatus.RELEASED, ReservationStatus.EXPIRED):
            raise ValueError(
                f"Cannot settle reservation '{reservation_id}' in terminal status '{reservation.status.value}'"
            )

        now = datetime.now(timezone.utc)
        settled_items: Dict[str, int] = {}

        for q_key, item in reservation.items.items():
            reserved_amt = item.reserved_amount
            actual_amt = actual_usage.get(q_key, reserved_amt)
            settled_items[q_key] = actual_amt

            # Find matching counter
            counters = self.counter_repo.list_counters(reservation.license_id)
            matching = [c for c in counters if c.quota_key == q_key]
            if matching:
                counter = matching[0]
                self.counter_repo.atomic_commit(
                    counter_id=counter.id,
                    reserved_to_release=reserved_amt,
                    actual_consumed=actual_amt,
                )

            # Record immutable ledger event
            ev_id = str(uuid.uuid4())
            ledger_event = UsageEvent(
                event_id=ev_id,
                license_id=reservation.license_id,
                evaluator_id=reservation.evaluator_id,
                tenant_id=reservation.tenant_id,
                operation_id=reservation.operation_id,
                reservation_id=reservation.id,
                event_type=UsageEventType.CONSUMPTION,
                quota_key=q_key,
                amount=actual_amt,
                unit="units",
                source=source,
                idempotency_key=f"{idempotency_key}:{q_key}",
                occurred_at=now,
                recorded_at=now,
            )
            self.event_repo.record_event(ledger_event)

        return self.reservation_repo.update_status(
            reservation_id=reservation_id,
            new_status=ReservationStatus.COMMITTED,
            settled_items=settled_items,
        )

    def release_reservation(
        self,
        reservation_id: str,
        reason: str = "operation_cancelled",
        source: str = "engine_release",
    ) -> UsageReservation:
        """
        Releases an in-flight reservation back to the available pool.
        """
        reservation = self.reservation_repo.get_reservation(reservation_id)
        if not reservation:
            raise KeyError(f"Reservation '{reservation_id}' not found")

        if reservation.status != ReservationStatus.PENDING:
            return reservation

        now = datetime.now(timezone.utc)
        for q_key, item in reservation.items.items():
            reserved_amt = item.reserved_amount
            if reserved_amt <= 0:
                continue

            counters = self.counter_repo.list_counters(reservation.license_id)
            matching = [c for c in counters if c.quota_key == q_key]
            if matching:
                counter = matching[0]
                self.counter_repo.atomic_release(counter.id, reserved_amt)

            # Record release event in ledger
            ev_id = str(uuid.uuid4())
            ledger_event = UsageEvent(
                event_id=ev_id,
                license_id=reservation.license_id,
                evaluator_id=reservation.evaluator_id,
                tenant_id=reservation.tenant_id,
                operation_id=reservation.operation_id,
                reservation_id=reservation.id,
                event_type=UsageEventType.RELEASE,
                quota_key=q_key,
                amount=-reserved_amt,
                unit="units",
                source=source,
                idempotency_key=f"release:{reservation_id}:{q_key}",
                occurred_at=now,
                recorded_at=now,
                metadata={"release_reason": reason},
            )
            self.event_repo.record_event(ledger_event)

        return self.reservation_repo.update_status(
            reservation_id=reservation_id,
            new_status=ReservationStatus.RELEASED,
        )


default_quota_settlement_service = QuotaSettlementService()
