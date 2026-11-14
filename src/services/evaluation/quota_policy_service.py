"""
AEGIS-DocIntel Quota Policy Service (PROT-04 WP-04.06)
Resolves, validates, and manages quota policies for evaluation tiers.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from src.repositories.evaluation.quota_policy_repository import (
    QuotaPolicyRepository,
    default_quota_policy_repository,
)
from src.schemas.evaluation.quota import EvaluationQuotaPolicy, QuotaDefinition, QuotaDimension


class QuotaPolicyService:
    def __init__(self, policy_repo: Optional[QuotaPolicyRepository] = None):
        self.policy_repo = policy_repo or default_quota_policy_repository

    def get_effective_policy(self, policy_key: str = "evaluation-basic", version: Optional[str] = None) -> EvaluationQuotaPolicy:
        policy = self.policy_repo.get_policy(policy_key, version)
        if not policy:
            # Fall back to evaluation-basic if requested policy not found
            policy = self.policy_repo.get_policy("evaluation-basic")
        if not policy or policy.status != "ACTIVE":
            raise ValueError(f"No active quota policy found for key '{policy_key}'")
        return policy

    def get_quota_definition(
        self,
        policy_key: str,
        dimension: QuotaDimension | str,
        version: Optional[str] = None,
    ) -> Optional[QuotaDefinition]:
        policy = self.get_effective_policy(policy_key, version)
        dim_key = dimension.value if isinstance(dimension, QuotaDimension) else dimension
        return policy.quotas.get(dim_key)

    def list_policies(self) -> List[EvaluationQuotaPolicy]:
        return self.policy_repo.list_policies()

    def create_policy(self, policy: EvaluationQuotaPolicy) -> EvaluationQuotaPolicy:
        return self.policy_repo.create_policy(policy)

    def activate_policy(self, policy_key: str, version: str) -> EvaluationQuotaPolicy:
        return self.policy_repo.activate_version(policy_key, version)

    def retire_policy(self, policy_key: str, version: str) -> EvaluationQuotaPolicy:
        return self.policy_repo.retire_version(policy_key, version)


default_quota_policy_service = QuotaPolicyService()
