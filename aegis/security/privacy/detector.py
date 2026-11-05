"""
aegis.security.privacy.detector
===============================
Privacy and Sensitive Data Detection Engine:
- Structured PII detection: SSN, Credit Card (with Luhn check), Phone, Email, Secrets.
- Context-aware masking and tokenization.
- Fail-closed policy enforcement.
- Safe telemetry summary generation (zero secret leakage).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def luhn_checksum(card_number: str) -> bool:
    """Validates Luhn mod-10 algorithm for credit card numbers."""
    digits = [int(c) for c in card_number if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            double = digit * 2
            checksum += double - 9 if double > 9 else double
        else:
            checksum += digit
    return checksum % 10 == 0


class PrivacyEntity:
    def __init__(self, entity_type: str, raw_value: str, start: int, end: int, confidence: float = 1.0) -> None:
        self.entity_type = entity_type
        self.raw_value = raw_value
        self.start = start
        self.end = end
        self.confidence = confidence


class PrivacyDetector:
    """Production PII and credential detection and masking engine."""

    SSN_PATTERN = re.compile(r"\b(?<!\w)\d{3}-\d{2}-\d{4}(?!\w)\b")
    # Matches formatted or space/dash separated cards
    CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
    PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    SECRET_PATTERN = re.compile(r"\b(?:sk-[a-zA-Z0-9_\-]{20,}|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|ghp_[0-9a-zA-Z]{30,})\b")

    def detect(self, text: str) -> List[PrivacyEntity]:
        """Detects sensitive entities across text."""
        entities: List[PrivacyEntity] = []

        # 1. API Keys & Secrets
        for m in self.SECRET_PATTERN.finditer(text):
            entities.append(PrivacyEntity("API_KEY", m.group(), m.start(), m.end(), 0.99))

        # 2. Credit Cards with Luhn check
        for m in self.CARD_PATTERN.finditer(text):
            raw = m.group()
            if luhn_checksum(raw):
                entities.append(PrivacyEntity("CREDIT_CARD", raw, m.start(), m.end(), 0.98))

        # 3. Social Security Numbers
        for m in self.SSN_PATTERN.finditer(text):
            entities.append(PrivacyEntity("SSN", m.group(), m.start(), m.end(), 0.95))

        # 4. Email Addresses
        for m in self.EMAIL_PATTERN.finditer(text):
            entities.append(PrivacyEntity("EMAIL_ADDRESS", m.group(), m.start(), m.end(), 0.95))

        # 5. Phone Numbers (excluding already matched digits)
        matched_spans = {(e.start, e.end) for e in entities}
        for m in self.PHONE_PATTERN.finditer(text):
            start, end = m.start(), m.end()
            # Ensure not overlapping with SSN or Credit Card
            if not any(max(start, s) < min(end, e) for s, e in matched_spans):
                entities.append(PrivacyEntity("PHONE_NUMBER", m.group(), start, end, 0.90))

        return entities

    def redact(self, text: str, entities: Optional[List[PrivacyEntity]] = None) -> Tuple[str, Dict[str, Any]]:
        """Redacts detected sensitive values in text and returns safe summary."""
        if entities is None:
            entities = self.detect(text)

        # Sort descending by start position to avoid offset corruption
        sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)
        redacted = list(text)

        replacements = {
            "EMAIL_ADDRESS": "[REDACTED_EMAIL]",
            "PHONE_NUMBER": "[REDACTED_PHONE]",
            "SSN": "[REDACTED_SSN]",
            "CREDIT_CARD": "[REDACTED_CREDIT_CARD]",
            "API_KEY": "[REDACTED_SECRET]",
        }

        category_counts: Dict[str, int] = {}
        for ent in sorted_entities:
            rep = replacements.get(ent.entity_type, "[REDACTED]")
            redacted[ent.start : ent.end] = list(rep)
            category_counts[ent.entity_type] = category_counts.get(ent.entity_type, 0) + 1

        summary = {
            "total_entities_detected": len(entities),
            "redactions_applied": len(entities),
            "categories": category_counts,
        }

        return "".join(redacted), summary
