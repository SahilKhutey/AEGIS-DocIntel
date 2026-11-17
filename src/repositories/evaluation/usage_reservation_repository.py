"""
AEGIS-DocIntel Usage Reservation Repository (PROT-04 WP-04.06)
Manages in-flight quota reservations, idempotency, and lifecycle state transitions.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from src.schemas.evaluation.usage_reservation import ReservationStatus, UsageReservation


class UsageReservationRepository:
    def __init__(self):
        # Key: reservation_id -> UsageReservation
        self._reservations: Dict[str, UsageReservation] = {}
        # Key: (license_id, idempotency_key) -> reservation_id
        self._idempotency_map: Dict[Tuple[str, str], str] = {}
        self._lock = threading.Lock()

    def create_reservation(self, reservation: UsageReservation) -> Tuple[UsageReservation, bool]:
        """
        Stores reservation with strict idempotency check.
        Returns (reservation, was_created).
        If idempotency key already exists for this license, returns existing reservation and False.
        """
        with self._lock:
            key = (reservation.license_id, reservation.idempotency_key)
            if key in self._idempotency_map:
                existing_id = self._idempotency_map[key]
                return self._reservations[existing_id], False

            self._reservations[reservation.id] = reservation
            self._idempotency_map[key] = reservation.id
            return reservation, True

    def get_reservation(self, reservation_id: str) -> Optional[UsageReservation]:
        with self._lock:
            return self._reservations.get(reservation_id)

    def get_by_idempotency_key(self, license_id: str, idempotency_key: str) -> Optional[UsageReservation]:
        with self._lock:
            key = (license_id, idempotency_key)
            res_id = self._idempotency_map.get(key)
            if res_id:
                return self._reservations.get(res_id)
            return None

    def update_status(
        self,
        reservation_id: str,
        new_status: ReservationStatus,
        settled_items: Optional[Dict[str, int]] = None,
    ) -> UsageReservation:
        with self._lock:
            res = self._reservations.get(reservation_id)
            if not res:
                raise KeyError(f"Reservation '{reservation_id}' not found")

            if res.status != ReservationStatus.PENDING:
                raise ValueError(
                    f"Cannot transition reservation '{reservation_id}' from {res.status.value} to {new_status.value}"
                )

            res.status = new_status
            now = datetime.now(timezone.utc)
            if new_status == ReservationStatus.COMMITTED:
                res.settled_at = now
                if settled_items:
                    for q_key, settled_amt in settled_items.items():
                        if q_key in res.items:
                            res.items[q_key].settled_amount = settled_amt
            elif new_status in (ReservationStatus.RELEASED, ReservationStatus.EXPIRED):
                res.settled_at = now

            return res

    def list_active_reservations(self, license_id: Optional[str] = None) -> List[UsageReservation]:
        with self._lock:
            now = datetime.now(timezone.utc)
            out = []
            for res in self._reservations.values():
                if res.status == ReservationStatus.PENDING and res.expires_at > now:
                    if license_id is None or res.license_id == license_id:
                        out.append(res)
            return out

    def expire_stale_reservations(self, now: Optional[datetime] = None) -> List[UsageReservation]:
        """
        Identifies all expired pending reservations, marks them EXPIRED, and returns them for quota release.
        """
        curr = now or datetime.now(timezone.utc)
        expired_list = []
        with self._lock:
            for res in self._reservations.values():
                if res.status == ReservationStatus.PENDING and res.expires_at <= curr:
                    res.status = ReservationStatus.EXPIRED
                    res.settled_at = curr
                    expired_list.append(res)
        return expired_list


default_usage_reservation_repository = UsageReservationRepository()
