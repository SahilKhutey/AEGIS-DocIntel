"""
Unit tests for Credit Card Luhn mod-10 validation (Session 7 Audit).
"""

import pytest
from src.compliance.redaction_engine import _luhn_check, detect_pii


def test_valid_luhn_credit_cards():
    """Test valid credit card numbers pass Luhn check."""
    # Standard test Visa, Mastercard, Amex numbers
    assert _luhn_check("4532-0151-1283-0366")
    assert _luhn_check("4111 1111 1111 1111")
    assert _luhn_check("378282246310005")



def test_invalid_luhn_number():
    """Test invalid 16-digit sequences fail Luhn check."""
    # Sequential 16-digit invoice format
    assert not _luhn_check("1234-5678-9012-3456")
    assert not _luhn_check("1111-1111-1111-1111")


def test_credit_card_pii_detection_scores():
    """Confirms valid cards get 0.95 score while non-Luhn 16-digit strings get 0.55 score."""
    valid_card_elem = {"id": "e1", "text": "Card: 4532-0151-1283-0366"}
    invoice_elem = {"id": "e2", "text": "Invoice Ref: 1234-5678-9012-3456"}

    valid_entities = detect_pii(valid_card_elem)
    invoice_entities = detect_pii(invoice_elem)

    assert len(valid_entities) == 1
    assert valid_entities[0].score == 0.95

    assert len(invoice_entities) == 1
    assert invoice_entities[0].score == 0.55


def test_short_and_long_digit_strings():
    assert not _luhn_check("123")
    assert not _luhn_check("123456789012345678901234")


def test_luhn_with_mixed_formatting():
    assert _luhn_check("4532 0151-1283.0366")


def test_redact_valid_card():
    elem = {"id": "e1", "text": "Pay with 4532-0151-1283-0366."}
    entities = detect_pii(elem)
    assert len(entities) == 1
    assert entities[0].score == 0.95


def test_non_luhn_downgrade_does_not_false_positive_as_high_confidence():
    elem = {"id": "e1", "text": "Order ID 1234 5678 9012 3456"}
    entities = detect_pii(elem)
    assert len(entities) == 1
    assert entities[0].score < 0.90
