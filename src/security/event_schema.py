"""
AEGIS-DocIntel Security Event Schema (PROT-04 WP-04.08)
Defines standard, immutable, strictly validated security event models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEvent(BaseModel):
    """
    Standardized, server-authoritative security event model.
    Enforces strict extra-field rejection to maintain canonical audit schemas.
    """
    model_config = ConfigDict(extra="forbid")

    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier (UUIDv4)")
    event_type: str = Field(..., description="Canonical event classification name")
    severity: Severity = Field(..., description="Categorized severity level")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of occurrence")
    service: str = Field(default="evaluation-gateway", description="Originating backend service")
    environment: str = Field(default="production", description="Runtime environment")
    request_id: Optional[str] = Field(default=None, description="Per-request correlation ID")
    correlation_id: Optional[str] = Field(default=None, description="End-to-end operation lineage ID")
    tenant_id: Optional[str] = Field(default=None, description="Associated tenant boundary")
    evaluator_id: Optional[str] = Field(default=None, description="Actor evaluator subject ID")
    session_id: Optional[str] = Field(default=None, description="Active session ID if applicable")
    device_id: Optional[str] = Field(default=None, description="Hardware device ID if applicable")
    result: str = Field(..., description="Action outcome: allowed, denied, error, success, failure")
    reason_code: Optional[str] = Field(default=None, description="Sanitized reason code or policy token")
    source_fingerprint: Optional[str] = Field(default=None, description="Privacy-preserving source hash")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Redacted operational metadata")
    schema_version: int = Field(default=1, description="Schema revision number")
