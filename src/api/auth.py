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


import logging
import os

logger = logging.getLogger("aegis.api.auth")
if os.environ.get("AEGIS_ENVIRONMENT", "production").lower() == "development":
    logger.warning(
        "SECURITY WARNING: AEGIS_ENVIRONMENT=development active. "
        "Development auth-bypass credentials ('dev-*', 'aegis-dev-key') are ENABLED."
    )


def _validate_jwt(token: str) -> TenantContext:
    """
    Validate RS256 JWT token.
    In development: accept 'dev-{tenant_id}' tokens when explicitly enabled.
    In production: validate RS256 JWT via PyJWT with public key.
    """
    from src.observability.audit_logger import audit_logger

    env = os.environ.get("AEGIS_ENVIRONMENT", "production").lower()
    if env == "development" and token.startswith("dev-"):
        tenant_id = token[4:] or "default-tenant"
        return TenantContext(
            tenant_id=tenant_id,
            user_id="dev-user",
            role="admin",
        )

    # Production / non-dev: decode and verify JWT using PyJWT
    try:
        import jwt
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PyJWT not installed. Cannot validate JWT.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    public_key = os.environ.get("AEGIS_JWT_PUBLIC_KEY")
    if not public_key:
        key_path = os.environ.get("AEGIS_JWT_PUBLIC_KEY_PATH")
        if key_path and os.path.isfile(key_path):
            with open(key_path, "r", encoding="utf-8") as f:
                public_key = f.read()

    if not public_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT validation not configured: public key missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    algorithms = ["RS256"]
    if not any(header in public_key for header in ("BEGIN PUBLIC KEY", "BEGIN RSA PUBLIC KEY", "BEGIN CERTIFICATE")):
        algorithms.append("HS256")

    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=algorithms,
            options={"require": ["exp"]},
        )
    except jwt.ExpiredSignatureError:
        audit_logger.log(
            action="auth.jwt_expired",
            tenant_id="unknown",
            user_id="anonymous",
            status="FAILURE",
            detail={"error": "Token has expired"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="The token has expired"'},
        )
    except jwt.InvalidTokenError as e:
        audit_logger.log(
            action="auth.jwt_invalid",
            tenant_id="unknown",
            user_id="anonymous",
            status="FAILURE",
            detail={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    tenant_id = payload.get("tenant_id") or payload.get("tid")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing tenant_id claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub") or payload.get("user_id") or "anonymous-user"
    role = payload.get("role") or "viewer"

    audit_logger.log(
        action="auth.jwt_success",
        tenant_id=str(tenant_id),
        user_id=str(user_id),
        status="SUCCESS",
        detail={"role": role},
    )

    return TenantContext(
        tenant_id=str(tenant_id),
        user_id=str(user_id),
        role=str(role),
    )


def _validate_api_key(api_key: str) -> TenantContext:
    """
    Validate API key.
    In development: accept 'aegis-dev-key' when explicitly enabled.
    In production: hash lookup against secure store or configured keys.
    """
    import hmac
    from src.observability.audit_logger import audit_logger

    env = os.environ.get("AEGIS_ENVIRONMENT", "production").lower()
    if env == "development" and api_key == "aegis-dev-key":
        return TenantContext(
            tenant_id="default-tenant",
            user_id="api-user",
            role="editor",
        )

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    raw_keys = os.environ.get("AEGIS_API_KEYS")
    if raw_keys:
        try:
            import json
            keys_map = json.loads(raw_keys)
            if isinstance(keys_map, dict):
                for stored_k, meta in keys_map.items():
                    stored_hash = hashlib.sha256(stored_k.encode()).hexdigest() if len(stored_k) != 64 else stored_k
                    if hmac.compare_digest(key_hash, stored_hash) or hmac.compare_digest(api_key, stored_k):
                        if isinstance(meta, dict):
                            tenant_id = str(meta.get("tenant_id", "default-tenant"))
                            user_id = str(meta.get("user_id", "api-user"))
                            role = str(meta.get("role", "editor"))
                        else:
                            tenant_id = str(meta)
                            user_id = "api-user"
                            role = "editor"

                        audit_logger.log(
                            action="auth.api_key_success",
                            tenant_id=tenant_id,
                            user_id=user_id,
                            status="SUCCESS",
                            detail={"role": role},
                        )
                        return TenantContext(
                            tenant_id=tenant_id,
                            user_id=user_id,
                            role=role,
                        )
        except Exception as e:
            logger.warning("Failed to parse AEGIS_API_KEYS: %s", e)

    audit_logger.log(
        action="auth.api_key_failure",
        tenant_id="unknown",
        user_id="anonymous",
        status="FAILURE",
        detail={"key_prefix": api_key[:6] if len(api_key) >= 6 else "***"},
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"},
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

