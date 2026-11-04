"""
aegis.security.auth.verifier
============================
Enterprise Authentication Verification Engine:
- RS256 JWT validation, cryptographic signature verification, claim enforcement.
- Token tampering, expiration, and invalid signature detection.
- API Key constant-time SHA-256 validation.
- Revoked token / session checking.
- Rate limiting / failed login attempt lockout protection.
- One-time password reset token enforcement.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import jwt


class AuthVerifier:
    """Production-grade authentication validator and test harness."""

    def __init__(self, key_size: int = 2048) -> None:
        # Generate in-memory RSA key pair for testing
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        self._public_key = self._private_key.public_key()
        self.public_pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        # Second key pair to simulate invalid signature attacks
        self._attacker_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )

        # State stores
        self.revoked_tokens: Set[str] = set()
        self.revoked_sessions: Set[str] = set()
        self.disabled_accounts: Set[str] = set()
        self.used_reset_tokens: Set[str] = set()
        self.api_keys: Dict[str, Dict[str, Any]] = {}  # sha256_hash -> metadata
        self.failed_attempts: Dict[str, List[float]] = {}
        self.lockout_threshold = 5
        self.lockout_window_seconds = 300.0

    def register_api_key(self, raw_key: str, tenant_id: str, principal_id: str, roles: List[str]) -> str:
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        self.api_keys[key_hash] = {
            "tenant_id": tenant_id,
            "principal_id": principal_id,
            "roles": roles,
            "active": True,
        }
        return key_hash

    def issue_jwt(
        self,
        principal_id: str,
        tenant_id: str,
        roles: List[str],
        expires_in_seconds: int = 3600,
        custom_claims: Optional[Dict[str, Any]] = None,
        use_attacker_key: bool = False,
    ) -> str:
        now = int(time.time())
        payload = {
            "sub": principal_id,
            "tenant_id": tenant_id,
            "roles": roles,
            "iat": now,
            "exp": now + expires_in_seconds,
            "jti": hashlib.sha256(f"{principal_id}-{tenant_id}-{now}".encode("utf-8")).hexdigest()[:16],
        }
        if custom_claims:
            payload.update(custom_claims)

        signing_key = self._attacker_private_key if use_attacker_key else self._private_key
        token = jwt.encode(payload, signing_key, algorithm="RS256")
        return token

    def record_failed_attempt(self, identifier: str) -> bool:
        """Records a failed attempt. Returns True if identifier is locked out."""
        now = time.time()
        attempts = self.failed_attempts.setdefault(identifier, [])
        # Filter attempts within window
        attempts = [t for t in attempts if now - t < self.lockout_window_seconds]
        attempts.append(now)
        self.failed_attempts[identifier] = attempts
        return len(attempts) >= self.lockout_threshold

    def is_locked_out(self, identifier: str) -> bool:
        now = time.time()
        attempts = [t for t in self.failed_attempts.get(identifier, []) if now - t < self.lockout_window_seconds]
        return len(attempts) >= self.lockout_threshold

    def reset_failed_attempts(self, identifier: str) -> None:
        self.failed_attempts.pop(identifier, None)

    def revoke_token(self, jti_or_token: str) -> None:
        self.revoked_tokens.add(jti_or_token)

    def revoke_session(self, session_id: str) -> None:
        self.revoked_sessions.add(session_id)

    def disable_account(self, principal_id: str) -> None:
        self.disabled_accounts.add(principal_id)

    def use_password_reset_token(self, token: str) -> Tuple[bool, str]:
        if token in self.used_reset_tokens:
            return False, "Password reset token already used"
        self.used_reset_tokens.add(token)
        return True, "Password reset token accepted"

    def verify_token(self, token: Optional[str]) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        if not token or not token.strip():
            return False, None, "Missing authentication credentials"

        if token in self.revoked_tokens:
            return False, None, "Token has been revoked"

        try:
            payload = jwt.decode(
                token,
                self.public_pem,
                algorithms=["RS256"],
                options={"require": ["sub", "exp", "tenant_id"], "verify_signature": True},
                leeway=30,
            )
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidSignatureError:
            return False, None, "Invalid token signature"
        except jwt.DecodeError:
            return False, None, "Malformed or tampered token"
        except jwt.InvalidTokenError as exc:
            return False, None, f"Invalid token: {exc}"

        # JTI revocation check
        jti = payload.get("jti")
        if jti and jti in self.revoked_tokens:
            return False, None, "Token has been revoked"

        # Session revocation check
        sid = payload.get("sid")
        if sid and sid in self.revoked_sessions:
            return False, None, "Session has been invalidated"

        # Disabled account check
        sub = payload.get("sub")
        if sub and sub in self.disabled_accounts:
            return False, None, "User account is disabled"

        return True, payload, "Authenticated"

    def verify_api_key(self, api_key: Optional[str]) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        if not api_key or not api_key.strip():
            return False, None, "Missing API key"

        key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        for stored_hash, record in self.api_keys.items():
            if hmac.compare_digest(key_hash, stored_hash):
                if not record.get("active", False):
                    return False, None, "API key inactive or revoked"
                return True, record, "Authenticated"

        return False, None, "Invalid API key"
