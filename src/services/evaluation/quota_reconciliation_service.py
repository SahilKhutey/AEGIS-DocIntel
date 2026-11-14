"""
AEGIS-DocIntel Quota Reconciliation Service (PROT-04 WP-04.06)
Detects and repairs accounting discrepancies between operational counters, reservations, and ledger events.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from src.repositories.evaluation.quota_counter_repository import (
    QuotaCounterRepository,
    default_quota_counter_repository,
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
from src.schemas.evaluation.usage_event import UsageEvent, UsageEventType
from src.schemas.evaluation.usage_reservation import ReservationStatus
from src.schemas.evaluation.usage_summary import UsageAdjustmentRecord


class QuotaReconciliationService:
    def __init__(
        self,
        counter_repo: Optional[QuotaCounterRepository] = None,
        event_repo: Optional[UsageEventRepository] = None,
        reservation_repo: Optional[UsageReservationRepository] = None,
        adjustment_repo: Optional[UsageAdjustmentRepository] = None,
    ):
        self.counter_repo = counter_repo or default_quota_counter_repository
        self.event_repo = event_repo or default_usage_event_repository
        self.reservation_repo = reservation_repo or default_usage_reservation_repository
        self.adjustment_repo = adjustment_repo or default_usage_adjustment_repository

    def reconcile_license(self, license_id: str) -> Dict[str, Any]:
        """
        Runs comprehensive integrity scan for a license:
        1. Recovers expired reservations and releases counter locks.
        2. Compares counter.consumed against authoritative sum of committed ledger events.
        3. Compares counter.reserved against sum of active pending reservation items.
        """
        # Step 1: Recover stale reservations
        expired_reservations = self.reservation_repo.expire_stale_reservations()
        stale_recovered_count = 0
        for exp_res in expired_reservations:
            if exp_res.license_id == license_id:
                stale_recovered_count += 1
                for q_key, item in exp_res.items.items():
                    counters = self.counter_repo.list_counters(license_id)
                    matching = [c for c in counters if c.quota_key == q_key]
                    if matching:
                        self.counter_repo.atomic_release(matching[0].id, item.reserved_amount)

        # Step 2: Compare counters to ledger and active reservations
        counters = self.counter_repo.list_counters(license_id)
        active_reservations = self.reservation_repo.list_active_reservations(license_id)

        discrepancies: List[Dict[str, Any]] = []

        for counter in counters:
            # Expected consumed from ledger
            expected_consumed = self.event_repo.get_total_consumed(license_id, counter.quota_key)

            # Expected reserved from active reservations
            expected_reserved = sum(
                res.items[counter.quota_key].reserved_amount
                for res in active_reservations
                if counter.quota_key in res.items
            )

            consumed_diff = counter.consumed - expected_consumed
            reserved_diff = counter.reserved - expected_reserved

            if consumed_diff != 0 or reserved_diff != 0:
                discrepancies.append({
                    "quota_key": counter.quota_key,
                    "counter_consumed": counter.consumed,
                    "expected_consumed": expected_consumed,
                    "consumed_difference": consumed_diff,
                    "counter_reserved": counter.reserved,
                    "expected_reserved": expected_reserved,
                    "reserved_difference": reserved_diff,
                })

        return {
            "license_id": license_id,
            "status": "DISCREPANCY_DETECTED" if discrepancies else "CLEAN",
            "stale_reservations_recovered": stale_recovered_count,
            "discrepancies": discrepancies,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def apply_reconciliation_fix(
        self,
        license_id: str,
        quota_key: str,
        actor: str = "reconciliation_daemon",
    ) -> Dict[str, Any]:
        """
        Corrects detected counter drift by aligning counter.consumed with authoritative ledger sum.
        Records an auditable adjustment record.
        """
        counters = self.counter_repo.list_counters(license_id)
        matching = [c for c in counters if c.quota_key == quota_key]
        if not matching:
            raise KeyError(f"No counter found for license '{license_id}' and quota '{quota_key}'")

        counter = matching[0]
        expected_consumed = self.event_repo.get_total_consumed(license_id, quota_key)
        diff = expected_consumed - counter.consumed

        if diff == 0:
            return {"status": "NO_ACTION_NEEDED", "license_id": license_id, "quota_key": quota_key}

        # Apply counter adjustment
        before_val = counter.consumed
        new_val = self.counter_repo.atomic_adjust(counter.id, diff)

        # Record adjustment record
        adj_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        record = UsageAdjustmentRecord(
            adjustment_id=adj_id,
            license_id=license_id,
            tenant_id=counter.tenant_id,
            quota_key=quota_key,
            amount=diff,
            before_value=before_val,
            after_value=new_val,
            reason=f"Automated reconciliation aligning operational counter with ledger sum ({before_val} -> {new_val})",
            ticket_ref="RECON-AUTO-CORRECT",
            approved_by=actor,
            timestamp=now,
        )
        self.adjustment_repo.record_adjustment(record)

        # Log compensating adjustment event in ledger
        ev_id = str(uuid.uuid4())
        ledger_event = UsageEvent(
            event_id=ev_id,
            license_id=license_id,
            evaluator_id=counter.evaluator_id,
            tenant_id=counter.tenant_id,
            operation_id="reconciliation_adjustment",
            event_type=UsageEventType.ADJUSTMENT,
            quota_key=quota_key,
            amount=diff,
            unit="units",
            source="reconciliation_service",
            idempotency_key=f"recon:{adj_id}",
            occurred_at=now,
            recorded_at=now,
        )
        self.event_repo.record_event(ledger_event)

        return {
            "status": "CORRECTED",
            "license_id": license_id,
            "quota_key": quota_key,
            "before": before_val,
            "after": new_val,
            "adjustment": diff,
        }


default_quota_reconciliation_service = QuotaReconciliationService()
