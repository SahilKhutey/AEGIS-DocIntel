"""
Tests for Hierarchical Memory L0-L5 maintenance passes, promotion, and eviction.
"""
from __future__ import annotations

import pytest

from src.engines.memory.hierarchical_memory import HierarchicalMemory, MemoryLevel
from src.engines.memory.levels import LevelMetadata


def test_hierarchical_memory_run_maintenance_pass_promotion_and_eviction():
    # Setup custom level configs with small capacities for testing eviction
    level_config = {
        lvl: LevelMetadata(
            level=lvl,
            capacity_items=2,  # Max 2 items per level
            capacity_bytes=1024 * 1024,
        )
        for lvl in MemoryLevel
    }

    mem = HierarchicalMemory(level_config=level_config)

    # Store 3 items in L5_SUMMARIES using force=True to create capacity overflow (capacity = 2)
    mem.store("summary_1", MemoryLevel.L5_SUMMARIES, "Summary 1 data", importance=0.1, force=True)
    mem.store("summary_2", MemoryLevel.L5_SUMMARIES, "Summary 2 data", importance=0.5, force=True)
    mem.store("summary_3", MemoryLevel.L5_SUMMARIES, "Summary 3 data", importance=0.9, force=True)

    # Record multiple reads for summary_1 to trigger promotion threshold
    for _ in range(5):
        mem.tracker.record_read("summary_1")

    # Run automated maintenance pass
    res = mem.run_maintenance_pass()

    assert "promotions" in res
    assert "evictions" in res
    assert res["evicted_count"] >= 1 or res["promoted_count"] >= 1
