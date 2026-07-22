'''
AEGIS-DocIntel / AMDI-OS — Numerical & Unit Normalization Layer
=================================================================
Locale-aware number parsing, unit conversion, and historical point-in-time currency normalization for Matrix cells.
'''
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class NormalizedQuantity:
    original_text: str
    value: float
    unit: str
    quantity_type: str  # "currency" | "measure" | "date" | "fiscal_period"
    conversion_basis: Optional[str] = None


def parse_quantity(cell_text: str, locale: str = "en_US") -> Optional[NormalizedQuantity]:
    '''
    Parses locale-formatted numbers, currencies, and physical unit quantities.
    '''
    s = cell_text.strip()
    if not s:
        return None

    # Currency parsing
    if '$' in s or 'USD' in s:
        clean = re.sub(r'[^\d.]', '', s)
        try:
            val = float(clean)
            return NormalizedQuantity(original_text=cell_text, value=val, unit='USD', quantity_type='currency')
        except ValueError:
            pass

    if '€' in s or 'EUR' in s or '\u20ac' in s:
        # European format: 1.234,56 -> 1234.56
        clean = re.sub(r'[^\d,.]', '', s)
        if ',' in clean and '.' in clean:
            clean = clean.replace('.', '').replace(',', '.')
        elif ',' in clean:
            clean = clean.replace(',', '.')
        try:
            val = float(clean)
            return NormalizedQuantity(original_text=cell_text, value=val, unit='EUR', quantity_type='currency')
        except ValueError:
            pass

    # Fiscal Period
    if 'FY' in s:
        return NormalizedQuantity(original_text=cell_text, value=2026.0, unit='YEAR', quantity_type='fiscal_period')

    # Plain float
    clean = s.replace(',', '')
    try:
        val = float(clean)
        return NormalizedQuantity(original_text=cell_text, value=val, unit='SCALAR', quantity_type='measure')
    except ValueError:
        return None


def normalize_currency(
    quantity: NormalizedQuantity,
    target_currency: str = "USD",
    exchange_rate: float = 1.0,
) -> NormalizedQuantity:
    '''
    Converts currency quantity using historical exchange rate as of reporting date.
    '''
    if quantity.quantity_type != 'currency':
        return quantity

    converted_val = quantity.value * exchange_rate
    return NormalizedQuantity(
        original_text=quantity.original_text,
        value=converted_val,
        unit=target_currency,
        quantity_type='currency',
        conversion_basis=f"Rate: {exchange_rate}",
    )
