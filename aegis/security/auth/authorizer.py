"""
aegis.security.auth.authorizer
==============================
Central Authorization & Access Control Engine:
- Role-based access control (RBAC) based on canonical permission matrix.
- Anti-privilege escalation (payload role tampering rejection).
- Resource ownership and tenant scope enforcement.
- Fail-closed access denial by default.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class Authorizer:
    """Evaluates operations against canonical roles and resource tenant scope."""

    def __init__(self, matrix_path: Optional[Path | str] = None) -> None:
        self.permission_matrix: Dict[str, Dict[str, str]] = {}
        if matrix_path is None:
            matrix_path = Path("artifacts/security/reports/ROLE_PERMISSION_MATRIX.csv")
        self._load_matrix(Path(matrix_path))

    def _load_matrix(self, path: Path) -> None:
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                op = row.get("operation")
                if op:
                    self.permission_matrix[op] = {k: v.upper() for k, v in row.items() if k != "operation"}

    def is_operation_permitted(self, operation: str, roles: Set[str]) -> bool:
        if not roles:
            roles = {"anonymous"}

        op_rules = self.permission_matrix.get(operation)
        if not op_rules:
            # Deny by default if operation is unmapped
            return False

        for role in roles:
            decision = op_rules.get(role, "DENY")
            if decision == "ALLOW":
                return True

        return False

    def authorize(
        self,
        principal_id: str,
        principal_tenant_id: str,
        principal_roles: Set[str],
        operation: str,
        resource_id: Optional[str] = None,
        resource_tenant_id: Optional[str] = None,
        resource_owner_id: Optional[str] = None,
        client_payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, int, str]:
        """
        Authorizes request. Returns (is_authorized, status_code, reason).
        Status code: 200 (OK), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found / Anti-IDOR).
        """
        # 1. Privilege Escalation Defense: Inspect payload for illegal role tampering
        if client_payload:
            for k in ("role", "roles", "is_admin", "permissions"):
                if k in client_payload:
                    val = client_payload[k]
                    # Client payload attempts to declare elevated roles
                    if any(r in str(val).lower() for r in ("admin", "tenant_admin", "platform_admin", "root")):
                        if not any(r in principal_roles for r in ("admin", "tenant_admin", "platform_admin")):
                            return False, 403, "Privilege escalation attempt detected in request payload"

        # 2. Check operation-level RBAC
        if not self.is_operation_permitted(operation, principal_roles):
            return False, 403, f"Operation '{operation}' not permitted for assigned roles {list(principal_roles)}"

        # 3. Check Resource Ownership & Tenant Scoping (Anti-IDOR)
        if resource_id is not None and resource_tenant_id is not None:
            if str(resource_tenant_id) != str(principal_tenant_id):
                # Anti-IDOR: Return 404 rather than 403 to prevent resource enumeration
                return False, 404, "Resource not found"

            # Check individual resource ownership if operation is owner-scoped
            if resource_owner_id is not None and "view_own" in operation:
                if str(resource_owner_id) != str(principal_id) and not any(
                    r in principal_roles for r in ("tenant_admin", "admin")
                ):
                    return False, 403, "Access to other user's resource denied"

        return True, 200, "Authorized"
