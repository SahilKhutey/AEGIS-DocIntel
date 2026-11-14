"""
src/repositories/evaluation/entitlement_repository.py
=====================================================
Repository for evaluation license assignments and administrative overrides.
Complies with PROT-04 WP-04.05 specification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.schemas.evaluation.entitlement_policy import (
    EvaluationEntitlementAssignment,
    EvaluationEntitlementOverride,
)


class EntitlementRepository:
    """Thread-safe storage for assignments and overrides with revision tracking."""

    def __init__(self) -> None:
        # license_id -> EvaluationEntitlementAssignment
        self._assignments: Dict[str, EvaluationEntitlementAssignment] = {}
        # license_id -> List[EvaluationEntitlementOverride]
        self._overrides: Dict[str, List[EvaluationEntitlementOverride]] = {}
        self._revision: int = 1

    @property
    def revision(self) -> int:
        return self._revision

    def assign_policy(
        self,
        *,
        license_id: str,
        evaluator_id: str,
        tenant_id: str,
        policy_key: str = "evaluation-basic",
        policy_version: str = "1.0",
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
    ) -> EvaluationEntitlementAssignment:
        assignment = EvaluationEntitlementAssignment(
            license_id=license_id,
            evaluator_id=evaluator_id,
            tenant_id=tenant_id,
            policy_key=policy_key,
            policy_version=policy_version,
            valid_from=valid_from or datetime.now(timezone.utc),
            valid_until=valid_until,
        )
        self._assignments[license_id] = assignment
        self._revision += 1
        return assignment

    def get_assignment(self, license_id: str) -> Optional[EvaluationEntitlementAssignment]:
        return self._assignments.get(license_id)

    def add_override(self, override: EvaluationEntitlementOverride) -> None:
        overrides = self._overrides.setdefault(override.license_id, [])
        # Remove any existing override for same feature
        self._overrides[override.license_id] = [
            o for o in overrides if o.feature_key != override.feature_key
        ]
        self._overrides[override.license_id].append(override)
        self._revision += 1

    def get_overrides(self, license_id: str) -> List[EvaluationEntitlementOverride]:
        return list(self._overrides.get(license_id, []))

    def clear_overrides(self, license_id: str) -> None:
        if license_id in self._overrides:
            del self._overrides[license_id]
            self._revision += 1

    def clear(self) -> None:
        self._assignments.clear()
        self._overrides.clear()
        self._revision += 1
