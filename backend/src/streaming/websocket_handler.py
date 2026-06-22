"""
WebSocket Handler
===================

WebSocket endpoint for bidirectional real-time streaming.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect

from .streaming_engine import StreamEvent, StreamEventType, StreamingEngine


class WebSocketHandler:
    """WebSocket handler for AMDI-OS streaming."""

    def __init__(self, engine: StreamingEngine) -> None:
        self.engine = engine
        self.active_connections: Dict[str, WebSocket] = {}

    async def handle_connection(
        self,
        websocket: WebSocket,
        client_id: str,
    ) -> None:
        """Handle a WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        try:
            while True:
                # receive messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                # handle different message types
                msg_type = message.get("type")
                if msg_type == "subscribe":
                    stream_id = message.get("stream_id")
                    await self._handle_subscribe(websocket, stream_id)
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "query":
                    query = message.get("query")
                    ueo = message.get("ueo")
                    await self._handle_query(websocket, client_id, query, ueo)
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}",
                    })
        except WebSocketDisconnect:
            pass
        finally:
            self.active_connections.pop(client_id, None)

    async def _handle_subscribe(
        self, websocket: WebSocket, stream_id: Optional[str]
    ) -> None:
        """Subscribe to a stream."""
        # In production: subscribe to stream updates
        await websocket.send_json({
            "type": "subscribed",
            "stream_id": stream_id,
        })

    async def _handle_query(
        self,
        websocket: WebSocket,
        client_id: str,
        query: str,
        ueo: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handle a streaming query."""
        stream_id = self.engine.create_stream({"query": query, "client_id": client_id})
        # start event
        await self._send_event(websocket, StreamEvent(
            event_id=f"{stream_id}_start",
            event_type=StreamEventType.START,
            timestamp=0,
            data={"stream_id": stream_id, "query": query},
        ))
        # stream progress
        for i in range(1, 6):
            await self._send_event(websocket, StreamEvent(
                event_id=f"{stream_id}_{i}",
                event_type=StreamEventType.PROGRESS,
                timestamp=0,
                data={"step": i, "total_steps": 5},
            ))
            await asyncio.sleep(0.5)
        # done
        await self._send_event(websocket, StreamEvent(
            event_id=f"{stream_id}_done",
            event_type=StreamEventType.DONE,
            timestamp=0,
            data={"answer": f"Processed query: {query}"},
        ))

    async def _send_event(self, websocket: WebSocket, event: StreamEvent) -> None:
        """Send an event to a WebSocket."""
        try:
            await websocket.send_json(event.to_dict())
        except Exception:
            pass

    def broadcast(self, event: StreamEvent) -> None:
        """Broadcast an event to all connected clients."""
        for ws in self.active_connections.values():
            asyncio.create_task(self._send_event(ws, event))
