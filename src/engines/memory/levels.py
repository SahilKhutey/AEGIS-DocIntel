"""
Memory Levels
=============

Defines the six hierarchical levels of the AMDI-OS memory system:

    L0 Raw        — original content (bytes / strings / arrays)
    L1 Templates  — extracted templates & fingerprints
    L2 Structures — graph / topological / tensor structures
    L3 Tables     — matrix / tabular representations
    L4 Semantic   — embeddings & semantic vectors
    L5 Summaries  — compressed summaries

Each level has:
    - capacity     (max items or bytes)
    - access_speed (relative; L5 fastest in cache, L0 slowest on disk)
    - priority     (higher level = higher priority)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from .exceptions import LevelNotFoundError


class MemoryLevel(Enum):
    """The six hierarchical memory levels."""

    L0_RAW = 0
    L1_TEMPLATES = 1
    L2_STRUCTURES = 2
    L3_TABLES = 3
    L4_SEMANTIC = 4
    L5_SUMMARIES = 5

    @property
    def priority(self) -> int:
        """Higher level → higher priority."""
        return self.value

    @property
    def name_long(self) -> str:
        return {
            0: "raw",
            1: "templates",
            2: "structures",
            3: "tables",
            4: "semantic",
            5: "summaries",
        }[self.value]


@dataclass
class LevelMetadata:
    """
    Metadata for a single memory level.

    Attributes
    ----------
    level : MemoryLevel
    capacity_items : int
        Maximum number of items stored.
    capacity_bytes : int
        Maximum total size in bytes.
    access_speed : float
        Relative speed (higher = faster).
    """

    level: MemoryLevel
    capacity_items: int = 10000
    capacity_bytes: int = 100 * 1024 * 1024  # 100 MB
    access_speed: float = 1.0
    description: str = ""

    def __post_init__(self) -> None:
        # Set default speeds based on level
        speeds = {
            0: 0.1,   # L0 raw — disk-backed
            1: 0.3,
            2: 0.5,
            3: 0.7,
            4: 1.5,
            5: 2.0,   # L5 summaries — fastest cached
        }
        if self.access_speed == 1.0:  # default was not changed
            self.access_speed = speeds[self.level.value]


# Default level configurations
DEFAULT_LEVEL_CONFIG: Dict[MemoryLevel, LevelMetadata] = {
    MemoryLevel.L0_RAW: LevelMetadata(
        level=MemoryLevel.L0_RAW,
        capacity_items=50000,
        capacity_bytes=1024 * 1024 * 1024,  # 1 GB
        description="Raw document content",
    ),
    MemoryLevel.L1_TEMPLATES: LevelMetadata(
        level=MemoryLevel.L1_TEMPLATES,
        capacity_items=20000,
        capacity_bytes=200 * 1024 * 1024,
        description="Templates and fingerprints",
    ),
    MemoryLevel.L2_STRUCTURES: LevelMetadata(
        level=MemoryLevel.L2_STRUCTURES,
        capacity_items=15000,
        capacity_bytes=300 * 1024 * 1024,
        description="Graph / topology / tensor structures",
    ),
    MemoryLevel.L3_TABLES: LevelMetadata(
        level=MemoryLevel.L3_TABLES,
        capacity_items=10000,
        capacity_bytes=200 * 1024 * 1024,
        description="Tabular and matrix representations",
    ),
    MemoryLevel.L4_SEMANTIC: LevelMetadata(
        level=MemoryLevel.L4_SEMANTIC,
        capacity_items=20000,
        capacity_bytes=400 * 1024 * 1024,
        description="Semantic embeddings",
    ),
    MemoryLevel.L5_SUMMARIES: LevelMetadata(
        level=MemoryLevel.L5_SUMMARIES,
        capacity_items=5000,
        capacity_bytes=100 * 1024 * 1024,
        description="Compressed summaries",
    ),
}


def get_level_metadata(level: MemoryLevel) -> LevelMetadata:
    """Get default metadata for a level."""
    if level not in DEFAULT_LEVEL_CONFIG:
        raise LevelNotFoundError(f"Unknown level: {level}")
    return DEFAULT_LEVEL_CONFIG[level]
