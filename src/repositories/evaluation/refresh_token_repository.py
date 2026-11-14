"""
AEGIS-DocIntel Refresh Token Repository (PROT-04 WP-04.07)
Manages refresh token records, rotation status, and atomic replay detection.
Thread-safe and concurrency-hardened.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from src.schemas.evaluation.refresh import EvaluationRefreshToken, RefreshTokenStatus


class RefreshTokenRepository:
    """
    Authoritative repository for opaque refresh token hashes.
    Guarantees strict atomic rotation and immediate replay compromise detection.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._tokens: Dict[str, EvaluationRefreshToken] = {}
        self._hash_index: Dict[str, str] = {}  # token_hash -> token_id
        self._family_index: Dict[str, Set[str]] = {}  # family_id -> set of token_id
        self._used_hashes: Dict[str, str] = {}  # token_hash -> family_id (consumed tokens)

    def save_token(self, token: EvaluationRefreshToken) -> EvaluationRefreshToken:
        with self._lock:
            self._tokens[token.token_id] = token
            self._hash_index[token.token_hash] = token.token_id
            if token.family_id not in self._family_index:
                self._family_index[token.family_id] = set()
            self._family_index[token.family_id].add(token.token_id)
            return token

    def get_by_hash(self, token_hash: str) -> Optional[EvaluationRefreshToken]:
        with self._lock:
            tid = self._hash_index.get(token_hash)
            if not tid:
                return None
            return self._tokens.get(tid)

    def get_by_id(self, token_id: str) -> Optional[EvaluationRefreshToken]:
        with self._lock:
            return self._tokens.get(token_id)

    def is_hash_consumed(self, token_hash: str) -> Optional[str]:
        """Returns the family_id if this hash was previously consumed (replay indicator)."""
        with self._lock:
            return self._used_hashes.get(token_hash)

    def atomic_rotate(
        self,
        old_hash: str,
        new_token: EvaluationRefreshToken,
        now: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[EvaluationRefreshToken], str]:
        """
        Atomically executes refresh token rotation:
        - If old_hash was already consumed -> REPLAY_DETECTED (returns family_id).
        - If old_hash does not exist -> NOT_FOUND.
        - If old token is revoked/expired/consumed -> INVALID_STATE / REPLAY_DETECTED.
        - Otherwise, marks old token CONSUMED, saves new token, records in used_hashes.

        Under high concurrency (e.g. 20 racing threads), exactly 1 thread succeeds;
        all others observe consumed state and fail immediately.
        """
        with self._lock:
            curr_time = now or datetime.now(timezone.utc)

            # 1. Check if hash was already marked consumed in historical ledger
            if old_hash in self._used_hashes:
                fam_id = self._used_hashes[old_hash]
                return False, None, f"REPLAY_DETECTED:{fam_id}"

            tid = self._hash_index.get(old_hash)
            if not tid:
                return False, None, "NOT_FOUND"

            old_tok = self._tokens.get(tid)
            if not old_tok:
                return False, None, "NOT_FOUND"

            if old_tok.status == RefreshTokenStatus.CONSUMED:
                # Concurrent race condition or prior consumption
                self._used_hashes[old_hash] = old_tok.family_id
                return False, None, f"REPLAY_DETECTED:{old_tok.family_id}"

            if old_tok.status == RefreshTokenStatus.REVOKED:
                return False, None, "REVOKED"

            if curr_time > old_tok.expires_at:
                old_tok.status = RefreshTokenStatus.EXPIRED
                return False, None, "EXPIRED"

            if old_tok.status != RefreshTokenStatus.ACTIVE:
                return False, None, f"INVALID_STATUS:{old_tok.status}"

            # Atomic transition to CONSUMED
            old_tok.status = RefreshTokenStatus.CONSUMED
            old_tok.consumed_at = curr_time
            old_tok.replaced_by_id = new_token.token_id
            self._used_hashes[old_hash] = old_tok.family_id

            # Save new active token
            self.save_token(new_token)
            return True, new_token, "SUCCESS"

    def revoke_family(self, family_id: str, reason: str = "token_family_compromise") -> int:
        """Revokes all tokens in a family."""
        with self._lock:
            tids = self._family_index.get(family_id, set())
            count = 0
            now = datetime.now(timezone.utc)
            for tid in tids:
                tok = self._tokens.get(tid)
                if tok and tok.status in (RefreshTokenStatus.ACTIVE, RefreshTokenStatus.CONSUMED):
                    tok.status = RefreshTokenStatus.REVOKED
                    tok.revoked_at = now
                    tok.revocation_reason = reason
                    count += 1
            return count

    def clear(self) -> None:
        """Reset repository for tests."""
        with self._lock:
            self._tokens.clear()
            self._hash_index.clear()
            self._family_index.clear()
            self._used_hashes.clear()


refresh_token_repository = RefreshTokenRepository()
