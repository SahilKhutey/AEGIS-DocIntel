"""
src/repositories/evaluation/entitlement_policy_repository.py
============================================================
Repository for versioned evaluation entitlement policies.
Enforces immutability of activated policy versions.
Complies with PROT-04 WP-04.05 specification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from src.schemas.evaluation.entitlement_catalogue import (
    FEATURE_DASHBOARD_VIEW,
    FEATURE_DEVICE_MANAGE,
    FEATURE_DOCUMENT_COMPARE,
    FEATURE_DOCUMENT_EXPORT,
    FEATURE_DOCUMENT_PARSE,
    FEATURE_DOCUMENT_PREVIEW,
    FEATURE_DOCUMENT_QUERY,
    FEATURE_DOCUMENT_UPLOAD,
    FEATURE_LICENSE_VIEW,
    FEATURE_USAGE_VIEW,
    FEATURE_WORKSPACE_MANAGE,
)
from src.schemas.evaluation.entitlement_policy import (
    EvaluationEntitlementPolicy,
    EvaluationPolicyDocument,
    EvaluationPolicyLimits,
    PolicyStatus,
)


class PolicyImmutabilityError(Exception):
    """Raised when an attempt is made to mutate an active or retired policy version."""
    pass


class PolicyNotFoundError(Exception):
    """Raised when a policy key or version is not found."""
    pass


class EntitlementPolicyRepository:
    """Thread-safe, versioned repository for evaluation entitlement policies."""

    def __init__(self) -> None:
        # (policy_key, version) -> EvaluationEntitlementPolicy
        self._policies: Dict[Tuple[str, str], EvaluationEntitlementPolicy] = {}
        self._revision: int = 1
        self._init_default_policies()

    def _init_default_policies(self) -> None:
        """Initializes canonical evaluation-basic v1.0 and evaluation-pro v1.0 policies."""
        basic_doc = EvaluationPolicyDocument(
            policy_key="evaluation-basic",
            version="1.0",
            features={
                FEATURE_DASHBOARD_VIEW: True,
                FEATURE_DOCUMENT_UPLOAD: True,
                FEATURE_DOCUMENT_PREVIEW: True,
                FEATURE_DOCUMENT_PARSE: True,
                FEATURE_DOCUMENT_QUERY: True,
                FEATURE_DOCUMENT_COMPARE: False,  # Disabled in basic evaluation
                FEATURE_DOCUMENT_EXPORT: False,   # Disabled in basic evaluation
                FEATURE_WORKSPACE_MANAGE: True,
                FEATURE_USAGE_VIEW: True,
                FEATURE_LICENSE_VIEW: True,
                FEATURE_DEVICE_MANAGE: True,
            },
            limits=EvaluationPolicyLimits(
                documents_per_license=20,
                max_file_size_bytes=10_485_760,  # 10 MB
                storage_bytes=104_857_600,       # 100 MB
                queries_per_license=100,
                comparisons_per_license=0,
                concurrent_jobs=2,
            ),
        )
        basic_policy = EvaluationEntitlementPolicy(
            policy_key="evaluation-basic",
            version="1.0",
            status=PolicyStatus.ACTIVE,
            policy_document=basic_doc,
            activated_at=datetime.now(timezone.utc),
        )
        self._policies[("evaluation-basic", "1.0")] = basic_policy

        # Pro policy (used for commercial pilot trials)
        pro_doc = EvaluationPolicyDocument(
            policy_key="evaluation-pro",
            version="1.0",
            features={
                FEATURE_DASHBOARD_VIEW: True,
                FEATURE_DOCUMENT_UPLOAD: True,
                FEATURE_DOCUMENT_PREVIEW: True,
                FEATURE_DOCUMENT_PARSE: True,
                FEATURE_DOCUMENT_QUERY: True,
                FEATURE_DOCUMENT_COMPARE: True,
                FEATURE_DOCUMENT_EXPORT: True,
                FEATURE_WORKSPACE_MANAGE: True,
                FEATURE_USAGE_VIEW: True,
                FEATURE_LICENSE_VIEW: True,
                FEATURE_DEVICE_MANAGE: True,
            },
            limits=EvaluationPolicyLimits(
                documents_per_license=50,
                max_file_size_bytes=26_214_400,  # 25 MB
                storage_bytes=524_288_000,       # 500 MB
                queries_per_license=500,
                comparisons_per_license=50,
                concurrent_jobs=5,
            ),
        )
        pro_policy = EvaluationEntitlementPolicy(
            policy_key="evaluation-pro",
            version="1.0",
            status=PolicyStatus.ACTIVE,
            policy_document=pro_doc,
            activated_at=datetime.now(timezone.utc),
        )
        self._policies[("evaluation-pro", "1.0")] = pro_policy

    @property
    def revision(self) -> int:
        return self._revision

    def get_policy(self, policy_key: str, version: str) -> Optional[EvaluationEntitlementPolicy]:
        return self._policies.get((policy_key, version))

    def save_policy(self, policy: EvaluationEntitlementPolicy) -> None:
        key = (policy.policy_key, policy.version)
        existing = self._policies.get(key)
        if existing and existing.status in (PolicyStatus.ACTIVE, PolicyStatus.RETIRED):
            raise PolicyImmutabilityError(
                f"Policy version {policy.policy_key} v{policy.version} is {existing.status.value} and immutable"
            )
        self._policies[key] = policy
        self._revision += 1

    def activate_policy(self, policy_key: str, version: str) -> EvaluationEntitlementPolicy:
        key = (policy_key, version)
        policy = self._policies.get(key)
        if not policy:
            raise PolicyNotFoundError(f"Policy {policy_key} v{version} not found")
        if policy.status == PolicyStatus.RETIRED:
            raise PolicyImmutabilityError(f"Cannot reactivate retired policy {policy_key} v{version}")
        
        updated = EvaluationEntitlementPolicy(
            id=policy.id,
            policy_key=policy.policy_key,
            version=policy.version,
            status=PolicyStatus.ACTIVE,
            policy_document=policy.policy_document,
            created_at=policy.created_at,
            activated_at=datetime.now(timezone.utc),
        )
        self._policies[key] = updated
        self._revision += 1
        return updated

    def retire_policy(self, policy_key: str, version: str) -> EvaluationEntitlementPolicy:
        key = (policy_key, version)
        policy = self._policies.get(key)
        if not policy:
            raise PolicyNotFoundError(f"Policy {policy_key} v{version} not found")
        
        updated = EvaluationEntitlementPolicy(
            id=policy.id,
            policy_key=policy.policy_key,
            version=policy.version,
            status=PolicyStatus.RETIRED,
            policy_document=policy.policy_document,
            created_at=policy.created_at,
            activated_at=policy.activated_at,
            retired_at=datetime.now(timezone.utc),
        )
        self._policies[key] = updated
        self._revision += 1
        return updated

    def list_policies(self) -> List[EvaluationEntitlementPolicy]:
        return list(self._policies.values())

    def clear(self) -> None:
        self._policies.clear()
        self._init_default_policies()
        self._revision += 1
