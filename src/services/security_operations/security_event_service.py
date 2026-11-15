"""
AEGIS-DocIntel Security Event Service (PROT-04 WP-04.08)
Centralized dispatching service for validating, redacting, and persisting security events.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from src.security.event_schema import SecurityEvent, Severity
from src.security.event_catalog import is_known_event_type, get_default_severity
from src.security.event_redaction import sanitize_event_details
from src.security.security_context import get_current_security_context
from src.repositories.security_operations.security_event_repository import (
    SecurityEventRepository,
    security_event_repository,
)
from src.repositories.security_operations.audit_repository import (
    AuditRepository,
    audit_repository,
)

logger = logging.getLogger("aegis.security.events")


class SecurityEventService:
    def __init__(
        self,
        event_repo: Optional[SecurityEventRepository] = None,
        audit_repo: Optional[AuditRepository] = None,
        alert_evaluator: Optional[Any] = None,
    ):
        self._event_repo = event_repo or security_event_repository
        self._audit_repo = audit_repo or audit_repository
        if alert_evaluator is not None:
            self._alert_evaluator = alert_evaluator
        else:
            try:
                from .alert_evaluation_service import alert_evaluation_service
                self._alert_evaluator = alert_evaluation_service
            except Exception:
                self._alert_evaluator = None

    def set_alert_evaluator(self, alert_evaluator: Any) -> None:
        self._alert_evaluator = alert_evaluator

    def emit_event(
        self,
        event_type: str,
        result: str,
        severity: Optional[Severity] = None,
        tenant_id: Optional[str] = None,
        evaluator_id: Optional[str] = None,
        session_id: Optional[str] = None,
        device_id: Optional[str] = None,
        reason_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        reject_if_secret: bool = False,
    ) -> SecurityEvent:
        """
        Validates, redacts, persists, and triggers alerting on security events.
        Enforces schema conformity and data minimization.
        """
        # Resolve request context if omitted
        ctx = get_current_security_context()
        req_id = request_id or ctx.request_id
        corr_id = correlation_id or ctx.correlation_id
        tid = tenant_id or ctx.tenant_id
        eid = evaluator_id or ctx.evaluator_id
        sid = session_id or ctx.session_id
        did = device_id or ctx.device_id

        # Classify severity
        sev = severity or get_default_severity(event_type)

        # Sanitize metadata (OPS-005)
        clean_details = sanitize_event_details(details or {}, reject_if_secret=reject_if_secret)

        event = SecurityEvent(
            event_id=uuid4(),
            event_type=event_type,
            severity=sev,
            occurred_at=datetime.now(timezone.utc),
            service="evaluation-gateway",
            environment="production",
            request_id=req_id,
            correlation_id=corr_id,
            tenant_id=tid,
            evaluator_id=eid,
            session_id=sid,
            device_id=did,
            result=result,
            reason_code=reason_code,
            details=clean_details,
        )

        # 1. Store in event repository
        self._event_repo.record_event(event)

        # 2. Append to cryptographic hash-chained audit ledger
        self._audit_repo.append_event(event.model_dump())

        # 3. Trigger alert evaluation if hooked
        if self._alert_evaluator:
            try:
                self._alert_evaluator.evaluate_event(event)
            except Exception as e:
                logger.error("Error evaluating alert rules on security event: %s", e)

        return event


security_event_service = SecurityEventService()
