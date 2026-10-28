"""
src/engines/intelligence/normalization.py
=========================================
Deterministic normalizers for currency amounts, units, dates, numbers,
and boolean values extracted from document passages.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional, Tuple


# Currency maps: symbols and abbreviations to ISO 4217 code
CURRENCY_SYMBOLS = {
    "$": "USD",
    "US$": "USD",
    "USD": "USD",
    "€": "EUR",
    "EUR": "EUR",
    "£": "GBP",
    "GBP": "GBP",
    "¥": "JPY",
    "JPY": "JPY",
    "₹": "INR",
    "INR": "INR",
    "C$": "CAD",
    "CAD": "CAD",
    "A$": "AUD",
    "AUD": "AUD",
    "CHF": "CHF",
}

# Scale multipliers
SCALE_MULTIPLIERS = {
    "thousand": 1_000.0,
    "thousands": 1_000.0,
    "k": 1_000.0,
    "million": 1_000_000.0,
    "millions": 1_000_000.0,
    "m": 1_000_000.0,
    "mn": 1_000_000.0,
    "billion": 1_000_000_000.0,
    "billions": 1_000_000_000.0,
    "b": 1_000_000_000.0,
    "bn": 1_000_000_000.0,
    "trillion": 1_000_000_000_000.0,
    "trillions": 1_000_000_000_000.0,
    "t": 1_000_000_000_000.0,
}

# Common month names
MONTH_NAMES = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


def parse_decimal(value: Any) -> Optional[float]:
    """
    Parse a numeric string or number into a standard float.
    Handles commas, spaces, percentage signs, accounting brackets, and magnitude suffixes.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    raw = str(value).strip()
    if not raw:
        return None

    # Check for accounting negative format: (1,234.50)
    is_negative = False
    if raw.startswith("(") and raw.endswith(")"):
        is_negative = True
        raw = raw[1:-1].strip()
    elif raw.startswith("-"):
        is_negative = True
        raw = raw[1:].strip()

    # Check for trailing %
    multiplier = 1.0
    if raw.endswith("%"):
        raw = raw[:-1].strip()

    # Check for scale suffix words (e.g. "1.5M", "250k", "2.5 billion")
    words = raw.split()
    remaining_words = []
    for w in words:
        clean_w = w.strip(".,;:()")
        if clean_w.lower() in SCALE_MULTIPLIERS:
            multiplier *= SCALE_MULTIPLIERS[clean_w.lower()]
        else:
            remaining_words.append(w)
    raw = " ".join(remaining_words).strip()

    # Check single token suffix like "10M" or "250k"
    match = re.match(r"^([\d.,]+)\s*([a-zA-Z]+)$", raw)
    if match:
        num_part = match.group(1)
        suffix_part = match.group(2).lower()
        if suffix_part in SCALE_MULTIPLIERS:
            raw = num_part
            multiplier *= SCALE_MULTIPLIERS[suffix_part]

    # Extract clean numeric sequence
    num_match = re.search(r"[\d]+(?:[.,\s]\d+)*", raw)
    if num_match:
        raw = num_match.group(0).strip()

    # Handle European format: e.g. "1.250.000,50" vs standard "1,250,000.50"
    if "," in raw and "." in raw:
        if raw.rfind(",") > raw.rfind("."):
            # European: dots are thousands, comma is decimal
            raw = raw.replace(".", "").replace(",", ".")
        else:
            # Standard: commas are thousands, dot is decimal
            raw = raw.replace(",", "")
    elif "," in raw:
        # If there's only comma, e.g. "1,250,000" or "50,5"
        parts = raw.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            # likely decimal: "50,5" or "50,50"
            raw = raw.replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif " " in raw:
        # E.g. "1 250 000.50"
        raw = raw.replace(" ", "")

    try:
        val = float(raw) * multiplier
        return -val if is_negative else val
    except ValueError:
        return None


def normalize_currency_amount(raw_text: str) -> Optional[Tuple[float, str]]:
    """
    Extract and normalize a currency amount and currency code.
    E.g.: "$1.5 million" -> (1500000.0, "USD")
          "€ 45,000" -> (45000.0, "EUR")
          "GBP 250,000" -> (250000.0, "GBP")
    """
    if not raw_text or not isinstance(raw_text, str):
        return None

    cleaned = raw_text.strip()
    detected_currency = None

    # 1. Match symbol at start or end
    for sym, code in CURRENCY_SYMBOLS.items():
        pattern = rf"(?i)(?:^|\s){re.escape(sym)}(?:\s*|\b)"
        if re.search(pattern, cleaned):
            detected_currency = code
            cleaned = re.sub(pattern, " ", cleaned).strip()
            break

    # 2. If not found, look for 3-letter currency code
    if not detected_currency:
        for code in set(CURRENCY_SYMBOLS.values()):
            pattern = rf"(?i)\b{re.escape(code)}\b"
            if re.search(pattern, cleaned):
                detected_currency = code
                cleaned = re.sub(pattern, " ", cleaned).strip()
                break

    if not detected_currency:
        return None

    # 3. Parse remaining numerical expression
    amount = parse_decimal(cleaned)
    if amount is None:
        return None

    return amount, detected_currency


