"""
Tests for PROT-FINAL-07: Third-Party Supplier Assurance & LLM Governance
Covers COMP-006, COMP-007, COMP-016
"""

import pytest

from src.llm_service.isolated_adapter import IsolatedLLMAdapter, ProviderSecurityViolation
from src.services.compliance.supplier_assessment_service import supplier_assessment_service


def test_comp_006_llm_provider_configuration_server_side_only():
    """COMP-006: Asserts LLM credentials remain strictly server-side and client attempts to inject keys fail."""
    adapter = IsolatedLLMAdapter()

    # Reject client-supplied credentials
    with pytest.raises(ProviderSecurityViolation, match="Client-supplied provider credentials are strictly prohibited"):
        adapter.execute_completion(
            tenant_id="tenant-eval",
            user_prompt="Analyze legal compliance clause",
            client_supplied_key="sk-unauthorized-key",
        )


def test_comp_007_provider_retention_and_training_policies_recorded():
    """COMP-007: Validates that all LLM suppliers have documented retention policies and excluded model training."""
    res = supplier_assessment_service.audit_llm_providers()
    assert res["compliant"] is True
    assert res["llm_suppliers_count"] >= 2
    assert len(res["violations"]) == 0


def test_comp_016_supplier_exit_procedures_tested():
    """COMP-016: Asserts that all registered external suppliers have documented and verified exit plans."""
    res = supplier_assessment_service.verify_exit_procedures()
    assert res["compliant"] is True
    assert len(res["untested_exits"]) == 0
