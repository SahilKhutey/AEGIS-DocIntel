"""JWT (HS256 default; RS256 ready) issuance and verification."""

from __future__ import annotations

import enum
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

import jwt

from amdi.config import get_settings

logger = logging.getLogger("amdi.security.auth")


class AuthError(enum.Enum):
    MISSING = "missing_token"
    BAD_FORMAT = "bad_format"
    BAD_SIGNATURE = "bad_signature"
    EXPIRED = "expired"
    BAD_AUDIENCE = "bad_audience"
    BAD_ISSUER = "bad_issuer"
    REVOKED = "revoked"
    INSUFFICIENT_SCOPE = "insufficient_scope"


@dataclass(slots=True)
class Principal:
    user_id: str
    roles: tuple[str, ...]
    scopes: tuple[str, ...]
    raw: dict[str, Any]

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes


@dataclass
class VerificationFailure:
    error: AuthError
    detail: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"code": self.error.value, "detail": self.detail}


class JWTIssuer:
    """Mints tokens. Use only from login / service-to-service edges."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def issue(
        self,
        *,
        user_id: str,
        roles: tuple[str, ...] = (),
        scopes: tuple[str, ...] = (),
        ttl_seconds: int | None = None,
        audience: str | None = None,
        issuer: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> str:
        now = int(time.time())
        ttl = ttl_seconds if ttl_seconds is not None else self._settings.jwt_ttl_minutes * 60
        aud = audience or "amdi-cli"
        iss = issuer or "amdi-issuer"
        payload: dict[str, Any] = {
            "sub": user_id,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "nbf": now,
            "exp": now + ttl,
            "aud": aud,
            "iss": iss,
            "roles": list(roles),
            "scopes": list(scopes),
        }
        if extra:
            payload.update(extra)

        return jwt.encode(
            payload,
            self._settings.jwt_secret,
            algorithm=self._settings.jwt_algorithm,
        )


class JWTVerifier:
    """Verifies tokens. Stateless and thread-safe."""

    def __init__(
        self,
        *,
        audience: str = "amdi-cli",
        issuer: str = "amdi-issuer",
        revocation_check=None,
    ) -> None:
        self._aud = audience
        self._iss = issuer
        self._revocation_check = revocation_check

    def verify(self, token: str) -> Principal | VerificationFailure:
        if not token:
            return VerificationFailure(AuthError.MISSING)

        parts = token.split(".")
        if len(parts) != 3:
            return VerificationFailure(AuthError.BAD_FORMAT)

        settings = get_settings()
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                audience=self._aud,
                issuer=self._iss,
                options={"require": ["sub", "exp", "iat"]},
            )

        except jwt.ExpiredSignatureError:
            return VerificationFailure(AuthError.EXPIRED)
        except jwt.InvalidAudienceError:
            return VerificationFailure(AuthError.BAD_AUDIENCE)
        except jwt.InvalidIssuerError:
            return VerificationFailure(AuthError.BAD_ISSUER)
        except jwt.InvalidSignatureError:
            return VerificationFailure(AuthError.BAD_SIGNATURE)
        except jwt.PyJWTError as exc:
            return VerificationFailure(AuthError.BAD_SIGNATURE, str(exc))

        if self._revocation_check is not None:
            if self._revocation_check(payload.get("jti")):
                return VerificationFailure(AuthError.REVOKED)

        return Principal(
            user_id=str(payload["sub"]),
            roles=tuple(payload.get("roles", ())),
            scopes=tuple(payload.get("scopes", ())),
            raw=payload,
        )


__all__ = [
    "AuthError",
    "Principal",
    "VerificationFailure",
    "JWTIssuer",
    "JWTVerifier",
]
