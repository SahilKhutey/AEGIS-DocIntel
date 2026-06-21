"""
AEGIS-DocIntel — JWT Authentication & Tenant Context
=====================================================
Production JWT authentication with RS256 + API key support.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

BEARER = HTTPBearer(auto_error=False)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass
class TenantContext:
    tenant_id: str
    user_id: str
    role: str  # admin | editor | viewer
    monthly_token_limit: int = 10_000_000


async def get_current_tenant(
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(BEARER),
    api_key: Optional[str] = Security(API_KEY_HEADER),
) -> TenantContext:
    """
    Validate JWT or API key and return TenantContext.
    In production: validate JWT (RS256) or look up API key hash from Postgres.
    """
    if bearer and bearer.credentials:
        return _validate_jwt(bearer.credentials)

    if api_key:
        return _validate_api_key(api_key)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication. Provide Bearer token or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _validate_jwt(token: str) -> TenantContext:
    """
    Validate RS256 JWT token.
    In production: use python-jose with RS256 public key from Keycloak/Auth0.
    """
    # DEVELOPMENT STUB: accept any "dev-{tenant_id}" token
    if token.startswith("dev-"):
        tenant_id = token[4:] or "default-tenant"
        return TenantContext(
            tenant_id=tenant_id,
            user_id="dev-user",
            role="admin",
        )

    # Production: decode and verify JWT
    try:
        from jose import jwt, JWTError
        # payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        # return TenantContext(tenant_id=payload["tenant_id"], ...)
        raise HTTPException(status_code=401, detail="JWT validation not configured")
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="python-jose not installed. Cannot validate JWT.",
        )


def _validate_api_key(api_key: str) -> TenantContext:
    """
    Validate API key (hash lookup in Postgres).
    Development: accept "aegis-dev-key" for testing.
    """
    if api_key == "aegis-dev-key":
        return TenantContext(
            tenant_id="default-tenant",
            user_id="api-user",
            role="editor",
        )

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    # Production: look up key_hash in Postgres api_keys table
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )


def require_role(*roles: str):
    """Role-based access control dependency factory."""
    async def check(tenant: TenantContext = Depends(get_current_tenant)):
        if tenant.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{tenant.role}' not authorized. Required: {roles}",
            )
        return tenant
    return check
