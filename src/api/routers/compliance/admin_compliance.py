"""
AEGIS-DocIntel Admin Compliance Router
PROT-FINAL-07: Workstream 07.03, 07.08 & 07.10
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter

from src.repositories.compliance.control_repository import control_repository
from src.repositories.compliance.evidence_repository import evidence_repository
from src.services.compliance.compliance_reporting_service import compliance_reporting_service

router = APIRouter(prefix="/v1/admin/compliance", tags=["Compliance Admin"])


@router.get("/controls")
def list_controls() -> List[Dict[str, Any]]:
    """Lists all controls from the authoritative control register."""
    return control_repository.list_controls()


@router.get("/evidence")
def list_evidence() -> List[Dict[str, Any]]:
    """Lists all compliance evidence records."""
    return evidence_repository.list_evidence()


@router.get("/gates")
def evaluate_release_gates() -> Dict[str, Any]:
    """Evaluates release gates against all compliance domains (COMP-018)."""
    return compliance_reporting_service.evaluate_release_gates()
