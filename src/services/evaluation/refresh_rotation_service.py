"""
AEGIS-DocIntel Refresh Rotation & Replay Detection Service (PROT-04 WP-04.07)
Coordinates atomic refresh rotation and instant family revocation upon replay attack detection.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from src.schemas.evaluation.refresh import EvaluationRefreshToken, RefreshTokenStatus
from src.schemas.evaluation.session import RevocationReason
from src.schemas.evaluation.session_audit import SessionAuditEvent, SessionAuditEventType
from src.repositories.evaluation.session_repository import session_repository, SessionRepository
from src.repositories.evaluation.refresh_token_repository import refresh_token_repository, RefreshTokenRepository
from src.repositories.evaluation.session_audit_repository import session_audit_repository, SessionAuditRepository
from .refresh_token_service import generate_access_token, generate_refresh_token, hash_token


class RefreshRotationService:
    def __init__(
        self,
        sess_repo: Optional[SessionRepository] = None,
        ref_repo: Optional[RefreshTokenRepository] = None,
        audit_repo: Optional[SessionAuditRepository] = None,
        access_token_ttl_seconds: int = 600,
        idle_timeout_seconds: int = 1800,
    ):
        self._sess_repo = sess_repo or session_repository
        self._ref_repo = ref_repo or refresh_token_repository
        self._audit_repo = audit_repo or session_audit_repository
        self.access_token_ttl_seconds = access_token_ttl_seconds
        self.idle_timeout_seconds = idle_timeout_seconds

    def rotate_session(
        self,
        raw_refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Executes atomic rotation of a refresh token.
        If a consumed token is replayed:
        1. Immediately revokes the parent session and ALL sessions sharing the token family.
        2. Revokes all refresh tokens in that family.
        3. Emits a high-severity security audit event.
        4. Rejects the request.
        """
        curr_time = now or datetime.now(timezone.utc)
        old_hash = hash_token(raw_refresh_token)

        # 1. Check if token was previously consumed
        consumed_fam_id = self._ref_repo.is_hash_consumed(old_hash)
        if consumed_fam_id:
            self._handle_replay_compromise(consumed_fam_id, old_hash, ip_address)
            return False, None, "REFRESH_REPLAY_DETECTED"

        # 2. Look up existing active token record to prepare rotation
        existing_tok = self._ref_repo.get_by_hash(old_hash)
        if not existing_tok:
            return False, None, "TOKEN_NOT_FOUND"

        fam_id = existing_tok.family_id
        sid = existing_tok.session_id

        # Look up parent session
        sess = self._sess_repo.get_by_id(sid)
        if not sess:
            return False, None, "SESSION_NOT_FOUND"

        if not sess.is_active(curr_time):
            return False, None, "SESSION_INACTIVE"

        # 3. Generate replacement credentials
        new_raw_rt = generate_refresh_token()
        new_rt_hash = hash_token(new_raw_rt)
        new_raw_at = generate_access_token()
        new_at_hash = hash_token(new_raw_at)

        new_tok_record = EvaluationRefreshToken(
            token_id=str(uuid.uuid4()),
            session_id=sid,
            family_id=fam_id,
            token_hash=new_rt_hash,
            status=RefreshTokenStatus.ACTIVE,
            created_at=curr_time,
            expires_at=sess.absolute_expires_at,
        )

        # 4. Atomic rotation call in repository
        success, rotated_tok, outcome = self._ref_repo.atomic_rotate(
            old_hash=old_hash,
            new_token=new_tok_record,
            now=curr_time,
        )

        if not success:
            if outcome.startswith("REPLAY_DETECTED"):
                rep_fam = outcome.split(":", 1)[1] if ":" in outcome else fam_id
                self._handle_replay_compromise(rep_fam, old_hash, ip_address)
                return False, None, "REFRESH_REPLAY_DETECTED"
            return False, None, outcome

        # 5. Successfully rotated: update session binding
        old_at_hash = sess.access_token_hash
        self._sess_repo.update_access_hash(sid, old_at_hash, new_at_hash)
        self._sess_repo.touch_session(sid, self.idle_timeout_seconds)

        self._audit_repo.record_event(
            SessionAuditEvent(
                event_type=SessionAuditEventType.SESSION_REFRESHED,
                session_id=sid,
                evaluator_id=sess.evaluator_id,
                license_id=sess.license_id,
                device_id=sess.device_id,
                status="SUCCESS",
                details={"family_id": fam_id, "ip_address": ip_address},
            )
        )

        response_payload = {
            "access_token": new_raw_at,
            "refresh_token": new_raw_rt,
            "token_type": "Bearer",
            "expires_in": self.access_token_ttl_seconds,
            "session_id": sid,
            "family_id": fam_id,
        }
        return True, response_payload, "SUCCESS"

    def _handle_replay_compromise(self, family_id: str, replayed_hash: str, ip_address: Optional[str]) -> None:
        """Executes immediate lockdown of the compromised token family."""
        revoked_sessions = self._sess_repo.revoke_family(family_id, RevocationReason.REFRESH_REPLAY_DETECTED)
        revoked_tokens = self._ref_repo.revoke_family(family_id, reason="refresh_replay_detected")

        self._audit_repo.record_event(
            SessionAuditEvent(
                event_type=SessionAuditEventType.REFRESH_TOKEN_REUSE_DETECTED,
                status="COMPROMISE_DETECTED",
                details={
                    "family_id": family_id,
                    "replayed_hash_prefix": replayed_hash[:16],
                    "revoked_sessions_count": revoked_sessions,
                    "revoked_tokens_count": revoked_tokens,
                    "ip_address": ip_address,
                },
            )
        )


refresh_rotation_service = RefreshRotationService()
