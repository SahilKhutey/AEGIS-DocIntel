"""
tests/test_mvp5_normalization.py
================================
Unit tests for deterministic normalization of currency, units, dates, numbers, and booleans.
"""

import math
import pytest
from src.engines.intelligence.normalization import (
    normalize_boolean,
    normalize_currency_amount,
    normalize_date,
    normalize_day_count,
    normalize_unit,
    parse_decimal,
)


def test_parse_decimal_numeric_and_formats():
    assert parse_decimal(100) == 100.0
    assert parse_decimal("1,234,567.89") == 1234567.89
    assert parse_decimal("1.234.567,89") == 1234567.89
    assert parse_decimal("1 250 000.50") == 1250000.50
    assert parse_decimal("-45.25") == -45.25
    assert parse_decimal("(1,500.00)") == -1500.00
    assert parse_decimal("15.5%") == 15.5
    assert parse_decimal(None) is None
    assert parse_decimal("invalid-string") is None


def test_parse_decimal_scale_multipliers():
    assert parse_decimal("2.5 million") == 2500000.0
    assert parse_decimal("10 billion") == 10000000000.0
    assert parse_decimal("250k") == 250000.0
    assert parse_decimal("1.2M") == 1200000.0
    assert parse_decimal("3.4 billion was recorded") == 3400000000.0


def test_normalize_currency_amount():
    res = normalize_currency_amount("$1.5 million")
    assert res is not None
    val, curr = res
    assert math.isclose(val, 1500000.0)
    assert curr == "USD"

    res_eur = normalize_currency_amount("€ 45,000")
    assert res_eur == (45000.0, "EUR")

    res_gbp = normalize_currency_amount("£250k")
    assert res_gbp == (250000.0, "GBP")

    res_cad = normalize_currency_amount("CAD 1,200.50")
    assert res_cad == (1200.50, "CAD")

    assert normalize_currency_amount("no amount here") is None


def test_normalize_day_count():
    assert normalize_day_count("30 days") == (30, "days")
    assert normalize_day_count("45 calendar days") == (45, "calendar_days")
    assert normalize_day_count("10 business days") == (10, "business_days")
    assert normalize_day_count("12 months") == (12, "months")
    assert normalize_day_count("2 years") == (2, "years")
    assert normalize_day_count("invalid") is None


def test_normalize_date():
    assert normalize_date("2026-10-28") == "2026-10-28"
    assert normalize_date("2026-10-28T14:30:00Z") == "2026-10-28"
    assert normalize_date("October 28, 2026") == "2026-10-28"
    assert normalize_date("28 October 2026") == "2026-10-28"
    assert normalize_date("Oct 28, 2026") == "2026-10-28"
    assert normalize_date("28 Oct 2026") == "2026-10-28"
    assert normalize_date("10/28/2026") == "2026-10-28"
    assert normalize_date("28/10/2026") == "2026-10-28"
    assert normalize_date("Q3 2026") == "2026-Q3"
    assert normalize_date("2026-Q1") == "2026-Q1"
    assert normalize_date("2026") == "2026"
    assert normalize_date("October 2026") == "2026-10"
    assert normalize_date("not a date") is None


def test_normalize_boolean():
    assert normalize_boolean("true") is True
    assert normalize_boolean("yes") is True
    assert normalize_boolean("required") is True
    assert normalize_boolean("permitted") is True
    assert normalize_boolean("shall indemnify") is True
    assert normalize_boolean("false") is False
    assert normalize_boolean("no") is False
    assert normalize_boolean("waived") is False
    assert normalize_boolean("prohibited") is False
    assert normalize_boolean("shall not indemnify") is False
    assert normalize_boolean(None) is None


def test_normalize_unit():
    assert normalize_unit("$") == "USD"
    assert normalize_unit("US Dollars") == "USD"
    assert normalize_unit("€") == "EUR"
    assert normalize_unit("£") == "GBP"
    assert normalize_unit("%") == "percent"
    assert normalize_unit("calendar days") == "calendar_days"
    assert normalize_unit("business days") == "business_days"
    assert normalize_unit("months") == "months"
    assert normalize_unit("sq ft") == "sq_ft"
    assert normalize_unit(None) is None
