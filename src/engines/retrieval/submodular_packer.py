"""
Submodular Knapsack Context Packer (Task C-1).
==============================================
Synchronized with aegis_docprep.context_packer.
"""
from __future__ import annotations

from aegis_docprep.context_packer import (
    ContextChunk,
    SubmodularKnapsackPacker,
    SubmodularPackingResult,
    calculate_available_context_budget,
    validate_packing_inputs,
)

__all__ = [
    "ContextChunk",
    "SubmodularKnapsackPacker",
    "SubmodularPackingResult",
    "calculate_available_context_budget",
    "validate_packing_inputs",
]
