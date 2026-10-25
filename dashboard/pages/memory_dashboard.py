"""
Memory Dashboard
=================

Visualizes the L0-L5 hierarchical memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np

try:
    from backend.src.memory import MemoryEngine, MemoryLevel, MemoryStats
except ImportError:
    try:
        from src.engines.memory import MemoryEngine, MemoryLevel, MemoryStats
    except ImportError:
        from engines.memory import MemoryEngine, MemoryLevel, MemoryStats


@dataclass
class LevelView:
    """Per-level visualization data."""

    level: str
    level_name: str
    item_count: int
    size_bytes: int
    capacity_items: int
    capacity_bytes: int
    utilization: float
    promotion_count: int = 0
    eviction_count: int = 0

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "level_name": self.level_name,
            "item_count": self.item_count,
            "size_bytes": self.size_bytes,
            "capacity_items": self.capacity_items,
            "capacity_bytes": self.capacity_bytes,
            "utilization": round(self.utilization, 4),
            "promotion_count": self.promotion_count,
            "eviction_count": self.eviction_count,
        }


@dataclass
class MemoryViewData:
    """Memory dashboard view."""

    levels: List[LevelView] = field(default_factory=list)
    total_items: int = 0
    total_bytes: int = 0
    cache_size: int = 0
    total_accesses: int = 0
    cache_hit_rate: float = 0.0

    def to_dict(self) -> dict:
        return {
            "levels": [lv.to_dict() for lv in self.levels],
            "total_items": self.total_items,
            "total_bytes": self.total_bytes,
            "cache_size": self.cache_size,
            "total_accesses": self.total_accesses,
            "cache_hit_rate": round(self.cache_hit_rate, 4),
        }


class MemoryDashboard:
    """Memory dashboard backend API."""

    def __init__(self, engine: MemoryEngine) -> None:
        self.engine = engine

    def get_view(self) -> MemoryViewData:
        stats = self.engine.stats()
        view = MemoryViewData(
            total_items=stats.total_items,
            total_bytes=stats.total_bytes,
            cache_size=stats.cache_size,
            total_accesses=stats.total_accesses,
        )
        for level in MemoryLevel:
            items = stats.items_per_level.get(level, 0)
            size = stats.bytes_per_level.get(level, 0)
            cap_items = stats.capacity_per_level.get(level, 1)
            cap_bytes = self.engine.memory.storage.capacity(level).capacity_bytes
            util = items / cap_items if cap_items > 0 else 0.0
            view.levels.append(
                LevelView(
                    level=str(level.value),
                    level_name=level.name_long,
                    item_count=items,
                    size_bytes=size,
                    capacity_items=cap_items,
                    capacity_bytes=cap_bytes,
                    utilization=util,
                )
            )
        return view

    def get_heatmap_data(self) -> Dict[str, List[float]]:
        """Data for memory access heatmap."""
        return {
            "levels": [lv.level_name for lv in self.get_view().levels],
            "utilization": [lv.utilization for lv in self.get_view().levels],
        }
