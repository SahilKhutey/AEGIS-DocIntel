"""
src/schemas/evaluation/authorization.py
=======================================
Authorization Decision, Principal Context, and Safe Client Response Schemas.
Enforces non-negotiable anti-escalation and structured allow/deny decisions.
Complies with PROT-04 WP-04.05 specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set

from pydantic import BaseModel, Field, model_validator


class AuditReasonCode(str, Enum):
    ALLOWED = "ALLOWED"
    FEATURE_NOT_GRANTED = "FEATURE_NOT_GRANTED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    LICENSE_EXPIRED = "LICENSE_EXPIRED"
    LICENSE_SUSPENDED = "LICENSE_SUSPENDED"
    LICENSE_REVOKED = "LICENSE_REVOKED"
    DEVICE_INACTIVE = "DEVICE_INACTIVE"
    UNKNOWN_FEATURE = "UNKNOWN_FEATURE"
    UNKNOWN_PERMISSION = "UNKNOWN_PERMISSION"
    INVALID_POLICY_VERSION = "INVALID_POLICY_VERSION"
    ENTITLEMENT_EXPIRED = "ENTITLEMENT_EXPIRED"
    ENTITLEMENT_FUTURE = "ENTITLEMENT_FUTURE"
    OVERRIDE_EXPIRED = "OVERRIDE_EXPIRED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CROSS_TENANT_ACCESS_DENIED = "CROSS_TENANT_ACCESS_DENIED"
    ADMIN_ROLE_PROHIBITED = "ADMIN_ROLE_PROHIBITED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


@dataclass(frozen=True)
class AuthorizationDecision:
    """Immutable result of an entitlement and authorization check."""
    allowed: bool
    reason_code: str
    feature: str
    permission: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# Canonical evaluation roles
ROLE_EVALUATION_USER = "evaluation_user"
ROLE_EVALUATION_REVIEWER = "evaluation_reviewer"
ROLE_VIEWER = "viewer"
ROLE_OPERATOR = "operator"
ROLE_ADMIN = "admin"
ROLE_PLATFORM_ADMIN = "platform_admin"
ROLE_TENANT_ADMIN = "tenant_admin"

DISALLOWED_EVALUATION_ROLES: FrozenSet[str] = frozenset({
    ROLE_ADMIN,
    ROLE_PLATFORM_ADMIN,
    ROLE_TENANT_ADMIN,
})


class PrincipalContext(BaseModel):
    """
    Authenticated security principal.
    Evaluator sessions cannot contain administrator roles.
    """
    evaluator_id: str
    tenant_id: str
    roles: FrozenSet[str] = Field(default_factory=lambda: frozenset({ROLE_EVALUATION_USER}))
    license_id: Optional[str] = None
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    workspace_id: Optional[str] = None
    is_evaluator: bool = True

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_evaluator_roles(self) -> PrincipalContext:
        if not self.roles:
            raise ValueError("At least one role is required")
        # Anti-escalation check (RBAC-002, RBAC-003)
        if self.is_evaluator:
            illegal_roles = set(self.roles).intersection(DISALLOWED_EVALUATION_ROLES)
            if illegal_roles:
                raise ValueError(
                    f"Evaluator principal cannot be assigned administrative roles: {illegal_roles}"
                )
        return self

    @property
    def primary_role(self) -> str:
        if ROLE_EVALUATION_USER in self.roles:
            return ROLE_EVALUATION_USER
        if ROLE_EVALUATION_REVIEWER in self.roles:
            return ROLE_EVALUATION_REVIEWER
        for r in self.roles:
            return r
        return ROLE_VIEWER


class SafePrincipalSummary(BaseModel):
    id: str
    role: str


class SafeLicenseSummary(BaseModel):
    status: str
    policy_version: str


class SafeEntitlementResponse(BaseModel):
    """
    Safe entitlement summary returned to evaluator client frontend.
    Never exposes internal policy definitions, private-engine endpoints, or secrets.
    """
    principal: SafePrincipalSummary
    license: SafeLicenseSummary
    entitlements: Dict[str, bool]
    limits: Dict[str, Any]
    version: int = 1
