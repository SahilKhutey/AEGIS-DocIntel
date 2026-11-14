"""
AEGIS-DocIntel Session Validation Service (PROT-04 WP-04.07)
Validates presented credentials against active sessions, timeouts, device states, and license revocation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Optional, Tuple

from src.schemas.evaluation.session import EvaluationSession, RevocationReason, SessionStatus
from src.schemas.evaluation.session_audit import SessionAuditEvent, SessionAuditEventType
from src.repositories.evaluation.session_repository import session_repository, SessionRepository
from src.repositories.evaluation.session_audit_repository import session_audit_repository, SessionAuditRepository
from .refresh_token_service import hash_token


class SessionValidationService:
    def __init__(
        self,
        sess_repo: Optional[SessionRepository] = None,
        audit_repo: Optional[SessionAuditRepository] = None,
        is_license_revoked_fn: Optional[Callable[[str], bool]] = None,
        is_device_active_fn: Optional[Callable[[str, str], bool]] = None,
    ):
        self._sess_repo = sess_repo or session_repository
        self._audit_repo = audit_repo or session_audit_repository
        self._is_license_revoked_fn = is_license_revoked_fn
        self._is_device_active_fn = is_device_active_fn

    def set_license_revocation_checker(self, fn: Callable[[str], bool]) -> None:
        self._is_license_revoked_fn = fn

    def set_device_active_checker(self, fn: Callable[[str, str], bool]) -> None:
        self._is_device_active_fn = fn

    def validate_access_token(
        self,
        raw_access_token: str,
        now: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[EvaluationSession], str]:
        """
        Authoritatively validates an access token.
        Returns: (is_valid, session, rejection_reason)
        """
        check_time = now or datetime.now(timezone.utc)
        at_hash = hash_token(raw_access_token)
        sess = self._sess_repo.get_by_access_hash(at_hash)

        if not sess:
            return False, None, "SESSION_NOT_FOUND"

        # 1. Explicit revocation check
        if sess.status == SessionStatus.REVOKED:
            return False, sess, "SESSION_REVOKED"

        # 2. Timeouts: Idle & Absolute
        if check_time > sess.absolute_expires_at:
            self._sess_repo.revoke_session(sess.session_id, RevocationReason.ABSOLUTE_TIMEOUT)
            self._audit_repo.record_event(
                SessionAuditEvent(
                    event_type=SessionAuditEventType.SESSION_EXPIRED,
                    session_id=sess.session_id,
                    evaluator_id=sess.evaluator_id,
                    status="EXPIRED",
                    details={"reason": "absolute_timeout"},
                )
            )
            return False, sess, "SESSION_ABSOLUTE_TIMEOUT"

        if check_time > sess.idle_expires_at:
            self._sess_repo.revoke_session(sess.session_id, RevocationReason.IDLE_TIMEOUT)
            self._audit_repo.record_event(
                SessionAuditEvent(
                    event_type=SessionAuditEventType.SESSION_EXPIRED,
                    session_id=sess.session_id,
                    evaluator_id=sess.evaluator_id,
                    status="EXPIRED",
                    details={"reason": "idle_timeout"},
                )
            )
            return False, sess, "SESSION_IDLE_TIMEOUT"

        # 3. External license revocation cascade
        if self._is_license_revoked_fn and self._is_license_revoked_fn(sess.license_id):
            self._sess_repo.revoke_session(sess.session_id, RevocationReason.LICENSE_REVOKED)
            self._audit_repo.record_event(
                SessionAuditEvent(
                    event_type=SessionAuditEventType.LICENSE_SESSION_REVOKED,
                    session_id=sess.session_id,
                    evaluator_id=sess.evaluator_id,
                    license_id=sess.license_id,
                    status="REVOKED",
                    details={"reason": "license_revocation_cascade"},
                )
            )
            return False, sess, "LICENSE_REVOKED"

        # 4. External device deactivation check
        if self._is_device_active_fn and not self._is_device_active_fn(sess.license_id, sess.device_id):
            self._sess_repo.revoke_session(sess.session_id, RevocationReason.DEVICE_DEACTIVATED)
            self._audit_repo.record_event(
                SessionAuditEvent(
                    event_type=SessionAuditEventType.DEVICE_SESSION_REVOKED,
                    session_id=sess.session_id,
                    evaluator_id=sess.evaluator_id,
                    device_id=sess.device_id,
                    status="REVOKED",
                    details={"reason": "device_deactivation_cascade"},
                )
            )
            return False, sess, "DEVICE_DEACTIVATED"

        # 5. Active: Slide idle expiration
        self._sess_repo.touch_session(sess.session_id)
        return True, sess, "OK"


session_validation_service = SessionValidationService()
