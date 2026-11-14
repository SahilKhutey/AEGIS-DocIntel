"""
src/services/evaluation/entitlement_resolver.py
===============================================
Core resolution engine mapping principal, policy, assignments, and overrides
into an effective entitlement set.
Complies with PROT-04 WP-04.05 specification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from src.repositories.evaluation.entitlement_policy_repository import (
    EntitlementPolicyRepository,
)
from src.repositories.evaluation.entitlement_repository import EntitlementRepository
from src.schemas.evaluation.authorization import AuditReasonCode
from src.schemas.evaluation.entitlement_catalogue import (
    FEATURE_REQUIRED_PERMISSIONS,
    is_known_feature,
    is_known_permission,
    normalize_feature,
    normalize_permission,
)
from src.schemas.evaluation.entitlement_policy import (
    EvaluationEntitlementAssignment,
    EvaluationEntitlementOverride,
    PolicyStatus,
)


class EntitlementResolver:
    """Evaluates effective features and action permissions for a license."""

    def __init__(
        self,
        policy_repo: EntitlementPolicyRepository,
        entitlement_repo: EntitlementRepository,
    ) -> None:
        self.policy_repo = policy_repo
        self.entitlement_repo = entitlement_repo

    def resolve_effective_entitlements(
        self,
        *,
        license_id: str,
        at_time: Optional[datetime] = None,
    ) -> Tuple[Dict[str, bool], Dict[str, Any], str]:
        """
        Returns (effective_features_map, limits_map, policy_version_key).
        Evaluates policy + assignment + active non-expired overrides.
        """
        now = at_time or datetime.now(timezone.utc)
        assignment = self.entitlement_repo.get_assignment(license_id)

        policy_key = assignment.policy_key if assignment else "evaluation-basic"
        policy_version = assignment.policy_version if assignment else "1.0"

        policy = self.policy_repo.get_policy(policy_key, policy_version)
        if not policy or policy.status != PolicyStatus.ACTIVE:
            # Policy missing or retired
            return ({}, {}, f"{policy_key}:{policy_version}")

        # Check assignment temporal validity (ENT-010, ENT-011)
        if assignment:
            if assignment.valid_from and now < assignment.valid_from:
                return ({}, {}, f"{policy_key}:{policy_version}")
            if assignment.valid_until and now >= assignment.valid_until:
                return ({}, {}, f"{policy_key}:{policy_version}")

        # Base features from policy document
        effective_features: Dict[str, bool] = dict(policy.policy_document.features)

        # Apply active overrides (ENT-013)
        overrides = self.entitlement_repo.get_overrides(license_id)
        for ov in overrides:
            if not ov.is_expired(now):
                norm_feat = normalize_feature(ov.feature_key)
                effective_features[norm_feat] = ov.override_enabled

        limits = policy.policy_document.limits.model_dump()
        return (effective_features, limits, f"{policy_key}:{policy_version}")

    def evaluate_permission(
        self,
        *,
        license_id: str,
        feature: str,
        permission: str,
        at_time: Optional[datetime] = None,
    ) -> Tuple[bool, str]:
        """
        Evaluates whether a specific feature and action permission are granted.
        Returns (allowed: bool, reason_code: str).
        """
        now = at_time or datetime.now(timezone.utc)

        # 1. Unknown feature guard (ENT-007)
        norm_feature = normalize_feature(feature)
        if not is_known_feature(norm_feature):
            return (False, AuditReasonCode.UNKNOWN_FEATURE.value)

        # 2. Unknown permission guard (ENT-008)
        norm_permission = normalize_permission(permission)
        if not is_known_permission(norm_permission):
            return (False, AuditReasonCode.UNKNOWN_PERMISSION.value)

        # 3. Check assignment and policy version validity (ENT-009)
        assignment = self.entitlement_repo.get_assignment(license_id)
        policy_key = assignment.policy_key if assignment else "evaluation-basic"
        policy_version = assignment.policy_version if assignment else "1.0"

        policy = self.policy_repo.get_policy(policy_key, policy_version)
        if not policy or policy.status != PolicyStatus.ACTIVE:
            return (False, AuditReasonCode.INVALID_POLICY_VERSION.value)

        # 4. Check temporal validity of assignment
        if assignment:
            if assignment.valid_from and now < assignment.valid_from:
                return (False, AuditReasonCode.ENTITLEMENT_FUTURE.value)
            if assignment.valid_until and now >= assignment.valid_until:
                return (False, AuditReasonCode.ENTITLEMENT_EXPIRED.value)

        # 5. Check override if present
        overrides = self.entitlement_repo.get_overrides(license_id)
        override_for_feat = next((o for o in overrides if normalize_feature(o.feature_key) == norm_feature), None)
        if override_for_feat:
            if override_for_feat.is_expired(now):
                # Expired override should not grant access if base policy is false
                pass
            else:
                if not override_for_feat.override_enabled:
                    return (False, AuditReasonCode.FEATURE_NOT_GRANTED.value)
                # If override granted the feature, ensure permission matches
                required_perms = FEATURE_REQUIRED_PERMISSIONS.get(norm_feature, set())
                if (
                    norm_permission not in required_perms
                    and norm_permission != norm_feature
                    and permission not in required_perms
                    and permission != norm_feature
                ):
                    return (False, AuditReasonCode.PERMISSION_DENIED.value)
                return (True, AuditReasonCode.ALLOWED.value)

        # 6. Evaluate base policy feature grant
        is_granted = policy.policy_document.features.get(norm_feature, False)
        if not is_granted:
            return (False, AuditReasonCode.FEATURE_NOT_GRANTED.value)

        # 7. Check permission requirement
        required_perms = FEATURE_REQUIRED_PERMISSIONS.get(norm_feature, set())
        if (
            norm_permission not in required_perms
            and norm_permission != norm_feature
            and permission not in required_perms
            and permission != norm_feature
        ):
            return (False, AuditReasonCode.PERMISSION_DENIED.value)

        return (True, AuditReasonCode.ALLOWED.value)
