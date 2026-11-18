"""
AEGIS-DocIntel Gateway Request Context Module
PROT-FINAL-05: Workstream DEP-02 & DEP-03

Defines the server-generated TrustedInternalContext that encapsulates
authenticated and verified evaluator identity, tenant boundary, license,
entitlements, and quota reservation before forwarding to the private engine.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TrustedInternalContext(BaseModel):
    """
    Immutable server-generated authorization context passed from the public gateway
    to the private engine. Clients cannot supply or forge this context.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(default_factory=lambda: f"req-{uuid.uuid4().hex[:12]}")
    principal_id: str
    tenant_id: str
    workspace_id: str = "default-eval-workspace"
    license_id: str
    session_id: str
    device_id: str
    operation: str
    entitlement_revision: int = 1
    quota_reservation_id: Optional[str] = None
    service_identity: str = "evaluation-gateway"
    environment: str = "production"
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(seconds=60)
    )
    role: str = "evaluator"

    def to_canonical_dict(self) -> dict:
        """Serializes context to a canonical dictionary for cryptographic signing."""
        return {
            "request_id": self.request_id,
            "principal_id": self.principal_id,
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "license_id": self.license_id,
            "session_id": self.session_id,
            "device_id": self.device_id,
            "operation": self.operation,
            "entitlement_revision": self.entitlement_revision,
            "quota_reservation_id": self.quota_reservation_id,
            "service_identity": self.service_identity,
            "environment": self.environment,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "role": self.role,
        }
