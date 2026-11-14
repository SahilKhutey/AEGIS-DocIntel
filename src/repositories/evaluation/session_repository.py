"""
AEGIS-DocIntel Session Repository (PROT-04 WP-04.07)
Manages evaluation session state, token lookups, and scoped multi-entity cascades.
Thread-safe and concurrency-hardened.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set

from src.schemas.evaluation.session import EvaluationSession, RevocationReason, SessionStatus


class SessionRepository:
    """Thread-safe in-memory session repository with multi-indexed lookups."""

    def __init__(self):
        self._lock = threading.RLock()
        self._sessions: Dict[str, EvaluationSession] = {}
        self._access_hash_index: Dict[str, str] = {}
        self._family_index: Dict[str, Set[str]] = {}
        self._evaluator_index: Dict[str, Set[str]] = {}
        self._device_index: Dict[str, Set[str]] = {}
        self._license_index: Dict[str, Set[str]] = {}

    def save_session(self, session: EvaluationSession) -> EvaluationSession:
        """Stores or updates a session and maintains indexes."""
        with self._lock:
            sid = session.session_id
            self._sessions[sid] = session
            self._access_hash_index[session.access_token_hash] = sid

            if session.token_family_id not in self._family_index:
                self._family_index[session.token_family_id] = set()
            self._family_index[session.token_family_id].add(sid)

            if session.evaluator_id not in self._evaluator_index:
                self._evaluator_index[session.evaluator_id] = set()
            self._evaluator_index[session.evaluator_id].add(sid)

            if session.device_id not in self._device_index:
                self._device_index[session.device_id] = set()
            self._device_index[session.device_id].add(sid)

            if session.license_id not in self._license_index:
                self._license_index[session.license_id] = set()
            self._license_index[session.license_id].add(sid)

            return session

    def get_by_id(self, session_id: str) -> Optional[EvaluationSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def get_by_access_hash(self, access_hash: str) -> Optional[EvaluationSession]:
        with self._lock:
            sid = self._access_hash_index.get(access_hash)
            if not sid:
                return None
            return self._sessions.get(sid)

    def list_by_evaluator(self, evaluator_id: str, active_only: bool = True) -> List[EvaluationSession]:
        with self._lock:
            sids = self._evaluator_index.get(evaluator_id, set())
            sessions = [self._sessions[sid] for sid in sids if sid in self._sessions]
            if active_only:
                now = datetime.now(timezone.utc)
                sessions = [s for s in sessions if s.is_active(now)]
            return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def list_by_license(self, license_id: str, active_only: bool = True) -> List[EvaluationSession]:
        with self._lock:
            sids = self._license_index.get(license_id, set())
            sessions = [self._sessions[sid] for sid in sids if sid in self._sessions]
            if active_only:
                now = datetime.now(timezone.utc)
                sessions = [s for s in sessions if s.is_active(now)]
            return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def list_by_device(self, device_id: str, active_only: bool = True) -> List[EvaluationSession]:
        with self._lock:
            sids = self._device_index.get(device_id, set())
            sessions = [self._sessions[sid] for sid in sids if sid in self._sessions]
            if active_only:
                now = datetime.now(timezone.utc)
                sessions = [s for s in sessions if s.is_active(now)]
            return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def list_by_family(self, family_id: str) -> List[EvaluationSession]:
        with self._lock:
            sids = self._family_index.get(family_id, set())
            return [self._sessions[sid] for sid in sids if sid in self._sessions]

    def update_access_hash(self, session_id: str, old_hash: str, new_hash: str) -> bool:
        """Rotates the access token hash bound to the session."""
        with self._lock:
            sess = self._sessions.get(session_id)
            if not sess:
                return False
            if old_hash in self._access_hash_index:
                del self._access_hash_index[old_hash]
            sess.access_token_hash = new_hash
            self._access_hash_index[new_hash] = session_id
            return True

    def touch_session(self, session_id: str, sliding_idle_seconds: int = 1800) -> Optional[EvaluationSession]:
        """Extends idle expiration timestamp upon active evaluator request."""
        with self._lock:
            sess = self._sessions.get(session_id)
            if not sess or not sess.is_active():
                return None
            now = datetime.now(timezone.utc)
            sess.last_seen_at = now
            new_idle = now + timedelta(seconds=sliding_idle_seconds)
            # Cannot exceed fixed absolute expiration
            sess.idle_expires_at = min(new_idle, sess.absolute_expires_at)
            return sess

    def revoke_session(self, session_id: str, reason: RevocationReason) -> Optional[EvaluationSession]:
        """Atomically marks a specific session as revoked."""
        with self._lock:
            sess = self._sessions.get(session_id)
            if not sess:
                return None
            sess.status = SessionStatus.REVOKED
            sess.revoked_at = datetime.now(timezone.utc)
            sess.revocation_reason = reason
            return sess

    def revoke_family(self, family_id: str, reason: RevocationReason) -> int:
        """Revokes all sessions belonging to a compromised token family."""
        with self._lock:
            sids = self._family_index.get(family_id, set())
            count = 0
            for sid in sids:
                sess = self._sessions.get(sid)
                if sess and sess.status == SessionStatus.ACTIVE:
                    sess.status = SessionStatus.REVOKED
                    sess.revoked_at = datetime.now(timezone.utc)
                    sess.revocation_reason = reason
                    count += 1
            return count

    def revoke_evaluator_sessions(
        self,
        evaluator_id: str,
        reason: RevocationReason,
        except_session_id: Optional[str] = None,
    ) -> int:
        """Revokes all sessions owned by an evaluator (with optional exception)."""
        with self._lock:
            sids = self._evaluator_index.get(evaluator_id, set())
            count = 0
            for sid in sids:
                if except_session_id and sid == except_session_id:
                    continue
                sess = self._sessions.get(sid)
                if sess and sess.status == SessionStatus.ACTIVE:
                    sess.status = SessionStatus.REVOKED
                    sess.revoked_at = datetime.now(timezone.utc)
                    sess.revocation_reason = reason
                    count += 1
            return count

    def revoke_device_sessions(self, device_id: str, reason: RevocationReason) -> int:
        """Revokes all sessions tied to a deactivated hardware device."""
        with self._lock:
            sids = self._device_index.get(device_id, set())
            count = 0
            for sid in sids:
                sess = self._sessions.get(sid)
                if sess and sess.status == SessionStatus.ACTIVE:
                    sess.status = SessionStatus.REVOKED
                    sess.revoked_at = datetime.now(timezone.utc)
                    sess.revocation_reason = reason
                    count += 1
            return count

    def revoke_license_sessions(self, license_id: str, reason: RevocationReason) -> int:
        """Revokes all sessions linked to a revoked or expired license."""
        with self._lock:
            sids = self._license_index.get(license_id, set())
            count = 0
            for sid in sids:
                sess = self._sessions.get(sid)
                if sess and sess.status == SessionStatus.ACTIVE:
                    sess.status = SessionStatus.REVOKED
                    sess.revoked_at = datetime.now(timezone.utc)
                    sess.revocation_reason = reason
                    count += 1
            return count

    def sweep_expired_sessions(self, now: Optional[datetime] = None) -> int:
        """Identifies and transitions idle or absolute-expired sessions."""
        with self._lock:
            check_time = now or datetime.now(timezone.utc)
            count = 0
            for sess in self._sessions.values():
                if sess.status == SessionStatus.ACTIVE:
                    if check_time > sess.absolute_expires_at:
                        sess.status = SessionStatus.EXPIRED
                        sess.revoked_at = check_time
                        sess.revocation_reason = RevocationReason.ABSOLUTE_TIMEOUT
                        count += 1
                    elif check_time > sess.idle_expires_at:
                        sess.status = SessionStatus.EXPIRED
                        sess.revoked_at = check_time
                        sess.revocation_reason = RevocationReason.IDLE_TIMEOUT
                        count += 1
            return count

    def clear(self) -> None:
        """Reset repository for tests."""
        with self._lock:
            self._sessions.clear()
            self._access_hash_index.clear()
            self._family_index.clear()
            self._evaluator_index.clear()
            self._device_index.clear()
            self._license_index.clear()


session_repository = SessionRepository()
