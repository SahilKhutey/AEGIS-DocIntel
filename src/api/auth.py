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

from fastapi import Depends, HTTPException, Request, Security, status, WebSocket
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from src.core.security_context import (
    TenantContext,
    ROLE_VIEWER,
    ROLE_EDITOR,
    ROLE_TENANT_ADMIN,
    ROLE_PLATFORM_ADMIN,
    LEGACY_ADMIN,
    STANDARD_ROLES,
)

BEARER = HTTPBearer(auto_error=False)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

ALLOWED_ROLES: frozenset[str] = STANDARD_ROLES
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


async def get_current_tenant(
    request: Request = None,
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(BEARER),
    api_key: Optional[str] = Security(API_KEY_HEADER),
) -> TenantContext:
    """
    Validate JWT or API key and return TenantContext.
    In production: validate JWT (RS256) or look up API key hash from configuration/store.
    """
    if request is not None:
        cached = getattr(request.state, "tenant_context", None)
        if isinstance(cached, TenantContext):
            return cached

    context: TenantContext
    if bearer and bearer.credentials:
        context = _validate_jwt(bearer.credentials)
    elif api_key:
        context = _validate_api_key(api_key)
    else:
        env = os.environ.get("AEGIS_ENVIRONMENT", "production").lower()
        demo_mode = os.environ.get("AEGIS_DEMO_MODE", "false").lower() in ("true", "1", "yes")
        allow_anon = os.environ.get("AEGIS_DEMO_ALLOW_ANONYMOUS", "false").lower() in ("true", "1", "yes")
        if (demo_mode or env == "demo") and allow_anon:
            context = TenantContext(
                tenant_id="demo-tenant",
                principal_id="demo-anonymous-visitor",
                roles=frozenset({"viewer", "editor"}),
                authentication_method="demo_anonymous",
                monthly_token_limit=50_000,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication. Provide Bearer token or X-API-Key header.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    if request is not None:
        request.state.tenant_context = context
    return context


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
    demo_mode = os.environ.get("AEGIS_DEMO_MODE", "false").lower() in ("true", "1", "yes")

    if (demo_mode or env == "demo") and (
        token == os.environ.get("AEGIS_DEMO_TOKEN", "aegis-demo-token-sandbox")
        or token == "demo-token"
        or token.startswith("demo-")
    ):
        audit_logger.log(
            action="auth.demo_jwt_success",
            tenant_id="demo-tenant",
            user_id="demo-visitor",
            status="SUCCESS",
            detail={"role": "editor"},
        )
        return TenantContext(
            tenant_id="demo-tenant",
            principal_id="demo-visitor",
            roles=frozenset({"viewer", "editor"}),
            authentication_method="demo_bearer",
            monthly_token_limit=50_000,
        )

    if env == "development" and token.startswith("dev-"):
        tenant_id = token[4:] or "default-tenant"
        return TenantContext(
            tenant_id=tenant_id,
            principal_id="dev-user",
            roles=frozenset({"admin", "tenant_admin", "editor", "reviewer", "review_admin"}),
            authentication_method="dev_token",
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

    is_strict = (
        os.environ.get("AEGIS_EVALUATION_MODE", "").lower() in ("true", "1", "yes") or
        os.environ.get("AEGIS_STRICT_JWT_VALIDATION", "").lower() in ("true", "1", "yes")
    )
    if is_strict:
        if not jwt_issuer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Evaluation production requires AEGIS_JWT_ISSUER",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not jwt_audience:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Evaluation production requires AEGIS_JWT_AUDIENCE",
                headers={"WWW-Authenticate": "Bearer"},
            )

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
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    raw_tid = payload.get("tenant_id")
    raw_tid_alt = payload.get("tid")
    if raw_tid and raw_tid_alt and str(raw_tid) != str(raw_tid_alt):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Conflicting tenant_id and tid claims in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tenant_id = raw_tid or raw_tid_alt
    if not tenant_id or not isinstance(tenant_id, str) or not str(tenant_id).strip() or len(str(tenant_id)) > 256:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing tenant_id claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id or not isinstance(user_id, str) or not str(user_id).strip() or len(str(user_id)) > 256:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing sub (user identity) claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = payload.get("role") or "viewer"
    if not isinstance(role, str) or role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unsupported role in token: {role}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    roles = frozenset({"admin", "tenant_admin"}) if role == "admin" else frozenset({role})
    if "roles" in payload and payload["roles"] is not None:
        raw_roles = payload["roles"]
        if not isinstance(raw_roles, (list, set, tuple)) or not raw_roles:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid roles claim format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not all(isinstance(r, str) and r in ALLOWED_ROLES for r in raw_roles):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unsupported role in roles array",
                headers={"WWW-Authenticate": "Bearer"},
            )
        parsed_roles = set(raw_roles)
        if role == "admin":
            parsed_roles.add("tenant_admin")
        if role not in parsed_roles:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Primary role '{role}' contradicts roles array",
                headers={"WWW-Authenticate": "Bearer"},
            )
        roles = frozenset(parsed_roles)

    audit_logger.log(
        action="auth.jwt_success",
        tenant_id=str(tenant_id),
        user_id=str(user_id),
        status="SUCCESS",
        detail={"role": role},
    )

    return TenantContext(
        tenant_id=str(tenant_id),
        principal_id=str(user_id),
        roles=roles,
        authentication_method="bearer",
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
    demo_mode = os.environ.get("AEGIS_DEMO_MODE", "false").lower() in ("true", "1", "yes")

    if (demo_mode or env == "demo") and (
        api_key == os.environ.get("AEGIS_DEMO_API_KEY", "aegis-demo-public-key")
        or api_key == "demo-key"
    ):
        audit_logger.log(
            action="auth.demo_api_key_success",
            tenant_id="demo-tenant",
            user_id="demo-visitor",
            status="SUCCESS",
            detail={"role": "editor"},
        )
        return TenantContext(
            tenant_id="demo-tenant",
            principal_id="demo-visitor",
            roles=frozenset({"viewer", "editor"}),
            authentication_method="demo_key",
            monthly_token_limit=50_000,
        )

    if env == "development" and api_key == "aegis-dev-key":
        return TenantContext(
            tenant_id="default-tenant",
            principal_id="api-user",
            roles=frozenset({"editor"}),
            authentication_method="dev_key",
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

    roles = frozenset({"admin", "tenant_admin"}) if role == "admin" else frozenset({role})
    if "roles" in matched_meta and isinstance(matched_meta["roles"], (list, set, tuple)):
        roles = frozenset(matched_meta["roles"])

    return TenantContext(
        tenant_id=str(tenant_id),
        principal_id=str(user_id),
        roles=roles,
        authentication_method="api_key",
    )


def require_role(*roles: str):
    """Role-based access control dependency factory."""
    async def check(tenant: TenantContext = Depends(get_current_tenant)):
        if not tenant.has_role(*roles):
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
    headers = getattr(websocket, "headers", {})
    if isinstance(headers, dict):
        lower_headers = {str(k).lower(): v for k, v in headers.items()}
        api_key = api_key or lower_headers.get("x-api-key")
        auth_header = lower_headers.get("authorization", "")
    elif hasattr(headers, "get"):
        api_key = api_key or headers.get("X-API-Key") or headers.get("x-api-key")
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
    else:
        auth_header = ""

    if auth_header.startswith("Bearer ") or auth_header.startswith("bearer "):
        token = auth_header[7:]

    async def _safe_close():
        if hasattr(websocket, "close"):
            try:
                import inspect
                close_res = websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                if inspect.isawaitable(close_res):
                    await close_res
            except Exception:
                pass

    if token:
        try:
            return _validate_jwt(token)
        except HTTPException:
            await _safe_close()
            raise

    if api_key:
        try:
            return _validate_api_key(api_key)
        except HTTPException:
            await _safe_close()
            raise

    await _safe_close()
    raise HTTPException(status_code=401, detail="WebSocket authentication required")


def validate_production_auth_config(strict_evaluation: bool = False) -> None:
    """
    Validates that production authentication configuration is complete and fail-closed.
    Raises RuntimeError at application startup if mandatory security parameters are missing.
    """
    env = os.environ.get("AEGIS_ENVIRONMENT", "production").lower()
    if env not in ("production", "prod", "evaluation"):
        return

    public_key = os.environ.get("AEGIS_JWT_PUBLIC_KEY")
    key_path = os.environ.get("AEGIS_JWT_PUBLIC_KEY_PATH")
    if not public_key and (not key_path or not os.path.isfile(key_path)):
        raise RuntimeError("Production auth misconfiguration: AEGIS_JWT_PUBLIC_KEY or AEGIS_JWT_PUBLIC_KEY_PATH is required.")

    is_strict = (
        strict_evaluation
        or os.environ.get("AEGIS_EVALUATION_MODE", "").lower() in ("true", "1", "yes")
        or os.environ.get("AEGIS_STRICT_JWT_VALIDATION", "").lower() in ("true", "1", "yes")
    )
    if is_strict:
        if not os.environ.get("AEGIS_JWT_ISSUER"):
            raise RuntimeError("Production auth misconfiguration: AEGIS_JWT_ISSUER is required in evaluation production.")
        if not os.environ.get("AEGIS_JWT_AUDIENCE"):
            raise RuntimeError("Production auth misconfiguration: AEGIS_JWT_AUDIENCE is required in evaluation production.")

