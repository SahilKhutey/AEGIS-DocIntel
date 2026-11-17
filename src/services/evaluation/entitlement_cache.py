"""
src/services/evaluation/entitlement_cache.py
============================================
Short-lived, revision-aware cache for evaluation entitlement decisions.
Complies with PROT-04 WP-04.05 specification.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple


class EntitlementCache:
    """Revision-aware cache. Stale entries are immediately invalidated when revision increments."""

    def __init__(self, ttl_seconds: float = 60.0) -> None:
        self._ttl = ttl_seconds
        # (license_id, feature, permission) -> (allowed, reason_code, revision, expire_time)
        self._cache: Dict[Tuple[str, str, str], Tuple[bool, str, int, float]] = {}

    def get(
        self,
        *,
        license_id: str,
        feature: str,
        permission: str,
        current_revision: int,
    ) -> Optional[Tuple[bool, str]]:
        key = (license_id, feature, permission)
        entry = self._cache.get(key)
        if not entry:
            return None

        allowed, reason_code, rev, expire_time = entry
        # Stale revision or expired TTL
        if rev != current_revision or time.time() >= expire_time:
            self._cache.pop(key, None)
            return None

        return (allowed, reason_code)

    def set(
        self,
        *,
        license_id: str,
        feature: str,
        permission: str,
        allowed: bool,
        reason_code: str,
        revision: int,
    ) -> None:
        key = (license_id, feature, permission)
        expire_time = time.time() + self._ttl
        self._cache[key] = (allowed, reason_code, revision, expire_time)

    def invalidate(self, license_id: Optional[str] = None) -> None:
        if license_id:
            to_remove = [k for k in self._cache.keys() if k[0] == license_id]
            for k in to_remove:
                self._cache.pop(k, None)
        else:
            self._cache.clear()

    def clear(self) -> None:
        self._cache.clear()
