"""
AEGIS-DocIntel Usage Reservation Schema (PROT-04 WP-04.06)
Defines models for atomic two-phase quota reservation and settlement.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReservationStatus(str, Enum):
    PENDING = "PENDING"
    COMMITTED = "COMMITTED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class ReservationItem(BaseModel):
    quota_key: str
    requested_amount: int = Field(ge=0, description="Requested units")
    reserved_amount: int = Field(ge=0, description="Amount locked from available capacity")
    settled_amount: int = Field(default=0, ge=0, description="Actual measured usage committed")


class UsageReservation(BaseModel):
    id: str = Field(description="Unique reservation UUID")
    idempotency_key: str = Field(description="Deduplication key for request idempotency")
    license_id: str = Field(description="Authoritative license ID")
    evaluator_id: str = Field(description="Evaluator user ID")
    tenant_id: str = Field(description="Tenant scope")
    operation_id: str = Field(description="Associated request or job identifier")
    items: Dict[str, ReservationItem] = Field(description="Map of quota_key -> ReservationItem")
    status: ReservationStatus = Field(default=ReservationStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(description="Reservation timeout timestamp")
    settled_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return self.status == ReservationStatus.PENDING and datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_active(self) -> bool:
        return self.status == ReservationStatus.PENDING and datetime.now(timezone.utc) < self.expires_at
