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


def test_person_name_with_preceding_label_does_not_leak_surname():
    """Regression test for I-15: Capitalized label before name must not leak surname."""
    for text in [
        "Customer John Smith called about the account.",
        "Call John Smith at the office.",
        "Patient Jane Doe checked in.",
        "Dear Customer Alice Brown, your order is ready.",
    ]:
        entities = detect_pii(text)
        persons = [e for e in entities if e.entity_type == "PERSON"]
        assert len(persons) == 1, f"Expected 1 PERSON in '{text}', found: {persons}"
        assert persons[0].text in ("John Smith", "Jane Doe", "Alice Brown")
        redacted = apply_redaction_policy(text, entities)
        assert "Smith" not in redacted
        assert "Doe" not in redacted
        assert "Brown" not in redacted


def test_person_name_three_words():
    text = "Please reach out to John William Smith immediately."
    entities = detect_pii(text)
    persons = [e for e in entities if e.entity_type == "PERSON"]
    assert len(persons) == 1
    assert persons[0].text == "John William Smith"
    redacted = apply_redaction_policy(text, entities)
    assert "Smith" not in redacted
    assert "<PERSON_REDACTED>" in redacted


def test_person_name_trailing_label():
    text = "Report authored by John Smith Table analysis."
    entities = detect_pii(text)
    persons = [e for e in entities if e.entity_type == "PERSON"]
    assert len(persons) == 1
    assert persons[0].text == "John Smith"


def test_detects_email_and_api_keys():
    text = "Contact alice.smith@example.com using token sk-ant-api03-abcdef1234567890abcdef."
    entities = detect_pii(text)
    types = {e.entity_type for e in entities}
    assert "EMAIL" in types
    assert "API_KEY" in types

    email_ent = next(e for e in entities if e.entity_type == "EMAIL")
    assert email_ent.text == "alice.smith@example.com"

    key_ent = next(e for e in entities if e.entity_type == "API_KEY")
    assert key_ent.text == "sk-ant-api03-abcdef1234567890abcdef"

    redacted = apply_redaction_policy(text, entities)
    assert "alice.smith@example.com" not in redacted
    assert "sk-ant-api03-abcdef1234567890abcdef" not in redacted
    assert "<EMAIL_REDACTED>" in redacted
    assert "<API_KEY_REDACTED>" in redacted


def test_detects_international_and_local_phone_numbers():
    text = "UK office: +44 20 7946 0958, local extension: 555-0100."
    entities = detect_pii(text)
    phones = [e for e in entities if e.entity_type == "PHONE_NUMBER"]
    assert len(phones) == 2
    phone_texts = {p.text for p in phones}
    assert "+44 20 7946 0958" in phone_texts
    assert "555-0100" in phone_texts

    redacted = apply_redaction_policy(text, entities)
    assert "+44 20 7946 0958" not in redacted
    assert "555-0100" not in redacted


