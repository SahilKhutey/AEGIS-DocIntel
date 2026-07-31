"""
Query-Adaptive Token-Budget Sizing Engine (Task H-5).

Dynamically adjusts context token budgets based on query complexity classification.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, Optional


class QueryType(Enum):
    FACTOID = "factoid"
    MULTIHOP = "multihop"
    ANALYTICAL = "analytical"
    SUMMARIZATION = "summarization"


class QueryAdaptiveBudgetSizer:
    """
    Classifies queries and dynamically calculates adaptive context token budgets.
    """

    DEFAULT_BUDGETS: Dict[QueryType, int] = {
        QueryType.FACTOID: 512,
        QueryType.MULTIHOP: 2048,
        QueryType.ANALYTICAL: 3072,
        QueryType.SUMMARIZATION: 4096,
    }

    def __init__(self, custom_budgets: Optional[Dict[QueryType, int]] = None):
        self.budgets = dict(self.DEFAULT_BUDGETS)
        if custom_budgets:
            self.budgets.update(custom_budgets)

    def classify_query(self, query: str) -> QueryType:
        """Classify query intent based on linguistic patterns and complexity signals."""
        q_lower = query.lower().strip()

        # Summarization indicators
        if any(w in q_lower for w in ["summarize", "summary", "overview", "executive summary", "key takeaways"]):
            return QueryType.SUMMARIZATION

        # Analytical / Synthesis indicators
        if any(w in q_lower for w in ["compare", "contrast", "relationship", "difference", "impact of", "trend"]):
            return QueryType.ANALYTICAL

        # Multi-hop reasoning indicators
        if any(w in q_lower for w in ["why", "how does", "what led to", "explain the cause", "steps to"]):
            return QueryType.MULTIHOP

        # Factoid (default for specific what/when/where/who lookup)
        return QueryType.FACTOID

    def compute_budget(
        self,
        query: str,
        base_budget: Optional[int] = None,
        max_cap: int = 8192,
    ) -> int:
        """
        Computes context budget for a given query.
        If base_budget is provided, scales base_budget according to query complexity multiplier.
        """
        q_type = self.classify_query(query)
        recommended = self.budgets[q_type]

        if base_budget is not None and base_budget > 0:
            multiplier_map = {
                QueryType.FACTOID: 0.5,
                QueryType.MULTIHOP: 1.0,
                QueryType.ANALYTICAL: 1.5,
                QueryType.SUMMARIZATION: 2.0,
            }
            computed = int(base_budget * multiplier_map[q_type])
            return min(max(computed, 256), max_cap)

        return min(recommended, max_cap)
