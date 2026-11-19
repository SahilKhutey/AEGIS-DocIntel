"""
Tests for Work Package PH-09:
Analytics, Measurement, Conversion Ratios, and Zero-PII Telemetry Compliance.
"""

from pathlib import Path
import json
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ANALYTICS_DIR = REPO_ROOT / "launch" / "product-hunt" / "analytics"
AUDIT_ANALYTICS = REPO_ROOT / "audit" / "prot-final-09" / "product-hunt" / "analytics"


def test_event_schema_zero_pii_invariant():
    """Verify that registered telemetry events contain zero personally identifiable information."""
    schema_file = AUDIT_ANALYTICS / "event-schema-audit.json"
    assert schema_file.exists()
    with schema_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["pii_audit"] == "CLEAN_ZERO_PII"
    events = data["registered_events"]
    assert "ph_referral_landed" in events
    assert "device_activated" in events
    assert "first_doc_processed" in events
    assert "feedback_submitted" in events

    forbidden_pii_keys = [
        "email", "user_email", "name", "full_name", "phone", "ssn",
        "pan", "credit_card", "password", "raw_ip", "ip_address",
        "query_text", "document_content", "document_text"
    ]

    event_plan_text = (ANALYTICS_DIR / "EVENT_TRACKING_PLAN.md").read_text(encoding="utf-8")
    for key in forbidden_pii_keys:
        # Check that forbidden keys are not listed as payload properties
        assert f"`{key}`" not in event_plan_text, f"Forbidden PII key `{key}` found in telemetry plan"


def test_conversion_kpi_definitions_and_formulas():
    """Verify KPI conversion rate mathematical definitions."""
    kpi_file = ANALYTICS_DIR / "KPI_DEFINITIONS.md"
    assert kpi_file.exists()
    content = kpi_file.read_text(encoding="utf-8")

    assert "Visit-to-Signup" in content
    assert "Signup-to-Activation" in content
    assert "Activation-to-First-Use" in content
    assert "Repeat Engagement" in content
    assert "Feedback Conversion" in content


def test_kpi_numerical_targets():
    """Verify quantitative KPI baseline targets in audit registry."""
    targets_file = AUDIT_ANALYTICS / "kpi-targets.json"
    assert targets_file.exists()
    with targets_file.open("r", encoding="utf-8") as f:
        data = json.load(f)["targets"]

    assert data["page_visits"] >= 100
    assert data["registrations"] >= 20
    assert data["activations"] >= 10
    assert data["first_document_completions"] >= 10
    assert data["feedback_submissions"] >= 5
    assert data["critical_defects"] == 0


def test_privacy_telemetry_compliance_guarantees():
    """Verify cookieless and regulatory compliance flags."""
    compliance_file = AUDIT_ANALYTICS / "privacy-telemetry-compliance.json"
    assert compliance_file.exists()
    with compliance_file.open("r", encoding="utf-8") as f:
        comp = json.load(f)

    assert comp["cookieless_tracking"] is True
    assert comp["ip_redaction_enforced"] is True
    assert comp["query_text_excluded"] is True
    assert comp["document_payloads_excluded"] is True
    assert comp["gdpr_compliance"] is True
    assert comp["dpdp_act_2023_compliance"] is True
