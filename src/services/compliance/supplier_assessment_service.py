"""
AEGIS-DocIntel Supplier Assessment Service
PROT-FINAL-07: Workstream 07.06

Assesses third-party suppliers and LLM providers:
- COMP-006: LLM provider configuration verified (server-side secrets only).
- COMP-007: Provider data retention terms and training policies recorded.
- COMP-016: Supplier exit and migration procedures tested.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from src.repositories.compliance.supplier_repository import supplier_repository

logger = logging.getLogger("aegis.compliance.supplier_assessment_service")


class SupplierAssessmentService:
    def __init__(self):
        self.supplier_repo = supplier_repository

    def audit_llm_providers(self) -> Dict[str, Any]:
        """
        COMP-007: Validates that all external LLM providers have documented retention terms
        and that customer data is excluded from foundation model training.
        """
        llm_sups = self.supplier_repo.get_llm_suppliers()
        if not llm_sups:
            return {"compliant": False, "error": "No LLM suppliers registered", "violations": []}

        violations = []
        for sup in llm_sups:
            sup_id = sup.get("supplier_id")
            training = sup.get("model_training", "").upper()
            retention = sup.get("retention_policy", "")

            # Ensure model training is explicitly NO / Excluded
            if "NO" not in training and "EXCLUDED" not in training:
                violations.append(f"{sup_id}: Model training is not explicitly excluded ({training})")

            # Ensure retention policy is recorded
            if not retention or "N/A" in retention:
                violations.append(f"{sup_id}: Missing documented retention policy")

        compliant = len(violations) == 0
        return {
            "compliant": compliant,
            "llm_suppliers_count": len(llm_sups),
            "violations": violations,
            "suppliers": llm_sups,
        }

    def verify_exit_procedures(self) -> Dict[str, Any]:
        """
        COMP-016: Asserts that all active suppliers have documented and tested exit procedures.
        """
        all_sups = self.supplier_repo.list_suppliers()
        untested_exits = []

        for s in all_sups:
            sup_id = s.get("supplier_id")
            exit_tested = s.get("exit_plan_tested", "").lower() == "true"
            if not exit_tested:
                untested_exits.append(sup_id)

        compliant = len(untested_exits) == 0 and len(all_sups) > 0
        return {
            "compliant": compliant,
            "total_suppliers": len(all_sups),
            "untested_exits": untested_exits,
        }


supplier_assessment_service = SupplierAssessmentService()
