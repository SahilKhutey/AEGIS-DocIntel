"""
tests/test_pii_precision_recall.py
===================================
P2.3 Privacy Validation, Precision & Recall Benchmark & Fail-Closed Redaction:
1. Precision and Recall quantification across synthetic labeled PII dataset.
2. Downstream leakage prevention and mandatory fail-closed blocking.
3. Multiple PII spans per block, table cell redaction, already-redacted text.
4. Safe aggregate telemetry (no raw PII in logs or reports).
"""
from __future__ import annotations

import pytest
from aegis_docprep.pii_redaction import (
    ComplianceReport,
    PIIEntity,
    PIIRedactionPolicyError,
    RedactionPolicy,
    apply_redaction_policy,
    detect_pii,
    redact_elements,
    redact_or_block,
)


LABELED_PII_DATASET = [
    # --- Emails ---
    {"text": "Contact our compliance lead at sarah.connor@cyberdyne.org for audits.", "expected": ["EMAIL"]},
    {"text": "Reach out to billing+invoices@saas-platform.co.uk today.", "expected": ["EMAIL"]},
    {"text": "Visit https://example.com/docs or ping @alex on slack.", "expected": []},
    # --- Phone numbers ---
    {"text": "Direct line is +1 (800) 555-0199 extension 4.", "expected": ["PHONE_NUMBER"]},
    {"text": "Call the London desk at +44 20 7946 0991 immediately.", "expected": ["PHONE_NUMBER"]},
    {"text": "Local support dispatch is 555-0142.", "expected": ["PHONE_NUMBER"]},
    {"text": "Release tag v2.4.1 published on 2026-10-24.", "expected": []},
    # --- SSN ---
    {"text": "Taxpayer identification: 000-12-3456.", "expected": ["US_SSN"]},
    {"text": "Ref code 12-345-6789 or order 987654321.", "expected": []},
    # --- Credit Card (Luhn Validated) ---
    {"text": "Visa primary card: 4532-0150-1234-5678.", "expected": ["CREDIT_CARD"]},  # Valid Luhn
    # --- API Keys & Credentials ---
    {"text": "Export OPENAI_API_KEY=sk-abcdef123456789012345678 in shell.", "expected": ["API_KEY"]},
    {"text": "AWS root access key AKIAIOSFODNN7EXAMPLE configured.", "expected": ["API_KEY"]},
    {"text": "GitHub token ghp_1234567890abcdef1234567890abcdef123456 generated.", "expected": ["API_KEY"]},
    {"text": "Token keyword or public key identifier abc12345.", "expected": []},
    # --- Person Names vs Exclusions ---
    {"text": "Authorized signatory: John Smith, Managing Director.", "expected": ["PERSON"]},
    {"text": "Meeting held in New York and San Francisco offices.", "expected": []},  # Geographic exclusions
    {"text": "Annual Executive Summary and Financial Table.", "expected": []},  # Stopword exclusions
]


def test_pii_precision_and_recall_metrics():
    """P2.3: Quantitative evaluation of PII detection Precision and Recall."""
    tp = 0
    fp = 0
    fn = 0

    for item in LABELED_PII_DATASET:
        text = item["text"]
        expected_types = item["expected"]
        entities = detect_pii(text)
        detected_types = [e.entity_type for e in entities]

        for exp in expected_types:
            if exp in detected_types:
                tp += 1
            else:
                fn += 1

        for det in detected_types:
            if det not in expected_types:
                fp += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0

    assert precision >= 0.85, f"PII Precision below threshold: {precision:.2f}"
    assert recall >= 0.90, f"PII Recall below threshold: {recall:.2f}"


def test_multiple_spans_in_single_paragraph():
    """P2.3: Multiple sensitive spans of different categories in one paragraph are cleanly redacted."""
    text = "Officer Jane Doe (SSN: 000-12-3456, Phone: +1 800 555 0199) deployed key sk-abcdef123456789012345678."
    redacted, report = redact_or_block(text, mandatory=True)

    assert "000-12-3456" not in redacted
    assert "+1 800 555 0199" not in redacted
    assert "sk-abcdef123456789012345678" not in redacted
    assert report.redactions_applied >= 3


def test_pii_in_table_structure():
    """P2.3: PII elements inside table cells are redacted while preserving table layout."""
    table_cell = {
        "id": "cell_1",
        "content": "Client: alice.wonderland@domain.com | Phone: 555-0188",
    }
    redacted, report = redact_elements([table_cell])
    assert "alice.wonderland@domain.com" not in redacted[0]["content"]
    assert "555-0188" not in redacted[0]["content"]
    assert report.redactions_applied >= 2


def test_already_redacted_text_does_not_double_redact():
    """P2.3: Text that has already undergone redaction is stable and idempotent."""
    text = "Contact <EMAIL_REDACTED> or call <PHONE_NUMBER_REDACTED>."
    redacted, report = redact_or_block(text, mandatory=True)
    assert redacted == text
    assert report.redactions_applied == 0


def test_mandatory_redaction_failure_blocks_downstream_transfer(monkeypatch):
    """P2.3: Failure in mandatory redaction raises PIIRedactionPolicyError to prevent plaintext leaks."""
    from aegis_docprep import pii_redaction

    def broken_detect(el):
        raise RuntimeError("Internal regex failure / catastrophic backtracking")

    monkeypatch.setattr(pii_redaction, "detect_pii", broken_detect)

    with pytest.raises(PIIRedactionPolicyError, match="Mandatory redaction failed"):
        redact_or_block("Secret text with alice@secret.org", mandatory=True)


def test_safe_aggregate_telemetry_contains_no_raw_secrets():
    """P2.3: Compliance report telemetry records counts and categories, never raw secret text."""
    text = "Sensitive data: sk-abcdef123456789012345678 and 000-12-3456."
    redacted, report = redact_or_block(text, mandatory=True)

    # In safe aggregate telemetry representation
    telemetry = report.safe_summary()
    tel_str = str(telemetry)
    assert "sk-abcdef123456789012345678" not in tel_str
    assert "000-12-3456" not in tel_str
    assert telemetry["redactions_applied"] == 2
    assert "API_KEY" in telemetry["entity_categories"]
    assert "US_SSN" in telemetry["entity_categories"]
