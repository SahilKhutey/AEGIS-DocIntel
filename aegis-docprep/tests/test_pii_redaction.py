"""
Tests for aegis_docprep.pii_redaction.
"""

from __future__ import annotations

import pytest
from aegis_docprep.pii_redaction import (
    ComplianceReport,
    PIIEntity,
    RedactionPolicy,
    _luhn_check,
    apply_redaction_policy,
    detect_pii,
    redact_elements,
)


def test_detects_ssn_and_validates_credit_card():
    results = detect_pii({"id": "e1", "text": "SSN 123-45-6789, card 4532015112830366."})
    types = {r.entity_type for r in results}
    assert "US_SSN" in types
    assert "CREDIT_CARD" in types

    cc = next(r for r in results if r.entity_type == "CREDIT_CARD")
    assert cc.score >= 0.9  # Luhn-valid card should score 0.95


def test_detects_phone_number_and_person():
    results = detect_pii({"id": "e2", "text": "Contact Jane Doe at 555-123-4567 regarding invoices."})
    types = {r.entity_type for r in results}
    assert "PHONE_NUMBER" in types
    assert "PERSON" in types

    person = next(r for r in results if r.entity_type == "PERSON")
    assert person.text == "Jane Doe"
    assert person.score >= 0.8


def test_luhn_algorithm_mod10():
    # Valid Visa card
    assert _luhn_check("4532015112830366") is True
    # Invalid card number (last digit altered)
    assert _luhn_check("4532015112830367") is False


def test_apply_redaction_policy_string_input():
    text = "Call John Smith at 555-123-4567, SSN 123-45-6789."
    entities = detect_pii(text)
    redacted = apply_redaction_policy(text, entities)
    assert isinstance(redacted, str)
    assert "123-45-6789" not in redacted
    assert "555-123-4567" not in redacted
    assert "<US_SSN_REDACTED>" in redacted


def test_apply_redaction_policy_dict_input():
    elem = {"id": "d1", "text": "SSN: 987-65-4321", "doc_id": "test_doc"}
    entities = detect_pii(elem)
    policies = [RedactionPolicy("US_SSN", "redact", replacement="[SSN_SCRUBBED]")]
    redacted_dict, report = apply_redaction_policy(elem, entities, policies)

    assert isinstance(redacted_dict, dict)
    assert "[SSN_SCRUBBED]" in redacted_dict["text"]
    assert "987-65-4321" not in redacted_dict["text"]
    assert report.redactions_applied == 1
    assert report.document_id == "test_doc"


def test_redact_elements_dict_list():
    elements = [
        {"id": "p1", "text": "Contact Alice Brown at 555-987-6543."},
        {"id": "p2", "text": "No PII present in this paragraph."},
    ]
    redacted_elems, report = redact_elements(elements)
    assert len(redacted_elems) == 2
    assert "555-987-6543" not in redacted_elems[0]["text"]
    assert report.redactions_applied >= 1
