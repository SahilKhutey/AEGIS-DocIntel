"""Bearer-JWT middleware for FastAPI."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from amdi.observability.metrics import JOBS_FAILED_TOTAL
from amdi.security.auth import (
    AuthError,
    JWTVerifier,
    Principal,
    VerificationFailure,
)
from amdi.security.rbac import Permission, authorize

_bearer = HTTPBearer(auto_error=False)
_verifier = JWTVerifier()


async def current_principal(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Principal:
    """Resolve the principal from a Bearer token."""
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=401,
            detail={"code": AuthError.MISSING.value, "detail": "missing bearer"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = _verifier.verify(creds.credentials)
    if isinstance(result, VerificationFailure):
        raise HTTPException(
            status_code=401,
            detail=result.as_dict(),
            headers={"WWW-Authenticate": "Bearer"},
        )
    request.state.principal = result
    return result


async def require_jwt(principal: Principal = Depends(current_principal)) -> None:
    """Sentinel that merely enforces auth without using the principal body."""
    return None


def require_permission(permission: Permission):
    """Build a FastAPI dependency enforcing RBAC."""
    async def _dep(p: Principal = Depends(current_principal)) -> Principal:
        if not authorize(p, permission):
            JOBS_FAILED_TOTAL.labels(reason="forbidden").inc()
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden",
                        "permission": permission.value,
                        "roles": list(p.roles)},
            )
        return p
    return _dep


__all__ = [
    "current_principal",
    "require_jwt",
    "require_permission",
]
