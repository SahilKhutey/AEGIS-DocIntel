"""
aegis-docprep — Pre-LLM Document Structuring Primitives
======================================================
Focused, installable toolkit containing the three most validated primitives
from AEGIS-DocIntel:
1. PII Redaction & Compliance Filter (regex + Luhn mod-10 + TitleCase name detection)
2. Submodular Knapsack Context Packing (provably bound greedy selection maximizing relevance & diversity)
3. Spatial Reading-Order Extraction (deterministic topological DAG reconstruction via Kahn's algorithm)
"""

from __future__ import annotations

from aegis_docprep.pii_redaction import (
    ComplianceReport,
    PIIEntity,
    RedactionPolicy,
    apply_redaction_policy,
    detect_pii,
    redact_elements,
)
from aegis_docprep.context_packer import (
    ContextChunk,
    SubmodularKnapsackPacker,
    SubmodularPackingResult,
)
from aegis_docprep.reading_order import (
    ReadingGraphConfig,
    SpatialReadingGraph,
    compute_opw_distance,
    flag_fragile_edges,
    is_reading_forward_successor,
    ollivier_ricci_curvature,
    order_preserving_wasserstein_distance,
)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # PII Redaction
    "detect_pii",
    "apply_redaction_policy",
    "redact_elements",
    "PIIEntity",
    "RedactionPolicy",
    "ComplianceReport",
    # Context Packing
    "SubmodularKnapsackPacker",
    "ContextChunk",
    "SubmodularPackingResult",
    # Reading Order
    "SpatialReadingGraph",
    "ReadingGraphConfig",
    "is_reading_forward_successor",
    "compute_opw_distance",
    "order_preserving_wasserstein_distance",
    "ollivier_ricci_curvature",
    "flag_fragile_edges",
]
