"""
AEGIS-DocIntel Usage Summary & Adjustment Schemas (PROT-04 WP-04.06)
Defines reporting responses and administrative adjustment models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QuotaDimensionUsage(BaseModel):
    used: int = Field(ge=0, description="Committed usage units")
    reserved: int = Field(default=0, ge=0, description="Currently reserved in-flight units")
    limit: int = Field(ge=0, description="Total permitted units")
    remaining: int = Field(ge=0, description="Available remaining capacity")
    unit: str = Field(description="Unit of measurement")
    period: str = Field(description="Quota period (lifetime, daily, etc.)")
    resets_at: Optional[str] = Field(default=None, description="ISO timestamp of next period reset if periodic")


class EvaluationUsageSummary(BaseModel):
    license_id: str
    tenant_id: str
    policy_key: str
    policy_version: str
    usage: Dict[str, QuotaDimensionUsage]
    generated_at: str


class UsageAdjustmentRequest(BaseModel):
    quota_key: str = Field(description="Target quota dimension")
    amount: int = Field(description="Units to adjust (positive to increase consumed, negative to credit)")
    reason: str = Field(min_length=5, description="Administrative audit justification")
    ticket_ref: Optional[str] = Field(default=None, description="Support ticket or authorization reference")
    approved_by: str = Field(min_length=3, description="Admin username or service principal")


class UsageAdjustmentRecord(BaseModel):
    adjustment_id: str
    license_id: str
    tenant_id: str
    quota_key: str
    amount: int
    before_value: int
    after_value: int
    reason: str
    ticket_ref: Optional[str] = None
    approved_by: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RateLimitExceededResponse(BaseModel):
    error: str = "rate_limit_exceeded"
    message: str = "The request rate limit has been reached."
    retry_after_seconds: int = 30
    limit: int
    window_seconds: int
