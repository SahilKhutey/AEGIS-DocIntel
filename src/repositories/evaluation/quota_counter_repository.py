"""
AEGIS-DocIntel Quota Counter Repository (PROT-04 WP-04.06)
Manages fast, durable operational counters with thread-safe atomic conditional reservations.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


@dataclass
class QuotaCounterRecord:
    id: str
    license_id: str
    evaluator_id: str
    tenant_id: str
    quota_key: str
    period_key: str
    period_start: datetime
    period_end: Optional[datetime]
    consumed: int
    reserved: int
    limit_value: int
    revision: int
    updated_at: datetime

    @property
    def available(self) -> int:
        return max(0, self.limit_value - self.consumed - self.reserved)


class QuotaCounterRepository:
    def __init__(self):
        # Key: (license_id, quota_key, period_key) -> QuotaCounterRecord
        self._counters: Dict[Tuple[str, str, str], QuotaCounterRecord] = {}
        # ID lookup: id -> (license_id, quota_key, period_key)
        self._id_index: Dict[str, Tuple[str, str, str]] = {}
        self._lock = threading.Lock()

    def get_or_create_counter(
        self,
        license_id: str,
        evaluator_id: str,
        tenant_id: str,
        quota_key: str,
        period_key: str,
        limit_value: int,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> QuotaCounterRecord:
        with self._lock:
            key = (license_id, quota_key, period_key)
            if key in self._counters:
                return self._counters[key]

            cid = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            record = QuotaCounterRecord(
                id=cid,
                license_id=license_id,
                evaluator_id=evaluator_id,
                tenant_id=tenant_id,
                quota_key=quota_key,
                period_key=period_key,
                period_start=period_start or now,
                period_end=period_end,
                consumed=0,
                reserved=0,
                limit_value=limit_value,
                revision=1,
                updated_at=now,
            )
            self._counters[key] = record
            self._id_index[cid] = key
            return record

    def get_counter(self, license_id: str, quota_key: str, period_key: str) -> Optional[QuotaCounterRecord]:
        with self._lock:
            return self._counters.get((license_id, quota_key, period_key))

    def get_counter_by_id(self, counter_id: str) -> Optional[QuotaCounterRecord]:
        with self._lock:
            key = self._id_index.get(counter_id)
            if key:
                return self._counters.get(key)
            return None

    def list_counters(self, license_id: str) -> List[QuotaCounterRecord]:
        with self._lock:
            return [c for c in self._counters.values() if c.license_id == license_id]

    def atomic_reserve(self, counter_id: str, amount: int) -> bool:
        """
        Atomically reserves capacity on the counter.
        Returns True if capacity was successfully reserved; False if insufficient capacity.
        Implements conditional update: WHERE consumed + reserved + amount <= limit_value
        """
        if amount <= 0:
            return True

        with self._lock:
            key = self._id_index.get(counter_id)
            if not key or key not in self._counters:
                return False
            counter = self._counters[key]

            # Invariant: consumed + reserved + amount <= limit_value
            if counter.consumed + counter.reserved + amount > counter.limit_value:
                return False

            counter.reserved += amount
            counter.revision += 1
            counter.updated_at = datetime.now(timezone.utc)
            return True

    def atomic_commit(self, counter_id: str, reserved_to_release: int, actual_consumed: int) -> None:
        """
        Atomically commits actual usage and releases the in-flight reservation.
        """
        with self._lock:
            key = self._id_index.get(counter_id)
            if not key or key not in self._counters:
                return
            counter = self._counters[key]
            counter.reserved = max(0, counter.reserved - reserved_to_release)
            counter.consumed += actual_consumed
            counter.revision += 1
            counter.updated_at = datetime.now(timezone.utc)

    def atomic_release(self, counter_id: str, amount_to_release: int) -> None:
        """
        Atomically releases reserved capacity back to available pool.
        """
        with self._lock:
            key = self._id_index.get(counter_id)
            if not key or key not in self._counters:
                return
            counter = self._counters[key]
            counter.reserved = max(0, counter.reserved - amount_to_release)
            counter.revision += 1
            counter.updated_at = datetime.now(timezone.utc)

    def atomic_adjust(self, counter_id: str, adjustment_amount: int) -> int:
        """
        Applies administrative adjustment to consumed count.
        Returns the new consumed count.
        """
        with self._lock:
            key = self._id_index.get(counter_id)
            if not key or key not in self._counters:
                raise KeyError(f"Counter '{counter_id}' not found")
            counter = self._counters[key]
            counter.consumed = max(0, counter.consumed + adjustment_amount)
            counter.revision += 1
            counter.updated_at = datetime.now(timezone.utc)
            return counter.consumed

    def reset_counter(self, license_id: str, quota_key: str, period_key: str) -> None:
        with self._lock:
            key = (license_id, quota_key, period_key)
            if key in self._counters:
                counter = self._counters[key]
                counter.consumed = 0
                counter.reserved = 0
                counter.revision += 1
                counter.updated_at = datetime.now(timezone.utc)


default_quota_counter_repository = QuotaCounterRepository()
