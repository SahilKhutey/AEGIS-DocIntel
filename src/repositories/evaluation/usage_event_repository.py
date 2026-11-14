"""
AEGIS-DocIntel Usage Event Repository (PROT-04 WP-04.06)
Maintains the authoritative append-only immutable usage ledger.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from src.schemas.evaluation.usage_event import UsageEvent, UsageEventType


class UsageEventRepository:
    def __init__(self):
        self._events: List[UsageEvent] = []
        # Key: (license_id, idempotency_key) -> event_id
        self._idempotency_map: Dict[Tuple[str, str], UsageEvent] = {}
        self._lock = threading.Lock()

    def record_event(self, event: UsageEvent) -> Tuple[UsageEvent, bool]:
        """
        Appends an event to the ledger with strict idempotency check.
        Returns (event, was_recorded).
        """
        with self._lock:
            key = (event.license_id, event.idempotency_key)
            if key in self._idempotency_map:
                return self._idempotency_map[key], False

            self._events.append(event)
            self._idempotency_map[key] = event
            return event, True

    def list_events(
        self,
        license_id: str,
        quota_key: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[UsageEvent]:
        with self._lock:
            results = []
            for ev in self._events:
                if ev.license_id != license_id:
                    continue
                if quota_key and ev.quota_key != quota_key:
                    continue
                if start_time and ev.occurred_at < start_time:
                    continue
                if end_time and ev.occurred_at > end_time:
                    continue
                results.append(ev)
            return results

    def get_total_consumed(
        self,
        license_id: str,
        quota_key: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> int:
        """
        Computes authoritative consumed total directly from ledger events:
        Total = sum(CONSUMPTION) - sum(RELEASE) + sum(ADJUSTMENT)
        """
        with self._lock:
            total = 0
            for ev in self._events:
                if ev.license_id != license_id or ev.quota_key != quota_key:
                    continue
                if period_start and ev.occurred_at < period_start:
                    continue
                if period_end and ev.occurred_at > period_end:
                    continue

                if ev.event_type == UsageEventType.CONSUMPTION:
                    total += ev.amount
                elif ev.event_type == UsageEventType.RELEASE:
                    total -= abs(ev.amount)
                elif ev.event_type == UsageEventType.ADJUSTMENT:
                    total += ev.amount

            return max(0, total)


default_usage_event_repository = UsageEventRepository()
