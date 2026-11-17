"""
AEGIS-DocIntel Quota Policy Repository (PROT-04 WP-04.06)
Manages versioned, immutable evaluation quota policy documents.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
from src.schemas.evaluation.quota import (
    EvaluationQuotaPolicy,
    get_default_evaluation_basic_quota_policy,
    get_default_evaluation_pro_quota_policy,
)


class QuotaPolicyRepository:
    def __init__(self):
        self._policies: Dict[str, Dict[str, EvaluationQuotaPolicy]] = {}
        self._lock = threading.Lock()
        self._seed_defaults()

    def _seed_defaults(self):
        basic = get_default_evaluation_basic_quota_policy()
        pro = get_default_evaluation_pro_quota_policy()
        self._policies[basic.policy_key] = {basic.version: basic}
        self._policies[pro.policy_key] = {pro.version: pro}

    def get_policy(self, policy_key: str, version: Optional[str] = None) -> Optional[EvaluationQuotaPolicy]:
        with self._lock:
            versions = self._policies.get(policy_key)
            if not versions:
                return None
            if version:
                return versions.get(version)
            # Find latest ACTIVE version
            active = [p for p in versions.values() if p.status == "ACTIVE"]
            if active:
                return sorted(active, key=lambda p: p.version, reverse=True)[0]
            return sorted(versions.values(), key=lambda p: p.version, reverse=True)[0]

    def create_policy(self, policy: EvaluationQuotaPolicy) -> EvaluationQuotaPolicy:
        with self._lock:
            versions = self._policies.setdefault(policy.policy_key, {})
            if policy.version in versions:
                existing = versions[policy.version]
                if existing.status in ("ACTIVE", "RETIRED"):
                    raise ValueError(
                        f"Policy '{policy.policy_key}' version '{policy.version}' is {existing.status} and immutable"
                    )
            versions[policy.version] = policy
            return policy

    def activate_version(self, policy_key: str, version: str) -> EvaluationQuotaPolicy:
        with self._lock:
            versions = self._policies.get(policy_key)
            if not versions or version not in versions:
                raise KeyError(f"Policy '{policy_key}' version '{version}' not found")
            target = versions[version]
            if target.status == "RETIRED":
                raise ValueError(f"Cannot activate RETIRED policy version '{version}'")
            
            # Retire other active versions
            now = datetime.now(timezone.utc)
            for v, p in versions.items():
                if v != version and p.status == "ACTIVE":
                    p.status = "RETIRED"
            target.status = "ACTIVE"
            target.activated_at = now
            return target

    def retire_version(self, policy_key: str, version: str) -> EvaluationQuotaPolicy:
        with self._lock:
            versions = self._policies.get(policy_key)
            if not versions or version not in versions:
                raise KeyError(f"Policy '{policy_key}' version '{version}' not found")
            target = versions[version]
            target.status = "RETIRED"
            return target

    def list_policies(self) -> List[EvaluationQuotaPolicy]:
        with self._lock:
            out = []
            for versions in self._policies.values():
                out.extend(versions.values())
            return out


default_quota_policy_repository = QuotaPolicyRepository()
