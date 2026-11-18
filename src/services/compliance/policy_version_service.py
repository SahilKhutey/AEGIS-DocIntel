"""
AEGIS-DocIntel Policy Version & Exception Management Service
PROT-FINAL-07: Workstream 07.04

Tracks compliance policies and risk exceptions:
- COMP-013: Policy versions and approvals are traceable and active.
- COMP-017: Documented exceptions are validated for approval and non-expired horizons.
"""

from __future__ import annotations

import csv
import logging
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("aegis.compliance.policy_version_service")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REGISTERS_DIR = REPO_ROOT / "compliance" / "registers"


class PolicyVersionService:
    def __init__(self):
        self.policy_file = REGISTERS_DIR / "policy_approval_register.csv"
        self.exception_file = REGISTERS_DIR / "exceptions_and_risk_acceptance.csv"

    def audit_policy_versions(self) -> Dict[str, Any]:
        """
        COMP-013: Verifies that all mandatory policies are approved and non-stale.
        """
        if not self.policy_file.exists():
            return {"compliant": False, "error": "policy_approval_register.csv missing", "stale": []}

        today = date.today()
        policies = []
        stale_policies = []

        with open(self.policy_file, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                policies.append(row)
                review_str = row.get("next_review_date", "")
                status = row.get("approval_status", "").lower()
                if status != "approved":
                    stale_policies.append(f"{row.get('policy_id')}: status={status}")
                    continue
                if review_str:
                    review_date = datetime.strptime(review_str, "%Y-%m-%d").date()
                    if review_date < today:
                        stale_policies.append(f"{row.get('policy_id')}: review overdue ({review_str})")

        compliant = len(stale_policies) == 0 and len(policies) >= 12
        return {
            "compliant": compliant,
            "total_policies": len(policies),
            "stale_policies": stale_policies,
            "policies": policies,
        }

    def audit_risk_exceptions(self) -> Dict[str, Any]:
        """
        COMP-017: Checks that documented risk exceptions have valid approvals and have not expired.
        """
        if not self.exception_file.exists():
            return {"compliant": True, "total_exceptions": 0, "expired_exceptions": []}

        today = date.today()
        exceptions = []
        expired = []

        with open(self.exception_file, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                exceptions.append(row)
                exp_str = row.get("expiry_date", "")
                status = row.get("approval_status", "").lower()
                if status != "approved":
                    expired.append(f"{row.get('exception_id')}: not approved ({status})")
                    continue
                if exp_str:
                    exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
                    if exp_date < today:
                        expired.append(f"{row.get('exception_id')}: expired on {exp_str}")

        compliant = len(expired) == 0
        return {
            "compliant": compliant,
            "total_exceptions": len(exceptions),
            "expired_exceptions": expired,
            "exceptions": exceptions,
        }


policy_version_service = PolicyVersionService()
