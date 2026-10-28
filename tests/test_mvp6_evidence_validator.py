"""
tests/test_mvp6_evidence_validator.py
=====================================
Unit tests for evidence quote validation against authoritative source text.
"""

import pytest
from src.engines.governance.evidence_validator import (
    EvidenceValidationError,
    validate_evidence_quote,
)

AUTH_TEXT = """
Section 12: Payment Terms and Conditions.
Payment is due strictly within thirty (30) days from invoice receipt date.
The maximum aggregate liability shall not exceed INR 1,250.50 under any circumstance.
"""


def test_validate_evidence_quote_success():
    # Exact match
    validate_evidence_quote(
        quote="Payment is due strictly within thirty (30) days",
        authoritative_text=AUTH_TEXT,
    )

    # Case-insensitive match
    validate_evidence_quote(
        quote="PAYMENT IS DUE STRICTLY WITHIN THIRTY (30) DAYS",
        authoritative_text=AUTH_TEXT,
    )

    # Normalized whitespace match
    validate_evidence_quote(
        quote="Payment is due strictly   within thirty (30) days",
        authoritative_text=AUTH_TEXT,
    )


def test_validate_evidence_quote_too_short():
    with pytest.raises(EvidenceValidationError, match="too short"):
        validate_evidence_quote(
            quote="due",
            authoritative_text=AUTH_TEXT,
            minimum_chars=8,
        )


def test_validate_evidence_quote_empty():
    with pytest.raises(EvidenceValidationError, match="quote is required"):
        validate_evidence_quote(
            quote="   ",
            authoritative_text=AUTH_TEXT,
        )


def test_validate_evidence_quote_absent_from_text():
    with pytest.raises(EvidenceValidationError, match="not present in the authoritative text"):
        validate_evidence_quote(
            quote="Unlimited damages shall be awarded",
            authoritative_text=AUTH_TEXT,
        )


def test_validate_evidence_quote_empty_authoritative_text():
    with pytest.raises(EvidenceValidationError, match="Authoritative source text is empty"):
        validate_evidence_quote(
            quote="Valid length quote here",
            authoritative_text="",
        )
