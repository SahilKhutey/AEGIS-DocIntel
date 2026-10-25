"""
src/core/security_context.py
============================
Enterprise Security & Tenant Context Model for AEGIS-DocIntel:
1. Typed, immutable TenantContext derived from verified authentication.
2. Explicit multi-tenant principal identity and role memberships.
3. Fail-closed validation enforcing non-empty tenant, principal, and roles.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Set, FrozenSet, Iterable


# Canonical enterprise roles
ROLE_VIEWER = "viewer"
ROLE_EDITOR = "editor"
ROLE_TENANT_ADMIN = "tenant_admin"
ROLE_PLATFORM_ADMIN = "platform_admin"
LEGACY_ADMIN = "admin"

STANDARD_ROLES: frozenset[str] = frozenset({
    ROLE_VIEWER,
    ROLE_EDITOR,
    ROLE_TENANT_ADMIN,
    ROLE_PLATFORM_ADMIN,
    LEGACY_ADMIN,
})


@dataclass(frozen=True, init=False)
class TenantContext:
    """
    Immutable security context representing the authenticated caller.
    Never infer this context from user-controlled document IDs or client headers.
    """
    tenant_id: str
    principal_id: str
    roles: frozenset[str]
    authentication_method: str
    monthly_token_limit: int

    def __init__(
        self,
        tenant_id: str,
        principal_id: Optional[str] = None,
        roles: Optional[frozenset[str] | Set[str] | Iterable[str]] = None,
        authentication_method: str = "bearer",
        monthly_token_limit: int = 10_000_000,
        *,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
    ) -> None:
        p_id = principal_id or user_id or ""
        if not roles:
            if role:
                r_set = frozenset({"admin", "tenant_admin"}) if role == "admin" else frozenset({role})
            else:
                r_set = frozenset()
        else:
            r_set = frozenset(roles)

        object.__setattr__(self, "tenant_id", tenant_id or "")
        object.__setattr__(self, "principal_id", p_id)
        object.__setattr__(self, "roles", r_set)
        object.__setattr__(self, "authentication_method", authentication_method)
        object.__setattr__(self, "monthly_token_limit", monthly_token_limit)

        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.principal_id or not self.principal_id.strip():
            raise ValueError("principal_id is required")
        if not self.roles:
            raise ValueError("At least one role is required")

    @property
    def user_id(self) -> str:
        """Backward-compatible alias for existing service calls."""
        return self.principal_id

    @property
    def role(self) -> str:
        """Backward-compatible primary role string."""
        for r in (ROLE_PLATFORM_ADMIN, LEGACY_ADMIN, ROLE_TENANT_ADMIN, ROLE_EDITOR, ROLE_VIEWER):
            if r in self.roles:
                return r
        return next(iter(self.roles))

    def has_role(self, *allowed_roles: str) -> bool:
        """Check if caller holds any of the specified roles."""
        target_roles = set(allowed_roles)
        if "admin" in target_roles:
            target_roles.add(ROLE_TENANT_ADMIN)
        if ROLE_TENANT_ADMIN in target_roles:
            target_roles.add(LEGACY_ADMIN)
        return bool(self.roles.intersection(target_roles))

    def can_read_document(self) -> bool:
        """Viewers, Editors, and Admins can read authorized tenant documents."""
        return bool(self.roles.intersection({ROLE_VIEWER, ROLE_EDITOR, ROLE_TENANT_ADMIN, LEGACY_ADMIN, ROLE_PLATFORM_ADMIN}))

    def can_write_document(self) -> bool:
        """Editors and Admins can upload, modify, or process tenant documents."""
        return bool(self.roles.intersection({ROLE_EDITOR, ROLE_TENANT_ADMIN, LEGACY_ADMIN}))

    def can_delete_document(self) -> bool:
        """Only Tenant Admins can delete tenant documents by default."""
        return bool(self.roles.intersection({ROLE_TENANT_ADMIN, LEGACY_ADMIN}))

    def can_manage_members(self) -> bool:
        """Tenant Admins can manage members of their organization."""
        return bool(self.roles.intersection({ROLE_TENANT_ADMIN, LEGACY_ADMIN, ROLE_PLATFORM_ADMIN}))

    def can_manage_platform(self) -> bool:
        """Platform Admins have global maintenance capabilities."""
        return ROLE_PLATFORM_ADMIN in self.roles
