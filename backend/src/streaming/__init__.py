"""
AMDI-OS Streaming Support
===========================

Server-Sent Events (SSE) + WebSocket streaming for real-time responses.

Capabilities:
    - Token-by-token streaming
    - Progress reporting for long operations
    - Server-Sent Events (SSE)
    - WebSocket streaming
    - Backpressure handling

Author : AMDI-OS Development Team
Version: 1.2.0
"""

from .streaming_engine import StreamingEngine, StreamEvent, StreamEventType
from .sse_handler import SSEHandler
from .websocket_handler import WebSocketHandler
from .progress_tracker import ProgressTracker, ProgressEvent
from .stream_buffer import StreamBuffer

__all__ = [
    "StreamingEngine",
    "StreamEvent",
    "StreamEventType",
    "SSEHandler",
    "WebSocketHandler",
    "ProgressTracker",
    "ProgressEvent",
    "StreamBuffer",
]

__version__ = "1.2.0"