def normalize_day_count(raw_text: str) -> Optional[Tuple[int, str]]:
    """
    Normalize duration expressions into an integer and canonical unit.
    E.g. "30 days" -> (30, "days")
         "45 calendar days" -> (45, "calendar_days")
         "10 business days" -> (10, "business_days")
         "12 months" -> (12, "months")
    """
    if not raw_text or not isinstance(raw_text, str):
        return None

    text = raw_text.strip().lower()

    # Look for number followed by unit
    match = re.search(r"(\d+)\s*(calendar\s+days?|business\s+days?|working\s+days?|days?|months?|years?|weeks?)", text)
    if not match:
        return None

    count = int(match.group(1))
    unit_raw = match.group(2)

    if "calendar" in unit_raw:
        unit = "calendar_days"
    elif "business" in unit_raw or "working" in unit_raw:
        unit = "business_days"
    elif "day" in unit_raw:
        unit = "days"
    elif "month" in unit_raw:
        unit = "months"
    elif "year" in unit_raw:
        unit = "years"
    elif "week" in unit_raw:
        unit = "weeks"
    else:
        unit = "days"

    return count, unit


def normalize_date(date_str: str) -> Optional[str]:
    """
    Normalize various date representations into ISO 8601 (YYYY-MM-DD or YYYY-MM or YYYY).
    Handles:
      - "2026-10-28"
      - "October 28, 2026" / "28 October 2026"
      - "Oct 28, 2026" / "28 Oct 2026"
      - "10/28/2026" or "28/10/2026"
      - "Q3 2026" / "2026-Q3"
      - "2026"
    """
    if not date_str or not isinstance(date_str, str):
        return None

    text = date_str.strip()

    # 1. ISO format: YYYY-MM-DD (with optional timestamp)
    iso_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:[T\s].*)?$", text)
    if iso_match:
        y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
        try:
            return datetime(y, m, d).strftime("%Y-%m-%d")
        except ValueError:
            return None

    # 2. Quarter: Q1 2026 or 2026-Q1
    q_match = re.match(r"^(?:(Q[1-4])[\s\-_]+(\d{4})|(\d{4})[\s\-_]+(Q[1-4]))$", text, re.IGNORECASE)
    if q_match:
        q = (q_match.group(1) or q_match.group(4)).upper()
        y = q_match.group(2) or q_match.group(3)
        return f"{y}-{q}"

    # 3. Year only
    if re.match(r"^\d{4}$", text):
        return text

    # 4. Textual month: "October 28, 2026", "28 October 2026", "Oct 28 2026"
    # Format: Month Day, Year
    text_match1 = re.search(r"([a-zA-Z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", text)
    if text_match1:
        month_name = text_match1.group(1).lower()
        if month_name in MONTH_NAMES:
            m = MONTH_NAMES[month_name]
            d = int(text_match1.group(2))
            y = int(text_match1.group(3))
            try:
                return datetime(y, m, d).strftime("%Y-%m-%d")
            except ValueError:
                pass

    # Format: Day Month Year (e.g. "28 October 2026")
    text_match2 = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+([a-zA-Z]+),?\s+(\d{4})", text)
    if text_match2:
        month_name = text_match2.group(2).lower()
        if month_name in MONTH_NAMES:
            m = MONTH_NAMES[month_name]
            d = int(text_match2.group(1))
            y = int(text_match2.group(3))
            try:
                return datetime(y, m, d).strftime("%Y-%m-%d")
            except ValueError:
                pass

    # Format: Month Year (e.g. "October 2026")
    text_match3 = re.search(r"([a-zA-Z]+)\s+(\d{4})", text)
    if text_match3:
        month_name = text_match3.group(1).lower()
        if month_name in MONTH_NAMES:
            m = MONTH_NAMES[month_name]
            y = int(text_match3.group(2))
            return f"{y:04d}-{m:02d}"

    # 5. Numerical slash or dash format: MM/DD/YYYY or DD/MM/YYYY
    slash_match = re.match(r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$", text)
    if slash_match:
        p1, p2, y = int(slash_match.group(1)), int(slash_match.group(2)), int(slash_match.group(3))
        # If p1 > 12, it must be DD/MM/YYYY
        if p1 > 12 and 1 <= p2 <= 12:
            d, m = p1, p2
        elif p2 > 12 and 1 <= p1 <= 12:
            m, d = p1, p2
        else:
            # Default to MM/DD/YYYY standard
            m, d = p1, p2
        try:
            return datetime(y, m, d).strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


def normalize_boolean(raw_text: Any) -> Optional[bool]:
    """Normalize common affirmative/negative boolean tokens."""
    if isinstance(raw_text, bool):
        return raw_text
    if raw_text is None:
        return None

    s = str(raw_text).strip().lower()
    if s in {"true", "yes", "1", "y", "required", "permitted", "enabled", "affirmative", "active", "provided", "shall indemnify", "agrees to indemnify"}:
        return True
    if s in {"false", "no", "0", "n", "waived", "prohibited", "disabled", "negative", "inactive", "excluded", "shall not indemnify"}:
        return False
    return None


def normalize_unit(unit_str: Optional[str]) -> Optional[str]:
    """Normalize unit labels into canonical identifiers."""
    if not unit_str or not isinstance(unit_str, str):
        return None

    s = unit_str.strip().lower()
    if s in {"$", "usd", "us dollars", "dollar", "dollars"}:
        return "USD"
    if s in {"€", "eur", "euros", "euro"}:
        return "EUR"
    if s in {"£", "gbp", "pounds", "british pounds"}:
        return "GBP"
    if s in {"%", "pct", "percent", "percentage"}:
        return "percent"
    if s in {"day", "days"}:
        return "days"
    if s in {"calendar day", "calendar days", "calendar_days"}:
        return "calendar_days"
    if s in {"business day", "business days", "working day", "working days", "business_days"}:
        return "business_days"
    if s in {"month", "months"}:
        return "months"
    if s in {"year", "years"}:
        return "years"
    if s in {"sq ft", "sqft", "square feet", "sq_ft"}:
        return "sq_ft"
    return unit_str.strip()
