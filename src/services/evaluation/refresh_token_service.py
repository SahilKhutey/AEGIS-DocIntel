"""
AEGIS-DocIntel Refresh Token Utility Service (PROT-04 WP-04.07)
Provides cryptographic generation and secure hashing for evaluation credentials.
CRITICAL: Plaintext refresh tokens are never persisted or logged.
"""

from __future__ import annotations

import hashlib
import secrets


def hash_token(raw_token: str) -> str:
    """Computes a SHA-256 cryptographic digest of a token secret."""
    cleaned = (raw_token or "").strip()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


def generate_refresh_token() -> str:
    """
    Generates a high-entropy, cryptographically secure opaque refresh token.
    Uses 48 bytes (384 bits) of entropy, URL-safe base64 encoded.
    """
    random_secret = secrets.token_urlsafe(48)
    return f"aegis_eval_rt_{random_secret}"


def generate_access_token() -> str:
    """
    Generates a high-entropy opaque access token.
    Uses 32 bytes (256 bits) of entropy.
    """
    random_secret = secrets.token_urlsafe(32)
    return f"aegis_eval_at_{random_secret}"
