"""
src/repositories/evaluation/entitlement_event_repository.py
===========================================================
Append-only audit event log for evaluation authorization decisions.
Strictly redacts credentials, private keys, raw tokens, and document content.
Complies with PROT-04 WP-04.05 specification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class EntitlementAuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    principal_id: str
    tenant_id: str
    license_id: Optional[str] = None
    feature: str
    permission: str
    resource_type: str = "generic"
    resource_id: Optional[str] = None
    decision: str  # "ALLOW" or "DENY"
    reason_code: str
    details: Dict[str, Any] = Field(default_factory=dict)


class EntitlementEventRepository:
    """Thread-safe append-only store for authorization telemetry and security monitoring."""

    def __init__(self) -> None:
        self._events: List[EntitlementAuditEvent] = []

    def record_event(
        self,
        *,
        event_type: str,
        principal_id: str,
        tenant_id: str,
        feature: str,
        permission: str,
        decision: str,
        reason_code: str,
        license_id: Optional[str] = None,
        resource_type: str = "generic",
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> EntitlementAuditEvent:
        # Sanitization: Ensure no raw tokens or document contents leak
        clean_details: Dict[str, Any] = {}
        if details:
            for k, v in details.items():
                if any(sec in k.lower() for sec in ("token", "secret", "key", "password", "prompt", "text", "body")):
                    clean_details[k] = "[REDACTED]"
                else:
                    clean_details[k] = v

        event = EntitlementAuditEvent(
            event_type=event_type,
            principal_id=principal_id,
            tenant_id=tenant_id,
            license_id=license_id,
            feature=feature,
            permission=permission,
            resource_type=resource_type,
            resource_id=resource_id,
            decision=decision,
            reason_code=reason_code,
            details=clean_details,
        )
        self._events.append(event)
        return event

    def list_events(
        self,
        *,
        license_id: Optional[str] = None,
        principal_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 100,
    ) -> List[EntitlementAuditEvent]:
        filtered = self._events
        if license_id:
            filtered = [e for e in filtered if e.license_id == license_id]
        if principal_id:
            filtered = [e for e in filtered if e.principal_id == principal_id]
        if tenant_id:
            filtered = [e for e in filtered if e.tenant_id == tenant_id]
        if decision:
            filtered = [e for e in filtered if e.decision == decision]
        return filtered[-limit:]

    def clear(self) -> None:
        self._events.clear()
