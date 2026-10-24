"""
src/core/authorization.py
=========================
FastAPI authorization dependencies and resource-level policy enforcement.
Enforces that authentication establishes the tenant context and authorization
verifies ownership without disclosing cross-tenant resource existence.
"""
from __future__ import annotations

from typing import Callable, Iterable, Optional

from fastapi import Depends, HTTPException, Request, status

from src.core.security_context import (
    LEGACY_ADMIN,
    ROLE_EDITOR,
    ROLE_PLATFORM_ADMIN,
    ROLE_TENANT_ADMIN,
    ROLE_VIEWER,
    TenantContext,
)


def require_tenant_context(request: Request) -> TenantContext:
    """
    FastAPI dependency ensuring an explicit, validated TenantContext exists.
    Fails closed with HTTP 401 if context is missing or unauthenticated.
    """
    context = getattr(request.state, "tenant_context", None)
    if not isinstance(context, TenantContext):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return context


def require_roles(*allowed_roles: str) -> Callable[[TenantContext], TenantContext]:
    """
    FastAPI dependency factory enforcing required role permissions.
    Fails closed with HTTP 403 if authenticated caller lacks required role.
    """
    def dependency(
        context: TenantContext = Depends(require_tenant_context),
    ) -> TenantContext:
        if not context.has_role(*allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of: {list(allowed_roles)}",
            )
        return context
    return dependency


def verify_resource_tenant(
    resource_tenant_id: Optional[str],
    context: TenantContext,
    resource_type: str = "document",
    allow_platform_admin: bool = False,
) -> None:
    """
    Verifies that the requested resource belongs to the caller's tenant.
    Never discloses resource existence across tenant boundaries: raises HTTP 404
    on mismatch rather than HTTP 403, preventing IDOR enumeration.
    """
    if not resource_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type.capitalize()} not found",
        )

    if str(resource_tenant_id) == str(context.tenant_id):
        return

    # Cross-tenant access is denied by default even for platform admin unless explicitly authorized
    if allow_platform_admin and ROLE_PLATFORM_ADMIN in context.roles:
        return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource_type.capitalize()} not found",
    )
