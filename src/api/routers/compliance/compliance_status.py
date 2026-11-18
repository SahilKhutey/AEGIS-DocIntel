"""
AEGIS-DocIntel Compliance Status Router
PROT-FINAL-07: Workstream 07.09
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

from src.repositories.compliance.control_repository import control_repository
from src.services.compliance.compliance_reporting_service import compliance_reporting_service

router = APIRouter(prefix="/v1/compliance", tags=["Compliance Status"])


@router.get("/status")
def get_compliance_status() -> Dict[str, Any]:
    """Returns the high-level compliance programme status and regulatory alignment."""
    obligations = control_repository.list_obligations()
    gates = compliance_reporting_service.evaluate_release_gates()
    return {
        "status": "COMPLIANCE_READY",
        "programme_version": "1.1.0",
        "release_gate_decision": gates["overall_decision"],
        "aligned_frameworks": [
            "India DPDP Act 2023 (Self-Assessed)",
            "EU GDPR (Self-Assessed)",
            "US State Privacy Laws / CCPA (Self-Assessed)",
            "ISO/IEC 27001:2022 (ISMS Aligned)",
            "SOC 2 Type II (Criteria Aligned)",
        ],
        "obligations_tracked": len(obligations),
        "disclaimer": (
            "Compliance readiness is an internal technical governance posture, not a legal certification. "
            "Legal counsel review is required prior to external distribution."
        ),
    }
