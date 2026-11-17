"""
AEGIS-DocIntel Usage Aggregation Service (PROT-04 WP-04.06)
Aggregates operational counter and ledger data into evaluator-scoped usage summaries.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional
from src.repositories.evaluation.quota_counter_repository import (
    QuotaCounterRepository,
    default_quota_counter_repository,
)
from src.schemas.evaluation.usage_summary import (
    EvaluationUsageSummary,
    QuotaDimensionUsage,
)
from src.services.evaluation.quota_policy_service import (
    QuotaPolicyService,
    default_quota_policy_service,
)


class UsageAggregationService:
    def __init__(
        self,
        policy_service: Optional[QuotaPolicyService] = None,
        counter_repo: Optional[QuotaCounterRepository] = None,
    ):
        self.policy_service = policy_service or default_quota_policy_service
        self.counter_repo = counter_repo or default_quota_counter_repository

    def get_evaluator_usage_summary(
        self,
        license_id: str,
        evaluator_id: str,
        tenant_id: str,
        policy_key: str = "evaluation-basic",
    ) -> EvaluationUsageSummary:
        """
        Compiles authoritative usage summary across all policy dimensions for evaluator view.
        """
        policy = self.policy_service.get_effective_policy(policy_key)
        counters = self.counter_repo.list_counters(license_id)
        counters_by_key = {c.quota_key: c for c in counters}

        now_iso = datetime.now(timezone.utc).isoformat()
        usage_map: Dict[str, QuotaDimensionUsage] = {}

        for q_key, q_def in policy.quotas.items():
            counter = counters_by_key.get(q_key)
            if counter:
                used = counter.consumed
                reserved = counter.reserved
                limit = counter.limit_value
            else:
                used = 0
                reserved = 0
                limit = q_def.limit

            remaining = max(0, limit - used - reserved)
            usage_map[q_key] = QuotaDimensionUsage(
                used=used,
                reserved=reserved,
                limit=limit,
                remaining=remaining,
                unit=q_def.unit.value,
                period=q_def.period.value,
            )

        return EvaluationUsageSummary(
            license_id=license_id,
            tenant_id=tenant_id,
            policy_key=policy.policy_key,
            policy_version=policy.version,
            usage=usage_map,
            generated_at=now_iso,
        )


default_usage_aggregation_service = UsageAggregationService()
