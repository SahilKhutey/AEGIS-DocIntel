"""
AEGIS-DocIntel Session Service (PROT-04 WP-04.07)
Coordinates session initialization, retrieval, and contextual updates.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from src.schemas.evaluation.refresh import EvaluationRefreshToken, RefreshTokenStatus
from src.schemas.evaluation.session import EvaluationSession, SessionStatus
from src.schemas.evaluation.session_audit import SessionAuditEvent, SessionAuditEventType
from src.repositories.evaluation.session_repository import session_repository, SessionRepository
from src.repositories.evaluation.refresh_token_repository import refresh_token_repository, RefreshTokenRepository
from src.repositories.evaluation.session_audit_repository import session_audit_repository, SessionAuditRepository
from .refresh_token_service import generate_access_token, generate_refresh_token, hash_token


class SessionService:
    def __init__(
        self,
        sess_repo: Optional[SessionRepository] = None,
        ref_repo: Optional[RefreshTokenRepository] = None,
        audit_repo: Optional[SessionAuditRepository] = None,
        access_token_ttl_seconds: int = 600,       # 10 minutes
        idle_timeout_seconds: int = 1800,          # 30 minutes
        absolute_timeout_seconds: int = 604800,    # 7 days
    ):
        self._sess_repo = sess_repo or session_repository
        self._ref_repo = ref_repo or refresh_token_repository
        self._audit_repo = audit_repo or session_audit_repository
        self.access_token_ttl_seconds = access_token_ttl_seconds
        self.idle_timeout_seconds = idle_timeout_seconds
        self.absolute_timeout_seconds = absolute_timeout_seconds

    def create_session(
        self,
        evaluator_id: str,
        tenant_id: str,
        license_id: str,
        device_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        family_id: Optional[str] = None,
    ) -> Tuple[EvaluationSession, str, str]:
        """
        Creates an authoritative server-side session and issues a matched pair of
        short-lived access token and rotating refresh token.
        Returns: (session_entity, raw_access_token, raw_refresh_token).
        """
        now = datetime.now(timezone.utc)
        fam_id = family_id or str(uuid.uuid4())
        sid = str(uuid.uuid4())

        raw_access_token = generate_access_token()
        raw_refresh_token = generate_refresh_token()

        at_hash = hash_token(raw_access_token)
        rt_hash = hash_token(raw_refresh_token)

        idle_exp = now + timedelta(seconds=self.idle_timeout_seconds)
        abs_exp = now + timedelta(seconds=self.absolute_timeout_seconds)

        session = EvaluationSession(
            session_id=sid,
            evaluator_id=evaluator_id,
            tenant_id=tenant_id,
            license_id=license_id,
            device_id=device_id,
            status=SessionStatus.ACTIVE,
            token_family_id=fam_id,
            access_token_hash=at_hash,
            created_at=now,
            last_seen_at=now,
            idle_expires_at=idle_exp,
            absolute_expires_at=abs_exp,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
        )
        self._sess_repo.save_session(session)

        refresh_record = EvaluationRefreshToken(
            token_id=str(uuid.uuid4()),
            session_id=sid,
            family_id=fam_id,
            token_hash=rt_hash,
            status=RefreshTokenStatus.ACTIVE,
            created_at=now,
            expires_at=abs_exp,
        )
        self._ref_repo.save_token(refresh_record)

        self._audit_repo.record_event(
            SessionAuditEvent(
                event_type=SessionAuditEventType.SESSION_CREATED,
                session_id=sid,
                evaluator_id=evaluator_id,
                license_id=license_id,
                device_id=device_id,
                status="SUCCESS",
                details={
                    "family_id": fam_id,
                    "ip_address": ip_address,
                    "idle_timeout_seconds": self.idle_timeout_seconds,
                    "absolute_timeout_seconds": self.absolute_timeout_seconds,
                },
            )
        )

        return session, raw_access_token, raw_refresh_token

    def get_session(self, session_id: str) -> Optional[EvaluationSession]:
        return self._sess_repo.get_by_id(session_id)

    def get_session_by_access_token(self, raw_access_token: str) -> Optional[EvaluationSession]:
        at_hash = hash_token(raw_access_token)
        return self._sess_repo.get_by_access_hash(at_hash)


session_service = SessionService()
