"""
Storage Manager
===============

Stores memory items at each hierarchical level.
Supports multiple backends: in-memory, file-based (future: redis, postgres).
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .exceptions import CapacityExceededError, LevelNotFoundError
from .levels import DEFAULT_LEVEL_CONFIG, LevelMetadata, MemoryLevel


class StorageBackend(Enum):
    IN_MEMORY = "in_memory"
    FILE = "file"
    # Future: REDIS = "redis"
    # Future: POSTGRES = "postgres"


@dataclass
class StoredItem:
    """
    An item stored in memory.

    Attributes
    ----------
    item_id : str
    level : MemoryLevel
    data : Any
    size_bytes : int
    importance : float
    created_at : float
    """

    item_id: str
    level: MemoryLevel
    data: Any
    size_bytes: int
    importance: float = 0.5
    created_at: float = field(default_factory=lambda: __import__("time").time())


class StorageManager:
    """
    Manages storage across all hierarchical levels.
    """

    def __init__(
        self,
        backend: StorageBackend = StorageBackend.IN_MEMORY,
        base_path: Optional[Path] = None,
        level_config: Optional[Dict[MemoryLevel, LevelMetadata]] = None,
    ) -> None:
        self.backend = backend
        self.base_path = base_path
        self.level_config = level_config or DEFAULT_LEVEL_CONFIG
        # in-memory store: {level: {item_id: StoredItem}}
        self._stores: Dict[MemoryLevel, Dict[str, StoredItem]] = {
            level: {} for level in MemoryLevel
        }
        self._current_bytes: Dict[MemoryLevel, int] = {
            level: 0 for level in MemoryLevel
        }

    def store(
        self,
        item_id: str,
        level: MemoryLevel,
        data: Any,
        importance: float = 0.5,
        force: bool = False,
    ) -> StoredItem:
        """
        Store an item at a given level.

        Parameters
        ----------
        item_id : str
        level : MemoryLevel
        data : Any
        importance : float
        force : bool
            If True, overwrite even if item exists.
        """
        if level not in self.level_config:
            raise LevelNotFoundError(f"Unknown level: {level}")
        if not (0.0 <= importance <= 1.0):
            raise ValueError("importance must be in [0, 1].")

        # estimate size
        try:
            size = len(pickle.dumps(data))
        except Exception:
            size = 1024  # default estimate

        # check existing
        existing = self._stores[level].get(item_id)
        if existing is not None and not force:
            # update in place
            self._current_bytes[level] -= existing.size_bytes
            existing.data = data
            existing.size_bytes = size
            existing.importance = importance
            self._current_bytes[level] += size
            return existing

        # capacity check
        meta = self.level_config[level]
        current_count = len(self._stores[level])
        current_bytes = self._current_bytes[level]
        if (
            current_count >= meta.capacity_items
            or current_bytes + size > meta.capacity_bytes
        ) and not force:
            raise CapacityExceededError(
                f"Level {level.name_long} at capacity "
                f"({current_count}/{meta.capacity_items} items, "
                f"{current_bytes}/{meta.capacity_bytes} bytes)."
            )

        item = StoredItem(
            item_id=item_id,
            level=level,
            data=data,
            size_bytes=size,
            importance=importance,
        )
        self._stores[level][item_id] = item
        self._current_bytes[level] += size
        return item

    def get(self, item_id: str, level: MemoryLevel) -> Optional[StoredItem]:
        """Retrieve an item from a specific level."""
        return self._stores[level].get(item_id)

    def exists(self, item_id: str, level: MemoryLevel) -> bool:
        return item_id in self._stores[level]

    def remove(self, item_id: str, level: MemoryLevel) -> bool:
        """Remove an item from a level."""
        item = self._stores[level].pop(item_id, None)
        if item is not None:
            self._current_bytes[level] -= item.size_bytes
            return True
        return False

    def move(self, item_id: str, from_level: MemoryLevel, to_level: MemoryLevel) -> bool:
        """Move an item between levels."""
        item = self.get(item_id, from_level)
        if item is None:
            return False
        # remove from source
        self._stores[from_level].pop(item_id)
        self._current_bytes[from_level] -= item.size_bytes
        # add to target
        new_item = StoredItem(
            item_id=item.item_id,
            level=to_level,
            data=item.data,
            size_bytes=item.size_bytes,
            importance=item.importance,
            created_at=item.created_at,
        )
        self._stores[to_level][item_id] = new_item
        self._current_bytes[to_level] += item.size_bytes
        return True

    def items_at_level(self, level: MemoryLevel) -> List[StoredItem]:
        """Return all items at a level."""
        return list(self._stores[level].values())

    def item_count(self, level: MemoryLevel) -> int:
        return len(self._stores[level])

    def size_bytes(self, level: MemoryLevel) -> int:
        return self._current_bytes[level]

    def capacity(self, level: MemoryLevel) -> LevelMetadata:
        return self.level_config[level]

    def clear_level(self, level: MemoryLevel) -> None:
        """Remove all items from a level."""
        self._stores[level].clear()
        self._current_bytes[level] = 0

    def clear_all(self) -> None:
        for level in MemoryLevel:
            self.clear_level(level)
