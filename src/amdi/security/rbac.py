"""Role-Based Access Control."""

from __future__ import annotations

from enum import Enum
from typing import Iterable, Mapping

from amdi.security.auth import Principal


class Permission(str, Enum):
    DOC_UPLOAD    = "doc:upload"
    DOC_READ      = "doc:read"
    DOC_DELETE    = "doc:delete"

    QUERY_RUN     = "query:run"
    QUERY_STREAM  = "query:stream"

    EXPORT_BUILD  = "export:build"

    ADMIN_USERS   = "admin:users"
    ADMIN_AUDIT   = "admin:audit"


ROLE_PERMISSIONS: Mapping[str, frozenset[Permission]] = {
    "reader":  frozenset({Permission.DOC_READ, Permission.QUERY_RUN}),
    "author":  frozenset({
        Permission.DOC_READ, Permission.DOC_UPLOAD, Permission.DOC_DELETE,
        Permission.QUERY_RUN, Permission.QUERY_STREAM, Permission.EXPORT_BUILD,
    }),
    "admin":   frozenset(set(Permission)),
    "service": frozenset({
        Permission.DOC_UPLOAD, Permission.DOC_READ,
        Permission.QUERY_RUN, Permission.QUERY_STREAM,
        Permission.EXPORT_BUILD,
        Permission.ADMIN_AUDIT,
    }),
}


def permissions_for(roles: Iterable[str]) -> frozenset[Permission]:
    out: set[Permission] = set()
    for r in roles:
        out |= ROLE_PERMISSIONS.get(r, frozenset())
    return frozenset(out)


def authorize(
    principal: Principal,
    action: Permission,
    *,
    resource: str | None = None,
) -> bool:
    return action in permissions_for(principal.roles)


__all__ = ["Permission", "ROLE_PERMISSIONS", "authorize", "permissions_for"]
