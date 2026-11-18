"""
Tests for PROT-FINAL-07: Governance, Data Flows, Policies & Risk Exceptions
Covers COMP-001, COMP-002, COMP-013, COMP-017
"""

import pytest

from src.services.compliance.control_register_service import control_register_service
from src.services.compliance.policy_version_service import policy_version_service


def test_comp_001_every_processing_activity_has_owner_and_purpose():
    """COMP-001: Verifies that every data processing activity in RoPA has an owner and lawful purpose."""
    res = control_register_service.audit_processing_activities()
    assert res["compliant"] is True
    assert res["total_activities"] >= 5
    assert len(res["unowned_activities"]) == 0


def test_comp_002_data_flows_match_service_integrations():
    """COMP-002: Verifies that data flow recipients match approved network destinations with no undocumented egress."""
    approved_egress = ["api.openai.com", "api.anthropic.com", "AWS S3 & EC2"]
    res = control_register_service.verify_data_flow_alignment(approved_egress)
    assert res["compliant"] is True
    assert len(res["undocumented_transfers"]) == 0


def test_comp_013_policy_versions_and_approvals():
    """COMP-013: Asserts that all compliance policies have approved status and active review horizons."""
    res = policy_version_service.audit_policy_versions()
    assert res["compliant"] is True
    assert res["total_policies"] >= 12
    assert len(res["stale_policies"]) == 0


def test_comp_017_exceptions_approval_and_expiry():
    """COMP-017: Asserts that all documented risk exceptions are approved and have not expired."""
    res = policy_version_service.audit_risk_exceptions()
    assert res["compliant"] is True
    assert len(res["expired_exceptions"]) == 0
