"""
AEGIS-DocIntel Cryptographic Key & Secret Rotation Service (PROT-04 WP-04.08)
Coordinates scheduled key rotation, emergency compromise handling, and API key lifecycles.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from typing import Any, Dict, Optional, Tuple

from services.evaluation_gateway.signing_key_registry import key_registry
from src.repositories.security_operations.key_metadata_repository import (
    KeyMetadataRepository,
    KeyStatus,
    key_metadata_repository,
)
from src.services.security_operations.security_event_service import (
    SecurityEventService,
    security_event_service,
)

logger = logging.getLogger("aegis.security.keys")


class KeyRotationService:
    def __init__(
        self,
        meta_repo: Optional[KeyMetadataRepository] = None,
        event_svc: Optional[SecurityEventService] = None,
    ):
        self._meta_repo = meta_repo or key_metadata_repository
        self._event_svc = event_svc or security_event_service
        self._active_api_keys: Dict[str, str] = {}  # key_id -> hash

    def register_api_key(self, key_id: str, raw_key: str) -> None:
        """Stores hashed API key."""
        khash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        self._active_api_keys[key_id] = khash

    def validate_api_key(self, key_id: str, raw_key: str) -> bool:
        """Validates API key presentation against hash."""
        khash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return self._active_api_keys.get(key_id) == khash

    def rotate_api_key(self, key_id: str) -> str:
        """
        Rotates an API key (IR-003).
        Issues new high-entropy key and invalidates the previous secret immediately.
        """
        new_secret = f"aegis_key_{secrets.token_urlsafe(32)}"
        self.register_api_key(key_id, new_secret)
        self._event_svc.emit_event(
            event_type="SECRET_ROTATION",
            result="success",
            details={"key_id": key_id, "action": "api_key_rotated"},
        )
        return new_secret

    def rotate_license_signing_key(self) -> Tuple[str, str]:
        """
        Rotates Ed25519 license signing key (IR-004, MON-006).
        Old key moves to VERIFY_ONLY (allowing circulating licenses to verify); new key becomes ACTIVE_SIGNING.
        Returns: (new_kid, new_public_key_pem)
        """
        old_kid = key_registry._active_key_id or "unknown"
        new_record = key_registry.rotate_key()
        new_kid = new_record.key_id
        pub_key = new_record.public_key_pem

        self._meta_repo.rotate_key(old_kid, new_kid)
        self._meta_repo.register_key(
            kid=new_kid,
            algorithm="Ed25519",
            purpose="evaluation_license_signing",
            fingerprint=f"fp-{new_kid}",
            status=KeyStatus.ACTIVE,
        )

        self._event_svc.emit_event(
            event_type="KEY_ROTATION",
            result="success",
            details={"old_kid": old_kid, "new_kid": new_kid},
        )

        logger.info("Rotated signing key: old=%s, new=%s", old_kid, new_kid)
        return new_kid, pub_key

    def emergency_compromise_key(self, kid: str) -> None:
        """
        Emergency response to suspected signing key leak (IR-02).
        Atomically invalidates signing key and all tokens signed by it.
        """
        key_registry.compromise_key(kid)
        self._meta_repo.compromise_key(kid)

        self._event_svc.emit_event(
            event_type="KEY_COMPROMISE_REPORTED",
            result="critical",
            details={"compromised_kid": kid},
        )
        logger.critical("Emergency compromise recorded for key '%s'", kid)


key_rotation_service = KeyRotationService()
