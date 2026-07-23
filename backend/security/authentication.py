"""
Authentication
================

JWT-based authentication + API keys + password hashing.

Mathematical Foundation:
    JWT = base64url(header) + "." + base64url(payload) + "." + base64url(signature)
    signature = HMAC-SHA256(secret, header + "." + payload)

    Password hashing: bcrypt / scrypt / argon2
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .exceptions import AuthenticationError
from .hash_compat import hash_password as _hash_pw, verify_password as _verify_pw


class AuthMethod(Enum):
    PASSWORD = "password"
    API_KEY = "api_key"
    JWT = "jwt"
    OAUTH = "oauth"


@dataclass
class User:
    """An authenticated user."""

    user_id: str
    username: str
    email: str
    password_hash: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    api_keys: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: Optional[str] = None
    is_active: bool = True
    is_locked: bool = False
    failed_login_attempts: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "mfa_enabled": self.mfa_enabled,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "is_active": self.is_active,
        }


@dataclass
class APIKey:
    """An API key."""

    key_id: str
    hashed_key: str
    user_id: str
    name: str
    scopes: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    last_used: Optional[str] = None
    is_revoked: bool = False

    def to_dict(self) -> dict:
        return {
            "key_id": self.key_id,
            "user_id": self.user_id,
            "name": self.name,
            "scopes": self.scopes,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_used": self.last_used,
            "is_revoked": self.is_revoked,
        }


@dataclass
class AuthToken:
    """An authentication token (JWT)."""

    token: str
    token_type: str = "Bearer"
    user_id: str = ""
    username: str = ""
    roles: List[str] = field(default_factory=list)
    expires_at: float = 0
    issued_at: float = 0
    scopes: List[str] = field(default_factory=list)

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    def to_dict(self) -> dict:
        return {
            "token": self.token,
            "token_type": self.token_type,
            "user_id": self.user_id,
            "username": self.username,
            "roles": self.roles,
            "expires_at": self.expires_at,
            "issued_at": self.issued_at,
            "scopes": self.scopes,
        }


class AuthenticationManager:
    """
    Manages users, API keys, and JWT tokens.
    """

    DEFAULT_TOKEN_LIFETIME = 3600  # 1 hour
    DEFAULT_API_KEY_LENGTH = 32
    MAX_FAILED_ATTEMPTS = 5

    def __init__(
        self,
        jwt_secret: Optional[str] = None,
        jwt_algorithm: str = "HS256",
        token_lifetime: int = DEFAULT_TOKEN_LIFETIME,
    ) -> None:
        self.jwt_secret = jwt_secret or secrets.token_urlsafe(64)
        self.jwt_algorithm = jwt_algorithm
        self.token_lifetime = token_lifetime
        self.users: Dict[str, User] = {}  # by user_id
        self.users_by_name: Dict[str, str] = {}  # username -> user_id
        self.api_keys: Dict[str, APIKey] = {}  # by key_id
        self.api_key_lookup: Dict[str, str] = {}  # hashed_key -> key_id
        self._revoked_tokens: set = set()

    # ========================================================================
    # User Management
    # ========================================================================

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: Optional[List[str]] = None,
        mfa_enabled: bool = False,
    ) -> User:
        """Create a new user with hashed password."""
        if username in self.users_by_name:
            raise AuthenticationError(f"Username '{username}' already exists")
        user_id = secrets.token_urlsafe(16)
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=_hash_pw(password),
            roles=roles or ["viewer"],
            mfa_enabled=mfa_enabled,
        )
        self.users[user_id] = user
        self.users_by_name[username] = user_id
        return user

    def authenticate_password(
        self,
        username: str,
        password: str,
        mfa_code: Optional[str] = None,
    ) -> AuthToken:
        """Authenticate user with username + password (+ optional MFA)."""
        user_id = self.users_by_name.get(username)
        if user_id is None:
            raise AuthenticationError("Invalid credentials")
        user = self.users[user_id]
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        if user.is_locked:
            raise AuthenticationError("User account is locked")
        if user.password_hash is None or not _verify_pw(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
                user.is_locked = True
            raise AuthenticationError("Invalid credentials")
        # MFA check
        if user.mfa_enabled:
            if mfa_code is None:
                raise AuthenticationError("MFA code required")
            if not self._verify_mfa(user, mfa_code):
                raise AuthenticationError("Invalid MFA code")
        # success
        user.failed_login_attempts = 0
        user.last_login = datetime.now(timezone.utc).isoformat()
        return self.create_token(user)

    def _verify_mfa(self, user: User, code: str) -> bool:
        """Verify TOTP code (RFC 6238)."""
        if user.mfa_secret is None:
            return False
        # Simple time-based code (production: use `pyotp`)
        import struct
        try:
            t = int(time.time() // 30)
            key = base64.b32decode(user.mfa_secret)
            # generate code for current + adjacent time steps
            for offset in [-1, 0, 1]:
                msg = struct.pack(">Q", t + offset)
                h = hmac.new(key, msg, hashlib.sha1).digest()
                offset_byte = h[-1] & 0x0F
                truncated = (
                    (h[offset_byte] & 0x7F) << 24
                    | (h[offset_byte + 1] & 0xFF) << 16
                    | (h[offset_byte + 2] & 0xFF) << 8
                    | (h[offset_byte + 3] & 0xFF)
                ) % 10**6
                if f"{truncated:06d}" == code:
                    return True
            return False
        except Exception:
            return False

    # ========================================================================
    # JWT Tokens
    # ========================================================================

    def create_token(
        self,
        user: User,
        scopes: Optional[List[str]] = None,
        lifetime: Optional[int] = None,
    ) -> AuthToken:
        """Create a JWT token for a user."""
        now = time.time()
        exp = now + (lifetime or self.token_lifetime)
        payload = {
            "sub": user.user_id,
            "username": user.username,
            "roles": user.roles,
            "scopes": scopes or [],
            "iat": now,
            "exp": exp,
            "jti": secrets.token_urlsafe(16),
        }
        token = self._encode_jwt(payload)
        return AuthToken(
            token=token,
            user_id=user.user_id,
            username=user.username,
            roles=user.roles,
            expires_at=exp,
            issued_at=now,
            scopes=scopes or [],
        )

    def verify_token(self, token: str) -> AuthToken:
        """Verify and decode a JWT token."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise AuthenticationError("Invalid token format")
            header_b64, payload_b64, sig_b64 = parts
            # verify signature
            signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            expected_sig = hmac.new(
                self.jwt_secret.encode("utf-8"),
                signing_input,
                hashlib.sha256,
            ).digest()
            actual_sig = self._b64url_decode(sig_b64)
            if not hmac.compare_digest(expected_sig, actual_sig):
                raise AuthenticationError("Invalid signature")
            # decode payload
            payload = json.loads(self._b64url_decode(payload_b64))
            # expiration
            if time.time() >= payload.get("exp", 0):
                raise AuthenticationError("Token expired")
            # revoked?
            jti = payload.get("jti", "")
            if jti in self._revoked_tokens:
                raise AuthenticationError("Token revoked")
            return AuthToken(
                token=token,
                user_id=payload.get("sub", ""),
                username=payload.get("username", ""),
                roles=payload.get("roles", []),
                expires_at=payload.get("exp", 0),
                issued_at=payload.get("iat", 0),
                scopes=payload.get("scopes", []),
            )
        except AuthenticationError:
            raise
        except Exception as exc:
            raise AuthenticationError(f"Token verification failed: {exc}") from exc

    def revoke_token(self, jti: str) -> None:
        """Revoke a JWT by its jti."""
        self._revoked_tokens.add(jti)

    def _encode_jwt(self, payload: Dict[str, Any]) -> str:
        """Encode a JWT (HS256)."""
        header = {"alg": self.jwt_algorithm, "typ": "JWT"}
        header_b64 = self._b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = self._b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        sig = hmac.new(
            self.jwt_secret.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        sig_b64 = self._b64url_encode(sig)
        return f"{header_b64}.{payload_b64}.{sig_b64}"

    @staticmethod
    def _b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    @staticmethod
    def _b64url_decode(data: str) -> bytes:
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data)

    # ========================================================================
    # API Keys
    # ========================================================================

    def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
    ) -> tuple:
        """Create an API key for a user. Returns (api_key_string, APIKey)."""
        if user_id not in self.users:
            raise AuthenticationError(f"User '{user_id}' not found")
        raw_key = secrets.token_urlsafe(self.DEFAULT_API_KEY_LENGTH)
        key_id = secrets.token_urlsafe(8)
        hashed = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        expires_at = None
        if expires_in_days:
            expires_at = (
                datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            ).isoformat()
        api_key = APIKey(
            key_id=key_id,
            hashed_key=hashed,
            user_id=user_id,
            name=name,
            scopes=scopes or [],
            expires_at=expires_at,
        )
        self.api_keys[key_id] = api_key
        self.api_key_lookup[hashed] = key_id
        # also store raw key on user for convenience
        self.users[user_id].api_keys.append(key_id)
        return raw_key, api_key

    def verify_api_key(self, raw_key: str) -> AuthToken:
        """Verify an API key and return an AuthToken."""
        hashed = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        key_id = self.api_key_lookup.get(hashed)
        if key_id is None:
            raise AuthenticationError("Invalid API key")
        api_key = self.api_keys[key_id]
        if api_key.is_revoked:
            raise AuthenticationError("API key revoked")
        if api_key.expires_at:
            exp_dt = datetime.fromisoformat(api_key.expires_at)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            if exp_dt < datetime.now(timezone.utc):
                raise AuthenticationError("API key expired")
        api_key.last_used = datetime.now(timezone.utc).isoformat()
        user = self.users[api_key.user_id]
        return AuthToken(
            token=raw_key,
            token_type="ApiKey",
            user_id=user.user_id,
            username=user.username,
            roles=user.roles,
            expires_at=float("inf"),
            issued_at=time.time(),
            scopes=api_key.scopes,
        )

    def revoke_api_key(self, key_id: str) -> None:
        if key_id in self.api_keys:
            self.api_keys[key_id].is_revoked = True
