"""
AEGIS-DocIntel Cryptographic Key Metadata Repository (PROT-04 WP-04.08)
Tracks lifecycle, rotation history, and compromise records for server-side signing keys.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class KeyStatus(str, Enum):
    ACTIVE = "active"
    VERIFY_ONLY = "verify_only"
    RETIRED = "retired"
    COMPROMISED = "compromised"


@dataclass
class KeyMetadataRecord:
    kid: str
    algorithm: str
    purpose: str
    status: KeyStatus
    fingerprint: str
    created_at: datetime
    rotated_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class KeyMetadataRepository:
    def __init__(self):
        self._lock = threading.RLock()
        self._keys: Dict[str, KeyMetadataRecord] = {}

    def register_key(
        self,
        kid: str,
        algorithm: str,
        purpose: str,
        fingerprint: str,
        status: KeyStatus = KeyStatus.ACTIVE,
    ) -> KeyMetadataRecord:
        with self._lock:
            rec = KeyMetadataRecord(
                kid=kid,
                algorithm=algorithm,
                purpose=purpose,
                status=status,
                fingerprint=fingerprint,
                created_at=datetime.now(timezone.utc),
            )
            self._keys[kid] = rec
            return rec

    def rotate_key(self, old_kid: str, new_kid: str) -> None:
        with self._lock:
            old = self._keys.get(old_kid)
            now = datetime.now(timezone.utc)
            if old:
                old.status = KeyStatus.VERIFY_ONLY
                old.rotated_at = now

    def compromise_key(self, kid: str) -> KeyMetadataRecord:
        with self._lock:
            rec = self._keys.get(kid)
            if not rec:
                raise KeyError(f"Key '{kid}' not found.")
            rec.status = KeyStatus.COMPROMISED
            rec.revoked_at = datetime.now(timezone.utc)
            return rec

    def get_key(self, kid: str) -> Optional[KeyMetadataRecord]:
        with self._lock:
            return self._keys.get(kid)

    def list_keys(self) -> List[KeyMetadataRecord]:
        with self._lock:
            return list(self._keys.values())

    def clear(self) -> None:
        with self._lock:
            self._keys.clear()


key_metadata_repository = KeyMetadataRepository()
