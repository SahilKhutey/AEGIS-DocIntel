"""
AEGIS-DocIntel Usage Ledger Event Schema (PROT-04 WP-04.06)
Defines immutable usage ledger events for auditable accounting.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class UsageEventType(str, Enum):
    CONSUMPTION = "consumption"
    RELEASE = "release"
    ADJUSTMENT = "adjustment"


class UsageEvent(BaseModel):
    event_id: str = Field(description="Unique event UUID")
    license_id: str = Field(description="License identifier")
    evaluator_id: str = Field(description="Evaluator identifier")
    tenant_id: str = Field(description="Tenant identifier")
    operation_id: str = Field(description="Operation / Request / Job UUID")
    reservation_id: Optional[str] = Field(default=None, description="Related reservation UUID if any")
    event_type: UsageEventType = Field(description="Type of usage event")
    quota_key: str = Field(description="Quota dimension name")
    amount: int = Field(description="Signed integer quantity (e.g. bytes, tokens, requests)")
    unit: str = Field(description="Measurement unit")
    source: str = Field(description="Trusted subsystem producing this event")
    idempotency_key: str = Field(description="Deduplication key")
    occurred_at: datetime = Field(description="When the event occurred")
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When recorded in DB")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Contextual non-sensitive metadata")
