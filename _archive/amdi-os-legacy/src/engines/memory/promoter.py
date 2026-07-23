"""
Promoter
========

Moves memory items UP the hierarchy (L0 → L1 → ... → L5)
based on access frequency and importance.

Mathematical Foundation:
-----------------------
Promotion score:
    P(v) = α · frequency(v) + β · importance(v) + γ · recency(v)

Promotion rule:
    if P(v) ≥ θ_p(level)  →  promote(v, level, level+1)

Promotion threshold per level:
    θ_p(L0) = 0.3
    θ_p(L1) = 0.5
    θ_p(L2) = 0.6
    θ_p(L3) = 0.7
    θ_p(L4) = 0.8
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .access_tracker import AccessTracker
from .levels import MemoryLevel
from .store import StorageManager


class PromotionPolicy(Enum):
    FREQUENCY = "frequency"
    IMPORTANCE = "importance"
    HYBRID = "hybrid"


@dataclass
class PromotionDecision:
    """Result of a single promotion decision."""

    item_id: str
    from_level: MemoryLevel
    to_level: MemoryLevel
    score: float
    reason: str


class Promoter:
    """
    Decides which items to promote up the hierarchy.
    """

    DEFAULT_THRESHOLDS = {
        MemoryLevel.L0_RAW: 0.3,
        MemoryLevel.L1_TEMPLATES: 0.5,
        MemoryLevel.L2_STRUCTURES: 0.6,
        MemoryLevel.L3_TABLES: 0.7,
        MemoryLevel.L4_SEMANTIC: 0.8,
    }

    def __init__(
        self,
        policy: PromotionPolicy = PromotionPolicy.HYBRID,
        thresholds: Optional[Dict[MemoryLevel, float]] = None,
        frequency_weight: float = 0.4,
        importance_weight: float = 0.4,
        recency_weight: float = 0.2,
    ) -> None:
        self.policy = policy
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS
        s = frequency_weight + importance_weight + recency_weight
        self.frequency_weight = frequency_weight / s
        self.importance_weight = importance_weight / s
        self.recency_weight = recency_weight / s

    def compute_score(
        self,
        frequency: float,
        importance: float,
        recency: float,
    ) -> float:
        """Compute promotion score."""
        return (
            self.frequency_weight * frequency
            + self.importance_weight * importance
            + self.recency_weight * recency
        )

    def should_promote(
        self,
        item_id: str,
        level: MemoryLevel,
        storage: StorageManager,
        tracker: AccessTracker,
    ) -> Optional[PromotionDecision]:
        """
        Decide if an item should be promoted.

        Returns PromotionDecision or None.
        """
        if level == MemoryLevel.L5_SUMMARIES:
            return None  # already at top

        item = storage.get(item_id, level)
        if item is None:
            return None

        rec = tracker.get(item_id)
        frequency = rec.frequency if rec else 0.0
        # recency: 1 / (1 + seconds_since_access)
        if rec is not None:
            recency = 1.0 / (1.0 + rec.recency_seconds)
        else:
            recency = 0.0
        importance = item.importance

        score = self.compute_score(frequency, importance, recency)
        threshold = self.thresholds.get(level, 0.5)

        if score >= threshold:
            next_level = MemoryLevel(level.value + 1)
            return PromotionDecision(
                item_id=item_id,
                from_level=level,
                to_level=next_level,
                score=score,
                reason=f"score={score:.3f} ≥ threshold={threshold:.3f}",
            )
        return None

    def promote_batch(
        self,
        level: MemoryLevel,
        storage: StorageManager,
        tracker: AccessTracker,
        max_promotions: int = 100,
    ) -> List[PromotionDecision]:
        """Promote up to `max_promotions` items from `level` upward."""
        decisions: List[PromotionDecision] = []
        for item in storage.items_at_level(level):
            if len(decisions) >= max_promotions:
                break
            decision = self.should_promote(item.item_id, level, storage, tracker)
            if decision is not None:
                if storage.move(decision.item_id, level, decision.to_level):
                    decisions.append(decision)
        return decisions
