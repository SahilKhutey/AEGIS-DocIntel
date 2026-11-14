"""
AEGIS-DocIntel Session Revocation Service (PROT-04 WP-04.07)
Provides multi-scoped server-side revocation: single session, evaluator all sessions,
device cascade, license cascade, and incident containment.
"""

from __future__ import annotations

from typing import Optional

from src.schemas.evaluation.session import RevocationReason
from src.schemas.evaluation.session_audit import SessionAuditEvent, SessionAuditEventType
from src.repositories.evaluation.session_repository import session_repository, SessionRepository
from src.repositories.evaluation.refresh_token_repository import refresh_token_repository, RefreshTokenRepository
from src.repositories.evaluation.session_audit_repository import session_audit_repository, SessionAuditRepository
from .refresh_token_service import hash_token


class SessionRevocationService:
    def __init__(
        self,
        sess_repo: Optional[SessionRepository] = None,
        ref_repo: Optional[RefreshTokenRepository] = None,
        audit_repo: Optional[SessionAuditRepository] = None,
    ):
        self._sess_repo = sess_repo or session_repository
        self._ref_repo = ref_repo or refresh_token_repository
        self._audit_repo = audit_repo or session_audit_repository

    def revoke_session(self, session_id: str, reason: RevocationReason = RevocationReason.USER_LOGOUT) -> bool:
        """Revokes a single session and logs the event."""
        sess = self._sess_repo.revoke_session(session_id, reason)
        if not sess:
            return False

        self._audit_repo.record_event(
            SessionAuditEvent(
                event_type=SessionAuditEventType.SESSION_LOGGED_OUT if reason == RevocationReason.USER_LOGOUT else SessionAuditEventType.SESSION_REVOKED,
                session_id=session_id,
                evaluator_id=sess.evaluator_id,
                license_id=sess.license_id,
                device_id=sess.device_id,
                status="REVOKED",
                details={"reason": reason.value},
            )
        )
        return True

    def revoke_by_access_token(self, raw_access_token: str, reason: RevocationReason = RevocationReason.USER_LOGOUT) -> bool:
        """Revokes the session associated with the provided active access token."""
        at_hash = hash_token(raw_access_token)
        sess = self._sess_repo.get_by_access_hash(at_hash)
        if not sess:
            return False
        return self.revoke_session(sess.session_id, reason)

    def revoke_all_evaluator_sessions(
        self,
        evaluator_id: str,
        reason: RevocationReason = RevocationReason.ALL_SESSIONS_LOGOUT,
        except_session_id: Optional[str] = None,
    ) -> int:
        """Revokes all active sessions for a specific evaluator."""
        count = self._sess_repo.revoke_evaluator_sessions(evaluator_id, reason, except_session_id=except_session_id)
        self._audit_repo.record_event(
            SessionAuditEvent(
                event_type=SessionAuditEventType.ALL_SESSIONS_REVOKED,
                evaluator_id=evaluator_id,
                status="REVOKED",
                details={"revoked_count": count, "reason": reason.value, "except_session_id": except_session_id},
            )
        )
        return count

    def revoke_device_sessions(self, device_id: str, reason: RevocationReason = RevocationReason.DEVICE_DEACTIVATED) -> int:
        """Revokes all active sessions bound to a hardware device."""
        count = self._sess_repo.revoke_device_sessions(device_id, reason)
        self._audit_repo.record_event(
            SessionAuditEvent(
                event_type=SessionAuditEventType.DEVICE_SESSION_REVOKED,
                device_id=device_id,
                status="REVOKED",
                details={"revoked_count": count, "reason": reason.value},
            )
        )
        return count

    def revoke_license_sessions(self, license_id: str, reason: RevocationReason = RevocationReason.LICENSE_REVOKED) -> int:
        """Revokes all active sessions bound to a revoked or expired license."""
        count = self._sess_repo.revoke_license_sessions(license_id, reason)
        self._audit_repo.record_event(
            SessionAuditEvent(
                event_type=SessionAuditEventType.LICENSE_SESSION_REVOKED,
                license_id=license_id,
                status="REVOKED",
                details={"revoked_count": count, "reason": reason.value},
            )
        )
        return count

    def revoke_security_incident(self, family_id: str, reason: RevocationReason = RevocationReason.SECURITY_COMPROMISE) -> int:
        """Revokes all sessions and tokens in a compromised family."""
        sess_count = self._sess_repo.revoke_family(family_id, reason)
        self._ref_repo.revoke_family(family_id, reason=reason.value)
        self._audit_repo.record_event(
            SessionAuditEvent(
                event_type=SessionAuditEventType.REFRESH_TOKEN_REUSE_DETECTED,
                status="COMPROMISE_DETECTED",
                details={"family_id": family_id, "revoked_sessions": sess_count, "reason": reason.value},
            )
        )
        return sess_count


session_revocation_service = SessionRevocationService()
