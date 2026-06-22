"""
Server-Sent Events (SSE) Handler
================================

SSE endpoint for streaming responses over HTTP.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import Request
from fastapi.responses import StreamingResponse

from .streaming_engine import StreamEvent, StreamingEngine


class SSEHandler:
    """SSE handler for FastAPI."""

    def __init__(self, engine: StreamingEngine) -> None:
        self.engine = engine

    async def stream_response(
        self,
        request: Request,
        event_stream: AsyncIterator[StreamEvent],
    ) -> StreamingResponse:
        """Wrap an event stream as an SSE response."""

        async def event_generator():
            try:
                async for event in event_stream:
                    # check if client disconnected
                    if await request.is_disconnected():
                        break
                    yield event.to_sse()
            except asyncio.CancelledError:
                pass

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    def create_sse_endpoint(self, path: str, app):
        """Register an SSE endpoint."""
        engine = self.engine

        @app.get(path)
        async def sse_endpoint(request: Request):
            # Example: stream a token sequence
            async def token_gen():
                for word in ["Hello", " ", "world", "!"]:
                    yield word
                    await asyncio.sleep(0.1)

            async_iter = engine.stream_tokens(token_gen())
            return await self.stream_response(request, async_iter)

        return sse_endpoint
