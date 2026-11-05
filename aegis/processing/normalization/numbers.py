"""
aegis.processing.normalization.numbers
======================================
Numeric, financial currency, and percentage normalizer preserving raw strings.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple


CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
}


class NumberNormalizer:
    """Normalizes numbers, financial currency figures, and percentages."""

    RULE_NAME = "financial_numeric_v1"

    @classmethod
    def normalize(cls, raw_text: str) -> Tuple[Optional[Dict[str, Any]], str, str]:
        """Parse numeric values with currency and signs.
        
        Returns: (parsed_dict_or_none, status, rule_name)
        """
        raw = raw_text.strip()
        if not raw:
            return None, "FAILED", cls.RULE_NAME

        currency = None
        for sym, code in CURRENCY_SYMBOLS.items():
            if sym in raw:
                currency = code
                break

        is_percentage = "%" in raw
        is_negative = False

        # Accounting negative: ($1,250.00) or -$1,250.00 or -1250
        if raw.startswith("(") and raw.endswith(")"):
            is_negative = True
            inner = raw[1:-1].strip()
        elif raw.startswith("-"):
            is_negative = True
            inner = raw[1:].strip()
        else:
            inner = raw

        # Remove currency symbols, commas, spaces, percent signs
        cleaned_digits = re.sub(r"[^\d.]", "", inner)
        if not cleaned_digits:
            return None, "FAILED", cls.RULE_NAME

        try:
            val = float(cleaned_digits)
            if is_negative:
                val = -val

            parsed = {
                "value": val,
                "currency": currency,
                "is_percentage": is_percentage,
                "raw_string": raw,
            }
            return parsed, "SUCCESS", cls.RULE_NAME
        except ValueError:
            return None, "FAILED", cls.RULE_NAME
