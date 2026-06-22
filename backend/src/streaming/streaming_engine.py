"""
Streaming Engine
=================

Core streaming primitives.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional


class StreamEventType(Enum):
    """Types of stream events."""

    START = "start"
    PROGRESS = "progress"
    TOKEN = "token"
    DATA = "data"
    DONE = "done"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


@dataclass
class StreamEvent:
    """A single event in a stream."""

    event_id: str
    event_type: StreamEventType
    timestamp: float
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
        }

    def to_sse(self) -> str:
        """Format as Server-Sent Event."""
        lines = [
            f"id: {self.event_id}",
            f"event: {self.event_type.value}",
            f"data: {json.dumps(self.to_dict())}",
        ]
        return "\n".join(lines) + "\n\n"


class StreamingEngine:
    """
    Engine for streaming responses.
    """

    def __init__(self, heartbeat_interval: float = 15.0) -> None:
        self.heartbeat_interval = heartbeat_interval
        self._streams: Dict[str, Dict[str, Any]] = {}

    def create_stream(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new stream and return its ID."""
        stream_id = str(uuid.uuid4())
        self._streams[stream_id] = {
            "created_at": time.time(),
            "metadata": metadata or {},
            "events": [],
            "status": "active",
        }
        return stream_id

    async def stream_tokens(
        self,
        token_generator: AsyncIterator[str],
        stream_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream tokens from an async generator."""
        if stream_id is None:
            stream_id = self.create_stream(metadata)
        # start event
        yield StreamEvent(
            event_id=f"{stream_id}_0",
            event_type=StreamEventType.START,
            timestamp=time.time(),
            data={"stream_id": stream_id},
            metadata=metadata or {},
        )
        last_heartbeat = time.time()
        i = 1
        try:
            async for token in token_generator:
                yield StreamEvent(
                    event_id=f"{stream_id}_{i}",
                    event_type=StreamEventType.TOKEN,
                    timestamp=time.time(),
                    data={"token": token},
                )
                i += 1
                # heartbeat if no token for a while
                if time.time() - last_heartbeat > self.heartbeat_interval:
                    yield StreamEvent(
                        event_id=f"{stream_id}_heartbeat_{i}",
                        event_type=StreamEventType.HEARTBEAT,
                        timestamp=time.time(),
                        data={"status": "alive"},
                    )
                    last_heartbeat = time.time()
            # done event
            yield StreamEvent(
                event_id=f"{stream_id}_done",
                event_type=StreamEventType.DONE,
                timestamp=time.time(),
                data={"total_tokens": i - 1},
            )
            if stream_id in self._streams:
                self._streams[stream_id]["status"] = "completed"
        except Exception as exc:
            yield StreamEvent(
                event_id=f"{stream_id}_error",
                event_type=StreamEventType.ERROR,
                timestamp=time.time(),
                data={"error": str(exc)},
            )
            if stream_id in self._streams:
                self._streams[stream_id]["status"] = "error"

    async def stream_progress(
        self,
        operations: List[Callable],
        stream_id: Optional[str] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream progress of multiple operations."""
        if stream_id is None:
            stream_id = self.create_stream()
        yield StreamEvent(
            event_id=f"{stream_id}_start",
            event_type=StreamEventType.START,
            timestamp=time.time(),
            data={"total": len(operations)},
        )
        results: List[Any] = []
        for i, op in enumerate(operations):
            try:
                if asyncio.iscoroutinefunction(op):
                    result = await op()
                else:
                    result = op()
                results.append(result)
            except Exception as exc:
                results.append({"error": str(exc)})
            yield StreamEvent(
                event_id=f"{stream_id}_{i}",
                event_type=StreamEventType.PROGRESS,
                timestamp=time.time(),
                data={
                    "completed": i + 1,
                    "total": len(operations),
                    "percent": (i + 1) / len(operations) * 100,
                },
            )
        yield StreamEvent(
            event_id=f"{stream_id}_done",
            event_type=StreamEventType.DONE,
            timestamp=time.time(),
            data={"results": results},
        )

    def get_stream_status(self, stream_id: str) -> Optional[Dict[str, Any]]:
        return self._streams.get(stream_id)
