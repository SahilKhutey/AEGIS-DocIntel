"""
Stream Buffer
==============

Buffers streaming tokens with configurable flush strategies.
"""

from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import AsyncIterator, List, Optional


class FlushStrategy(Enum):
    """When to flush the buffer."""

    ON_TOKEN = "on_token"          # flush each token
    ON_SPACE = "on_space"          # flush on space character
    ON_SIZE = "on_size"            # flush when buffer reaches size
    ON_TIME = "on_time"            # flush after timeout


class StreamBuffer:
    """
    Buffers tokens for efficient streaming.

    Reduces network overhead by batching small tokens.
    """

    def __init__(
        self,
        strategy: FlushStrategy = FlushStrategy.ON_SPACE,
        max_size: int = 50,
        max_interval_ms: float = 50.0,
    ) -> None:
        self.strategy = strategy
        self.max_size = max_size
        self.max_interval_ms = max_interval_ms
        self.buffer: List[str] = []
        self.last_flush = time.time()

    def add(self, token: str) -> Optional[str]:
        """Add a token; return flushed chunk if ready."""
        self.buffer.append(token)
        should_flush = False
        if self.strategy == FlushStrategy.ON_TOKEN:
            should_flush = True
        elif self.strategy == FlushStrategy.ON_SPACE:
            if " " in token or "\n" in token:
                should_flush = True
        elif self.strategy == FlushStrategy.ON_SIZE:
            if sum(len(t) for t in self.buffer) >= self.max_size:
                should_flush = True
        elif self.strategy == FlushStrategy.ON_TIME:
            elapsed_ms = (time.time() - self.last_flush) * 1000
            if elapsed_ms >= self.max_interval_ms:
                should_flush = True
        if should_flush:
            return self.flush()
        return None

    def flush(self) -> str:
        """Flush the buffer and return the chunk."""
        chunk = "".join(self.buffer)
        self.buffer = []
        self.last_flush = time.time()
        return chunk

    async def stream(
        self, token_source: AsyncIterator[str]
    ) -> AsyncIterator[str]:
        """Stream with buffering."""
        async for token in token_source:
            chunk = self.add(token)
            if chunk is not None:
                yield chunk
        # flush remaining
        remaining = self.flush()
        if remaining:
            yield remaining
