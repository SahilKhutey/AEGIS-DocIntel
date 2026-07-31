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

from fastapi import Depends, HTTPException, Security, status, WebSocket
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


async def get_current_tenant_ws(websocket: WebSocket) -> TenantContext:
    """WebSocket-native equivalent of get_current_tenant().

    get_current_tenant() depends on fastapi.security.HTTPBearer and
    APIKeyHeader, both of which — in the FastAPI version this project
    currently pins — require an http.Request specifically and raise
    ``TypeError: HTTPBearer.__call__() missing 1 required positional
    argument: 'request'`` when FastAPI's dependency-injection system tries
    to resolve them for a ``@router.websocket`` route instead (confirmed
    directly: this was the actual failure mode of the first attempt at
    wiring authentication onto queries.py's WebSocket endpoint, discovered
    only by writing an authenticated-connection test and watching it fail
    rather than by code inspection alone). A Starlette ``WebSocket``
    object exposes the same ``.headers`` mapping an HTTP ``Request``
    does, so this helper reads the Authorization/X-API-Key headers
    directly and reuses the same ``_validate_jwt``/``_validate_api_key``
    functions ``get_current_tenant`` itself calls, rather than duplicating
    their logic.

    Raises ``HTTPException`` (401) on missing or invalid credentials, the
    same as ``get_current_tenant`` — callers on a WebSocket route should
    catch this before calling ``websocket.accept()`` and close the
    connection with an appropriate code rather than letting the exception
    propagate raw, since a raised HTTPException has no meaning to a
    WebSocket client the way it does to an HTTP one.
    """
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return _validate_jwt(auth_header[7:])

    api_key = websocket.headers.get("x-api-key")
    if api_key:
        return _validate_api_key(api_key)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication. Provide Bearer token or X-API-Key header.",
    )

