"""
AMDI-OS Python SDK Utilities.
"""

from typing import Any, Dict


def validate_budget(budget: int) -> bool:
    """Validate token budget."""
    if budget <= 0:
        raise ValueError("Token budget must be a positive integer")
    return True


def format_ueo_summary(ueo_dict: Dict[str, Any]) -> str:
    """Format a simple user-friendly summary of a UEO."""
    tokens = ueo_dict.get("total_tokens", 0)
    citations_count = len(ueo_dict.get("citations", []))
    confidence = ueo_dict.get("confidence", 0.0)
    return f"UEO (Tokens: {tokens}, Citations: {citations_count}, Confidence: {confidence:.2f})"
