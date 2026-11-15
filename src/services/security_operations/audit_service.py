"""
AEGIS-DocIntel Audit Service (PROT-04 WP-04.08)
Provides operational interface for querying and retrieving audit telemetry.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from src.repositories.security_operations.audit_repository import AuditRepository, audit_repository


class AuditService:
    def __init__(self, audit_repo: Optional[AuditRepository] = None):
        self._audit_repo = audit_repo or audit_repository

    def get_audit_trail(self, caller_role: str = "security_operator") -> List[Dict[str, Any]]:
        """Restricts audit trail retrieval based on caller authorization role."""
        if caller_role in ("evaluator", "unauthenticated"):
            raise PermissionError("Evaluator accounts are not permitted to inspect raw audit trail records.")
        return self._audit_repo.get_chain()

    def export_evidence(self) -> Dict[str, Any]:
        return self._audit_repo.export_audit_log()


audit_service = AuditService()
