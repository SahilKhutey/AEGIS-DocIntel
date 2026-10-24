"""
AEGIS-DocIntel — JWT Authentication & Tenant Context
=====================================================
Production JWT authentication with RS256 + API key support.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Security, status, WebSocket
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

BEARER = HTTPBearer(auto_error=False)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

ALLOWED_ROLES: frozenset[str] = frozenset({"admin", "editor", "viewer"})
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


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
    In production: validate JWT (RS256) or look up API key hash from configuration/store.
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
    In production: validate RS256 JWT via PyJWT with verified RSA public key.
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

    # Cryptographically verify that the key is a valid RSA public key (not symmetric or malformed)
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        from cryptography.hazmat.primitives.asymmetric import rsa

        key_bytes = public_key.encode("utf-8") if isinstance(public_key, str) else public_key
        loaded_key = load_pem_public_key(key_bytes)
        if not isinstance(loaded_key, rsa.RSAPublicKey):
            raise ValueError("Configured key is not an RSA public key")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid RSA public key configuration: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    decode_options = {
        "require": ["exp", "sub"],
        "verify_signature": True,
    }
    jwt_issuer = os.environ.get("AEGIS_JWT_ISSUER")
    jwt_audience = os.environ.get("AEGIS_JWT_AUDIENCE")
    if jwt_issuer:
        decode_options["require"].append("iss")
    if jwt_audience:
        decode_options["require"].append("aud")

    decode_kwargs = {
        "algorithms": ["RS256"],
        "options": decode_options,
        "leeway": 30,
    }
    if jwt_issuer:
        decode_kwargs["issuer"] = jwt_issuer
    if jwt_audience:
        decode_kwargs["audience"] = jwt_audience

    try:
        payload = jwt.decode(
            token,
            public_key,
            **decode_kwargs,
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

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing sub (user identity) claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = payload.get("role") or "viewer"
    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unsupported role in token: {role}",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    In production: hash lookup (SHA-256) against configured keys.
    """
    from src.observability.audit_logger import audit_logger

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    env = os.environ.get("AEGIS_ENVIRONMENT", "production").lower()
    if env == "development" and api_key == "aegis-dev-key":
        return TenantContext(
            tenant_id="default-tenant",
            user_id="api-user",
            role="editor",
        )

    raw_keys = os.environ.get("AEGIS_API_KEYS")
    if not raw_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key authentication not configured",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    try:
        keys_map = json.loads(raw_keys)
    except json.JSONDecodeError as exc:
        audit_logger.log(
            action="auth.api_key_invalid_config",
            tenant_id="unknown",
            user_id="anonymous",
            status="FAILURE",
            detail={"error": "Malformed AEGIS_API_KEYS JSON"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key configuration",
            headers={"WWW-Authenticate": "ApiKey"},
        ) from exc

    if not isinstance(keys_map, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="AEGIS_API_KEYS configuration must be a JSON object",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    supplied_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    matched_meta = None
    for stored_hash, meta in keys_map.items():
        # Configuration keys must be lowercase 64-character hex strings (SHA-256 digests)
        if not isinstance(stored_hash, str) or not _SHA256_HEX.fullmatch(stored_hash):
            continue
        if not isinstance(meta, dict):
            continue
        if hmac.compare_digest(supplied_hash, stored_hash):
            matched_meta = meta
            break

    if not matched_meta:
        audit_logger.log(
            action="auth.api_key_unknown",
            tenant_id="unknown",
            user_id="anonymous",
            status="FAILURE",
            detail={"key_prefix": supplied_hash[:8]},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unrecognized API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    tenant_id = matched_meta.get("tenant_id")
    user_id = matched_meta.get("user_id", "api-user")
    role = matched_meta.get("role", "editor")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key configuration missing tenant_id metadata",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unsupported role in API key configuration: {role}",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    audit_logger.log(
        action="auth.api_key_success",
        tenant_id=str(tenant_id),
        user_id=str(user_id),
        status="SUCCESS",
        detail={"role": role, "key_prefix": supplied_hash[:8]},
    )

    return TenantContext(
        tenant_id=str(tenant_id),
        user_id=str(user_id),
        role=str(role),
    )


def require_role(*roles: str):
    """Role-based access control dependency factory."""
    async def check(tenant: TenantContext = Depends(get_current_tenant)):
        if tenant.role != "admin" and tenant.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{tenant.role}' not authorized. Required: {list(roles)}",
            )
        return tenant
    return check


async def get_current_tenant_ws(
    websocket: WebSocket,
    api_key: Optional[str] = None,
    token: Optional[str] = None,
) -> TenantContext:
    """Validate WebSocket connection credentials from query params or headers."""
    api_key = api_key or websocket.headers.get("X-API-Key")
    auth_header = websocket.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    if token:
        try:
            return _validate_jwt(token)
        except HTTPException:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise

    if api_key:
        try:
            return _validate_api_key(api_key)
        except HTTPException:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise

    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    raise HTTPException(status_code=401, detail="WebSocket authentication required")
