"""
aegis.processing.normalization.dates
====================================
Date and timestamp normalization preserving raw string values and marking ambiguous locales.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


class DateNormalizer:
    """Normalizes dates to ISO-8601 (YYYY-MM-DD) while preserving raw strings and flagging ambiguity."""

    RULE_NAME = "iso8601_date_v1"

    @classmethod
    def normalize(
        cls,
        raw_text: str,
        locale: Optional[str] = None
    ) -> Tuple[Optional[str], str, str]:
        """Normalize date string.
        
        Returns: (normalized_date_or_none, status, rule_name)
        status: "SUCCESS" | "AMBIGUOUS" | "FAILED"
        """
        raw = raw_text.strip()
        if not raw:
            return None, "FAILED", cls.RULE_NAME

        # Pattern 1: ISO 8601: YYYY-MM-DD or YYYY/MM/DD
        m_iso = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", raw)
        if m_iso:
            y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
            try:
                dt = datetime(y, m, d)
                return dt.strftime("%Y-%m-%d"), "SUCCESS", cls.RULE_NAME
            except ValueError:
                return None, "FAILED", cls.RULE_NAME

        # Pattern 2: Explicit named month: "January 15, 2024" or "15 Jan 2024"
        month_names = {
            "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
            "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
            "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
            "nov": 11, "november": 11, "dec": 12, "december": 12
        }

        m_named1 = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$", raw)
        if m_named1:
            mon_str, day, year = m_named1.group(1).lower(), int(m_named1.group(2)), int(m_named1.group(3))
            if mon_str in month_names:
                try:
                    dt = datetime(year, month_names[mon_str], day)
                    return dt.strftime("%Y-%m-%d"), "SUCCESS", cls.RULE_NAME
                except ValueError:
                    return None, "FAILED", cls.RULE_NAME

        m_named2 = re.match(r"^(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})$", raw)
        if m_named2:
            day, mon_str, year = int(m_named2.group(1)), m_named2.group(2).lower(), int(m_named2.group(3))
            if mon_str in month_names:
                try:
                    dt = datetime(year, month_names[mon_str], day)
                    return dt.strftime("%Y-%m-%d"), "SUCCESS", cls.RULE_NAME
                except ValueError:
                    return None, "FAILED", cls.RULE_NAME

        # Pattern 3: Ambiguous slash or dot format: "03/04/2025"
        m_slash = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", raw)
        if m_slash:
            v1, v2, year = int(m_slash.group(1)), int(m_slash.group(2)), int(m_slash.group(3))
            # If both v1 <= 12 and v2 <= 12 and v1 != v2: ambiguous without locale!
            if v1 <= 12 and v2 <= 12 and v1 != v2:
                if locale == "US":  # MM/DD/YYYY
                    dt = datetime(year, v1, v2)
                    return dt.strftime("%Y-%m-%d"), "SUCCESS", cls.RULE_NAME
                elif locale in ["UK", "EU", "IN"]:  # DD/MM/YYYY
                    dt = datetime(year, v2, v1)
                    return dt.strftime("%Y-%m-%d"), "SUCCESS", cls.RULE_NAME
                else:
                    # Explicit policy: DO NOT GUESS without locale!
                    return None, "AMBIGUOUS", cls.RULE_NAME
            elif v1 > 12:  # Must be DD/MM/YYYY
                try:
                    dt = datetime(year, v2, v1)
                    return dt.strftime("%Y-%m-%d"), "SUCCESS", cls.RULE_NAME
                except ValueError:
                    return None, "FAILED", cls.RULE_NAME
            elif v2 > 12:  # Must be MM/DD/YYYY
                try:
                    dt = datetime(year, v1, v2)
                    return dt.strftime("%Y-%m-%d"), "SUCCESS", cls.RULE_NAME
                except ValueError:
                    return None, "FAILED", cls.RULE_NAME

        return None, "FAILED", cls.RULE_NAME
