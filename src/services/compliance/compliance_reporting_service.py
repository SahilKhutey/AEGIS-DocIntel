"""
AEGIS-DocIntel Compliance Reporting & Release Gate Evaluator
PROT-FINAL-07: Workstream 07.09 & 07.10

Aggregates compliance readiness across all ten work packages, evaluates
automated release gates (COMP-018), and produces the authoritative readiness posture.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from src.repositories.compliance.control_repository import control_repository
from src.services.compliance.control_register_service import control_register_service
from src.services.compliance.evidence_service import evidence_service
from src.services.compliance.policy_version_service import policy_version_service
from src.services.compliance.supplier_assessment_service import supplier_assessment_service

logger = logging.getLogger("aegis.compliance.compliance_reporting_service")


class ComplianceReportingService:
    def __init__(self):
        self.control_svc = control_register_service
        self.evidence_svc = evidence_service
        self.policy_svc = policy_version_service
        self.supplier_svc = supplier_assessment_service
        self.control_repo = control_repository

    def evaluate_release_gates(self) -> Dict[str, Any]:
        """
        COMP-018: Evaluates mandatory compliance release gates:
        1. All data processing activities have documented owners & purposes (COMP-001)
        2. Data flows match network policy allowlist (COMP-002)
        3. All compliance evidence artifacts exist and are valid (COMP-015)
        4. LLM model training is excluded and retention terms recorded (COMP-007)
        5. Supplier exit procedures are documented (COMP-016)
        6. Mandatory policies are approved and non-stale (COMP-013)
        7. No expired risk exceptions exist (COMP-017)
        """
        gate_1 = self.control_svc.audit_processing_activities()
        gate_2 = self.control_svc.verify_data_flow_alignment(
            approved_network_egress=["api.openai.com", "api.anthropic.com", "AWS S3 & EC2"]
        )
        gate_3 = self.evidence_svc.audit_all_evidence()
        gate_4 = self.supplier_svc.audit_llm_providers()
        gate_5 = self.supplier_svc.verify_exit_procedures()
        gate_6 = self.policy_svc.audit_policy_versions()
        gate_7 = self.policy_svc.audit_risk_exceptions()

        gates = {
            "GATE-COMP-01-ROPA": gate_1["compliant"],
            "GATE-COMP-02-DATA-FLOWS": gate_2["compliant"],
            "GATE-COMP-03-EVIDENCE-INTEGRITY": gate_3["compliant"],
            "GATE-COMP-04-LLM-SUPPLIER-TRAINING": gate_4["compliant"],
            "GATE-COMP-05-SUPPLIER-EXITS": gate_5["compliant"],
            "GATE-COMP-06-POLICY-CURRENCY": gate_6["compliant"],
            "GATE-COMP-07-RISK-EXCEPTIONS": gate_7["compliant"],
        }

        all_passed = all(gates.values())
        decision = "GO" if all_passed else "HOLD"

        return {
            "overall_decision": decision,
            "all_gates_passed": all_passed,
            "gates": gates,
            "details": {
                "ropa": gate_1,
                "data_flows": gate_2,
                "evidence": gate_3,
                "llm_suppliers": gate_4,
                "supplier_exits": gate_5,
                "policies": gate_6,
                "exceptions": gate_7,
            },
        }


compliance_reporting_service = ComplianceReportingService()
