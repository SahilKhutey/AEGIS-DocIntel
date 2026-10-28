"""
src/engines/governance/evidence_validator.py
============================================
Validation of evidence quotes against authoritative source document text.
"""

from __future__ import annotations

import re


class EvidenceValidationError(ValueError):
    """Raised when an evidence quote fails grounding validation against authoritative text."""
    pass


def validate_evidence_quote(
    *,
    quote: str,
    authoritative_text: str,
    minimum_chars: int = 8,
) -> None:
    """
    Validate that an evidence quote is non-empty, meets minimum length,
    and is strictly grounded in the authoritative source text.
    """
    if not quote or not isinstance(quote, str) or not quote.strip():
        raise EvidenceValidationError("Evidence quote is required.")

    cleaned_quote = quote.strip()
    if len(cleaned_quote) < minimum_chars:
        raise EvidenceValidationError(
            f"Evidence quote is too short (minimum {minimum_chars} characters required)."
        )

    if not authoritative_text or not isinstance(authoritative_text, str):
        raise EvidenceValidationError("Authoritative source text is empty or unavailable.")

    # 1. Exact match check
    if cleaned_quote in authoritative_text:
        return

    # 2. Case-insensitive substring match
    if cleaned_quote.lower() in authoritative_text.lower():
        return

    # 3. Normalized whitespace match
    normalized_quote = re.sub(r"\s+", " ", cleaned_quote).strip().lower()
    normalized_source = re.sub(r"\s+", " ", authoritative_text).strip().lower()
    if normalized_quote in normalized_source:
        return

    raise EvidenceValidationError(
        "Evidence quote is not present in the authoritative text."
    )
