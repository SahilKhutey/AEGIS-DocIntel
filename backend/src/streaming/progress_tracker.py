"""
Progress Tracker
==================

Track and report progress of long-running operations.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ProgressEvent:
    """A progress update event."""

    operation: str
    current: int
    total: int
    percent: float
    message: str = ""
    elapsed_seconds: float = 0.0
    estimated_remaining_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "current": self.current,
            "total": self.total,
            "percent": self.percent,
            "message": self.message,
            "elapsed_seconds": self.elapsed_seconds,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
            "timestamp": self.timestamp,
        }


class ProgressTracker:
    """
    Track progress of operations.

    Can be used as a context manager or async iterator.
    """

    def __init__(self, operation: str, total: int, message: str = "") -> None:
        self.operation = operation
        self.total = total
        self.message = message
        self.current = 0
        self.start_time = time.time()
        self._callbacks: List[Callable[[ProgressEvent], None]] = []
        self._async_callbacks: List[Callable] = []

    def on_progress(self, callback: Callable[[ProgressEvent], None]) -> None:
        """Register a progress callback."""
        self._callbacks.append(callback)

    async def on_progress_async(self, callback: Callable) -> None:
        """Register an async progress callback."""
        self._async_callbacks.append(callback)

    def update(self, current: int, message: str = "") -> ProgressEvent:
        """Update progress to current/total."""
        self.current = min(current, self.total)
        self.message = message or self.message
        elapsed = time.time() - self.start_time
        rate = self.current / max(elapsed, 1e-6)
        remaining = (self.total - self.current) / max(rate, 1e-6)
        event = ProgressEvent(
            operation=self.operation,
            current=self.current,
            total=self.total,
            percent=self.current / max(self.total, 1) * 100,
            message=self.message,
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=remaining,
        )
        for cb in self._callbacks:
            cb(event)
        return event

    def finish(self, message: str = "Completed") -> ProgressEvent:
        """Mark as finished."""
        return self.update(self.total, message=message)

    @property
    def percent(self) -> float:
        return self.current / max(self.total, 1) * 100

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.finish()
