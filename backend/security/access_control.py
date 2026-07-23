"""
Access Control
===============

Role-Based Access Control (RBAC) + Attribute-Based (ABAC).

Mathematical Foundation:
    RBAC:
        P(user, resource, action) = user.role ⊆ action ⊆ resource.permissions

    ABAC:
        P(user, resource, action, context) = policy.evaluate(user, resource, action, context)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from .exceptions import AuthorizationError


def assign_shard_number_theoretic(
    key: str,
    primes: list[int] | None = None,
    thresholds: list[int] | None = None,
) -> int:
    '''
    Concept N2 — Number-Theoretic Consistent Hashing for Multi-Tenant Sharding:
    Routes key using machine distinct prime residues h % p_j < t_j with provable minimal redistribution bounds.
    '''
    p_list = primes or [997, 1009, 1013, 1019]
    t_list = thresholds or [500, 500, 500, 500]

    h = hash(key) & 0x7FFFFFFF
    for j in reversed(range(len(p_list))):
        if (h % p_list[j]) < t_list[j]:
            return j
    return 0


class Permission(Enum):
    """Standard permissions."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class Role:
    """A role with a set of permissions."""

    name: str
    permissions: Set[Permission] = field(default_factory=set)
    description: str = ""
    parent_roles: List[str] = field(default_factory=list)

    def has_permission(self, perm: Permission) -> bool:
        return perm in self.permissions


@dataclass
class Resource:
    """A protected resource."""

    resource_id: str
    resource_type: str
    owner_id: Optional[str] = None
    permissions: Set[Permission] = field(default_factory=set)
    attributes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Policy:
    """
    An access control policy.

    A predicate (user, resource, action, context) → bool.
    """

    name: str
    description: str
    predicate: Callable[[Dict[str, Any], Resource, Permission, Dict[str, Any]], bool]
    priority: int = 0
    enabled: bool = True


@dataclass
class AccessDecision:
    """Result of an access decision."""

    granted: bool
    user_id: str
    resource_id: str
    action: Permission
    reason: str
    matched_policy: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "granted": self.granted,
            "user_id": self.user_id,
            "resource_id": self.resource_id,
            "action": self.action.value,
            "reason": self.reason,
            "matched_policy": self.matched_policy,
            "timestamp": self.timestamp,
        }


class AccessController:
    """
    RBAC + ABAC access controller.

    Usage:
        controller = AccessController()
        controller.add_role(Role("admin", {Permission.READ, Permission.WRITE}))
        controller.assign_role_to_user("alice", "admin")
        decision = controller.check_access("alice", resource, Permission.WRITE)
    """

    def __init__(self) -> None:
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, Set[str]] = {}
        self.resources: Dict[str, Resource] = {}
        self.policies: List[Policy] = []
        self._audit_log: List[AccessDecision] = []

    def add_role(self, role: Role) -> None:
        self.roles[role.name] = role

    def remove_role(self, role_name: str) -> None:
        if role_name in self.roles:
            del self.roles[role_name]
        # remove from users
        for user_id in list(self.user_roles.keys()):
            self.user_roles[user_id].discard(role_name)

    def assign_role_to_user(self, user_id: str, role_name: str) -> None:
        if role_name not in self.roles:
            raise AuthorizationError(f"Role '{role_name}' not found")
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        self.user_roles[user_id].add(role_name)

    def revoke_role_from_user(self, user_id: str, role_name: str) -> None:
        if user_id in self.user_roles:
            self.user_roles[user_id].discard(role_name)

    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Aggregate permissions from all user roles (including parents)."""
        perms: Set[Permission] = set()
        role_names = self.user_roles.get(user_id, set()).copy()
        # process parent roles
        processed: Set[str] = set()
        while role_names:
            rname = role_names.pop()
            if rname in processed:
                continue
            processed.add(rname)
            role = self.roles.get(rname)
            if role is None:
                continue
            perms.update(role.permissions)
            role_names.update(role.parent_roles)
        return perms

    def register_resource(self, resource: Resource) -> None:
        self.resources[resource.resource_id] = resource

    def add_policy(self, policy: Policy) -> None:
        self.policies.append(policy)
        # sort by priority descending
        self.policies.sort(key=lambda p: p.priority, reverse=True)

    def check_access(
        self,
        user_id: str,
        resource: Resource,
        action: Permission,
        context: Optional[Dict[str, Any]] = None,
    ) -> AccessDecision:
        """Check if user can perform action on resource."""
        context = context or {}
        # 1. RBAC check
        user_perms = self.get_user_permissions(user_id)
        # 2. Resource owner always has access
        if resource.owner_id == user_id:
            decision = AccessDecision(
                granted=True,
                user_id=user_id,
                resource_id=resource.resource_id,
                action=action,
                reason="owner_access",
            )
            self._audit_log.append(decision)
            return decision
        # 3. ABAC policies
        for policy in self.policies:
            if not policy.enabled:
                continue
            user_attrs = context.get("user_attrs", {})
            try:
                if policy.predicate(user_attrs, resource, action, context):
                    decision = AccessDecision(
                        granted=True,
                        user_id=user_id,
                        resource_id=resource.resource_id,
                        action=action,
                        reason=f"policy:{policy.name}",
                        matched_policy=policy.name,
                    )
                    self._audit_log.append(decision)
                    return decision
            except Exception:
                continue
        # 4. RBAC + resource permissions
        if action in user_perms and action in resource.permissions:
            decision = AccessDecision(
                granted=True,
                user_id=user_id,
                resource_id=resource.resource_id,
                action=action,
                reason="rbac",
            )
            self._audit_log.append(decision)
            return decision
        # 5. Deny by default
        decision = AccessDecision(
            granted=False,
            user_id=user_id,
            resource_id=resource.resource_id,
            action=action,
            reason="no_matching_policy_or_role",
        )
        self._audit_log.append(decision)
        return decision

    def require_access(
        self,
        user_id: str,
        resource: Resource,
        action: Permission,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Raise if access is denied."""
        decision = self.check_access(user_id, resource, action, context)
        if not decision.granted:
            raise AuthorizationError(
                f"Access denied: user={user_id}, resource={resource.resource_id}, "
                f"action={action.value}, reason={decision.reason}"
            )

    def get_audit_log(
        self,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        granted_only: bool = False,
        denied_only: bool = False,
        limit: int = 100,
    ) -> List[AccessDecision]:
        """Query the audit log."""
        results = self._audit_log
        if user_id is not None:
            results = [d for d in results if d.user_id == user_id]
        if resource_id is not None:
            results = [d for d in results if d.resource_id == resource_id]
        if granted_only:
            results = [d for d in results if d.granted]
        if denied_only:
            results = [d for d in results if not d.granted]
        return results[-limit:]

    def create_default_roles(self) -> None:
        """Create a standard set of roles."""
        self.add_role(
            Role("admin", {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.EXECUTE, Permission.ADMIN}, description="Full access")
        )
        self.add_role(
            Role("editor", {Permission.READ, Permission.WRITE}, description="Read + write")
        )
        self.add_role(
            Role("viewer", {Permission.READ}, description="Read-only")
        )
        self.add_role(
            Role("service", {Permission.READ, Permission.EXECUTE}, description="Service account")
        )
