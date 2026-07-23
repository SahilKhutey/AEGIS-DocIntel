"""
Access Tracker
==============

Tracks read/write access patterns for each memory item to inform
promotion and eviction decisions.

For each item v we track:
    - access_count    total number of accesses
    - last_access     timestamp of last access
    - first_access    timestamp of first access
    - write_count     total number of writes
    - access_history  recent access timestamps
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Dict, List, Optional


@dataclass
class AccessRecord:
    """
    Access statistics for a single memory item.

    Attributes
    ----------
    item_id : str
    access_count : int
    write_count : int
    last_access_time : float
    first_access_time : float
    access_history : List[float]
    """

    item_id: str
    access_count: int = 0
    write_count: int = 0
    last_access_time: float = field(default_factory=time)
    first_access_time: float = field(default_factory=time)
    access_history: List[float] = field(default_factory=list)

    def record_read(self, history_size: int = 50) -> None:
        """Record a read access."""
        now = time()
        self.access_count += 1
        self.last_access_time = now
        self.access_history.append(now)
        if len(self.access_history) > history_size:
            self.access_history = self.access_history[-history_size:]

    def record_write(self) -> None:
        """Record a write access."""
        self.write_count += 1
        self.last_access_time = time()

    @property
    def age_seconds(self) -> float:
        return time() - self.first_access_time

    @property
    def recency_seconds(self) -> float:
        return time() - self.last_access_time

    @property
    def frequency(self) -> float:
        """Accesses per second of lifetime."""
        lifetime = max(self.age_seconds, 1e-9)
        return self.access_count / lifetime

    @property
    def recent_frequency(self) -> float:
        """Accesses in last N records / time window."""
        if len(self.access_history) < 2:
            return 0.0
        window = self.access_history[-1] - self.access_history[0]
        if window < 1e-9:
            return float(self.access_count)
        return (len(self.access_history) - 1) / window


class AccessTracker:
    """
    Tracks access patterns across all memory items.
    """

    def __init__(self, history_size: int = 50) -> None:
        self.records: Dict[str, AccessRecord] = {}
        self.history_size = history_size

    def record_read(self, item_id: str) -> AccessRecord:
        """Record a read access."""
        if item_id not in self.records:
            self.records[item_id] = AccessRecord(item_id=item_id)
        rec = self.records[item_id]
        rec.record_read(history_size=self.history_size)
        return rec

    def record_write(self, item_id: str) -> AccessRecord:
        """Record a write access."""
        if item_id not in self.records:
            self.records[item_id] = AccessRecord(item_id=item_id)
        rec = self.records[item_id]
        rec.record_write()
        return rec

    def get(self, item_id: str) -> Optional[AccessRecord]:
        """Get access record for an item."""
        return self.records.get(item_id)

    def remove(self, item_id: str) -> None:
        """Remove tracking for an item."""
        if item_id in self.records:
            del self.records[item_id]

    def top_k_by_frequency(self, k: int) -> List[AccessRecord]:
        """Return top-k items by access frequency."""
        return sorted(
            self.records.values(),
            key=lambda r: r.frequency,
            reverse=True,
        )[:k]

    def top_k_by_recency(self, k: int) -> List[AccessRecord]:
        """Return top-k items by recency."""
        return sorted(
            self.records.values(),
            key=lambda r: r.last_access_time,
            reverse=True,
        )[:k]

    def cold_items(self, threshold_seconds: float) -> List[AccessRecord]:
        """Return items not accessed for `threshold_seconds`."""
        return [
            r for r in self.records.values()
            if r.recency_seconds > threshold_seconds
        ]
