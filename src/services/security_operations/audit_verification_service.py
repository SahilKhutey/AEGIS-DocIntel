"""
AEGIS-DocIntel Audit Verification Service (PROT-04 WP-04.08)
Verifies hash-chain continuity and anchors external tamper-evident checkpoints.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from src.security.event_schema import Severity
from src.repositories.security_operations.audit_repository import AuditRepository, audit_repository

logger = logging.getLogger("aegis.security.audit.verification")


class AuditVerificationService:
    def __init__(self, audit_repo: Optional[AuditRepository] = None, alert_evaluator: Optional[Any] = None):
        self._audit_repo = audit_repo or audit_repository
        if alert_evaluator is not None:
            self._alert_evaluator = alert_evaluator
        else:
            try:
                from src.services.security_operations.alert_evaluation_service import alert_evaluation_service
                self._alert_evaluator = alert_evaluation_service
            except ImportError:
                self._alert_evaluator = None

    def set_alert_evaluator(self, alert_evaluator: Any) -> None:
        self._alert_evaluator = alert_evaluator

    def verify_chain_integrity(self) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Validates hash-chain integrity: H_i = SHA-256(H_{i-1} || Canonical(E_i)).
        Triggers critical alert and incident on verification failure (AUDIT-008, MON-007).
        """
        valid, fail_idx, reason = self._audit_repo.verify_integrity()

        # Check external checkpoint
        checkpoint_ok = self._audit_repo.verify_latest_checkpoint()
        if not checkpoint_ok:
            valid = False
            fail_idx = fail_idx or len(self._audit_repo.get_chain())
            reason = "EXTERNAL_CHECKPOINT_MISMATCH"

        if not valid:
            logger.critical("Audit integrity failure detected at index %s: %s", fail_idx, reason)
            if self._alert_evaluator:
                self._alert_evaluator.trigger_alert(
                    rule_id="MON-010",
                    severity="critical",
                    title="Audit Log Integrity Failure",
                    description=f"Cryptographic hash chain or external checkpoint verification failed: {reason}",
                    context={"failure_index": fail_idx, "reason": reason},
                )

        return valid, fail_idx, reason

    def anchor_checkpoint(self) -> Dict[str, Any]:
        """Anchors an external signed checkpoint of the current audit head."""
        return self._audit_repo.create_checkpoint()

    def export_tamper_evident_log(self) -> Dict[str, Any]:
        """Generates a complete, verifiable export for external auditors."""
        return self._audit_repo.export_audit_log()


audit_verification_service = AuditVerificationService()
