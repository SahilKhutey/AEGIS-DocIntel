"""
AEGIS-DocIntel Session Expiry Sweeper Service (PROT-04 WP-04.07)
Runs periodic sweeps of idle and absolute expired sessions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from src.repositories.evaluation.session_repository import session_repository, SessionRepository


class SessionExpiryService:
    def __init__(self, sess_repo: Optional[SessionRepository] = None):
        self._sess_repo = sess_repo or session_repository

    def sweep_expired(self, now: Optional[datetime] = None) -> int:
        """Sweeps and transitions all expired sessions."""
        return self._sess_repo.sweep_expired_sessions(now or datetime.now(timezone.utc))


session_expiry_service = SessionExpiryService()
