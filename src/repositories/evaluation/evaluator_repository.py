"""
AEGIS-DocIntel Evaluator Repository
PROT-FINAL-08: Evaluator Profile Storage and Atomic Lifecycle State Machine
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.schemas.evaluation.evaluator import EvaluatorProfile, EvaluatorStatus


class InvalidStateTransitionError(Exception):
    """Raised when an evaluator state transition violates lifecycle rules."""
    pass


class EvaluatorNotFoundError(Exception):
    """Raised when an evaluator ID does not exist."""
    pass


class EvaluatorRepository:
    """Thread-safe in-memory repository for evaluator profiles with audit trail."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._evaluators: Dict[str, EvaluatorProfile] = {}
        self._audit_log: List[dict] = []

    def create(self, profile: EvaluatorProfile) -> EvaluatorProfile:
        with self._lock:
            self._evaluators[profile.evaluator_id] = profile
            self._record_audit(
                evaluator_id=profile.evaluator_id,
                action="CREATE",
                from_status=None,
                to_status=profile.status.value,
                operator_id="system",
                reason="Initial creation",
            )
            return profile

    def get_by_id(self, evaluator_id: str) -> Optional[EvaluatorProfile]:
        with self._lock:
            return self._evaluators.get(evaluator_id)

    def get_by_email(self, email: str) -> Optional[EvaluatorProfile]:
        with self._lock:
            norm_email = email.strip().lower()
            for profile in self._evaluators.values():
                if profile.contact_email.strip().lower() == norm_email:
                    return profile
            return None

    def list_all(self, status: Optional[EvaluatorStatus] = None) -> List[EvaluatorProfile]:
        with self._lock:
            if status is None:
                return list(self._evaluators.values())
            return [p for p in self._evaluators.values() if p.status == status]

    def transition_status(
        self,
        evaluator_id: str,
        target_status: EvaluatorStatus,
        reason: str,
        operator_id: str,
        allowed_from: Optional[List[EvaluatorStatus]] = None,
    ) -> EvaluatorProfile:
        with self._lock:
            evaluator = self.get_by_id(evaluator_id)
            if not evaluator:
                raise EvaluatorNotFoundError(f"Evaluator '{evaluator_id}' not found")

            current_status = evaluator.status

            # Strict terminal state rules: EXPIRED, REVOKED, and TERMINATED cannot be silently reverted to ACTIVE
            terminal_states = {EvaluatorStatus.EXPIRED, EvaluatorStatus.REVOKED, EvaluatorStatus.TERMINATED}
            if current_status in terminal_states and target_status == EvaluatorStatus.ACTIVE:
                raise InvalidStateTransitionError(
                    f"Cannot automatically reinstate evaluator from terminal state '{current_status.value}' to ACTIVE. "
                    "A new evaluation license and operator authorization is required."
                )

            # Reinstatement from SUSPENDED requires explicit reason and operator
            if current_status == EvaluatorStatus.SUSPENDED and target_status == EvaluatorStatus.ACTIVE:
                if not reason or len(reason.strip()) < 5:
                    raise InvalidStateTransitionError("Reinstatement from SUSPENDED requires an explicit reason (min 5 chars).")

            if allowed_from is not None and current_status not in allowed_from:
                raise InvalidStateTransitionError(
                    f"Invalid state transition from '{current_status.value}' to '{target_status.value}'. "
                    f"Allowed source states: {[s.value for s in allowed_from]}"
                )

            now_iso = datetime.now(timezone.utc).isoformat()
            updated = evaluator.model_copy(
                update={"status": target_status, "updated_at": now_iso}
            )
            self._evaluators[evaluator_id] = updated

            self._record_audit(
                evaluator_id=evaluator_id,
                action="TRANSITION_STATUS",
                from_status=current_status.value,
                to_status=target_status.value,
                operator_id=operator_id,
                reason=reason,
            )
            return updated

    def record_agreements(
        self,
        evaluator_id: str,
        agreement_version: str,
        privacy_notice_version: str,
    ) -> EvaluatorProfile:
        with self._lock:
            evaluator = self.get_by_id(evaluator_id)
            if not evaluator:
                raise EvaluatorNotFoundError(f"Evaluator '{evaluator_id}' not found")

            now_iso = datetime.now(timezone.utc).isoformat()
            updated = evaluator.model_copy(
                update={
                    "agreement_version": agreement_version,
                    "agreement_accepted_at": now_iso,
                    "privacy_notice_version": privacy_notice_version,
                    "privacy_notice_acknowledged_at": now_iso,
                    "updated_at": now_iso,
                }
            )
            self._evaluators[evaluator_id] = updated
            self._record_audit(
                evaluator_id=evaluator_id,
                action="ACCEPT_AGREEMENTS",
                from_status=evaluator.status.value,
                to_status=evaluator.status.value,
                operator_id="evaluator",
                reason=f"Accepted Agreement v{agreement_version} and Privacy Notice v{privacy_notice_version}",
            )
            return updated

    def get_audit_trail(self, evaluator_id: Optional[str] = None) -> List[dict]:
        with self._lock:
            if evaluator_id is None:
                return list(self._audit_log)
            return [e for e in self._audit_log if e["evaluator_id"] == evaluator_id]

    def _record_audit(
        self,
        evaluator_id: str,
        action: str,
        from_status: Optional[str],
        to_status: str,
        operator_id: str,
        reason: str,
    ) -> None:
        self._audit_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "evaluator_id": evaluator_id,
            "action": action,
            "from_status": from_status,
            "to_status": to_status,
            "operator_id": operator_id,
            "reason": reason,
        })
