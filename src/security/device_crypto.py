"""
AEGIS-DocIntel Device Cryptography & Proof-of-Possession (PROT-FINAL-02 / REM-02)
Provides hardware key parsing, challenge nonce generation, fingerprint computation,
and digital signature verification for device registration and binding.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from typing import Any, Tuple

from services.evaluation_gateway.activation import (
    parse_and_validate_public_key,
    verify_device_signature,
    compute_key_fingerprint,
)


class DeviceCryptoService:
    @staticmethod
    def generate_challenge(ttl_seconds: int = 60) -> Tuple[str, str, float]:
        """
        Generates a cryptographic challenge nonce for device Proof-of-Possession.
        Returns (challenge_id, nonce_hex, expires_at_timestamp).
        """
        challenge_id = f"chal-{secrets.token_hex(16)}"
        nonce = secrets.token_hex(32)
        expires_at = time.time() + ttl_seconds
        return challenge_id, nonce, expires_at

    @staticmethod
    def parse_public_key(pub_key_str: str) -> Tuple[Any, bytes, str]:
        """Parses and validates PEM or Base64 raw/DER device public keys."""
        return parse_and_validate_public_key(pub_key_str)

    @staticmethod
    def verify_signature(pub_key_obj: Any, message_bytes: bytes, signature_b64: str) -> bool:
        """Verifies digital signature over canonical challenge message."""
        return verify_device_signature(pub_key_obj, message_bytes, signature_b64)

    @staticmethod
    def fingerprint_key(key_bytes: bytes) -> str:
        """Computes deterministic SHA-256 fingerprint for device public key."""
        return compute_key_fingerprint(key_bytes)


device_crypto = DeviceCryptoService()
