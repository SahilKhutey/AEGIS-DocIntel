import asyncio
import os
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest

# Configure Python path to find backend packages
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.src.streaming import (
    StreamingEngine,
    StreamEvent,
    StreamEventType,
    SSEHandler,
    WebSocketHandler,
    ProgressTracker,
    ProgressEvent,
    StreamBuffer,
)
from backend.src.streaming.stream_buffer import FlushStrategy


@pytest.mark.asyncio
async def test_stream_event_formatting():
    event = StreamEvent(
        event_id="test_1",
        event_type=StreamEventType.TOKEN,
        timestamp=time.time(),
        data={"token": "hello"},
        metadata={"session": "xyz"}
    )
    
    # Verify dict conversion
    d = event.to_dict()
    assert d["event_id"] == "test_1"
    assert d["event_type"] == "token"
    assert d["data"] == {"token": "hello"}
    
    # Verify SSE lines format
    sse = event.to_sse()
    assert "id: test_1" in sse
    assert "event: token" in sse
    assert "data: " in sse
    assert sse.endswith("\n\n")


@pytest.mark.asyncio
async def test_streaming_engine_tokens():
    engine = StreamingEngine(heartbeat_interval=0.1)

    async def dummy_token_generator():
        yield "Hello"
        await asyncio.sleep(0.05)
        yield "World"

    events = []
    async for event in engine.stream_tokens(dummy_token_generator(), metadata={"test": "run"}):
        events.append(event)

    # We expect: 1 START event, 2 TOKEN events, 1 DONE event
    assert len(events) >= 4
    assert events[0].event_type == StreamEventType.START
    assert events[1].event_type == StreamEventType.TOKEN
    assert events[1].data["token"] == "Hello"
    assert events[-1].event_type == StreamEventType.DONE
    assert events[-1].data["total_tokens"] == 2


@pytest.mark.asyncio
async def test_streaming_engine_progress():
    engine = StreamingEngine()

    async def op1():
        return "step1"

    def op2():
        return "step2"

    events = []
    async for event in engine.stream_progress([op1, op2]):
        events.append(event)

    assert len(events) == 4  # START, 2 PROGRESS updates, DONE
    assert events[0].event_type == StreamEventType.START
    assert events[1].event_type == StreamEventType.PROGRESS
    assert events[1].data["percent"] == 50.0
    assert events[2].data["percent"] == 100.0
    assert events[-1].event_type == StreamEventType.DONE
    assert events[-1].data["results"] == ["step1", "step2"]


@pytest.mark.asyncio
async def test_sse_handler_response():
    engine = StreamingEngine()
    handler = SSEHandler(engine)

    # Mock fastapi request
    mock_request = MagicMock()
    mock_request.is_disconnected = AsyncMock(return_value=False)

    async def dummy_events():
        yield StreamEvent(
            event_id="e1",
            event_type=StreamEventType.TOKEN,
            timestamp=time.time(),
            data={"token": "t"}
        )

    response = await handler.stream_response(mock_request, dummy_events())
    assert response.media_type == "text/event-stream"
    assert response.headers["Cache-Control"] == "no-cache"


@pytest.mark.asyncio
async def test_websocket_handler():
    engine = StreamingEngine()
    handler = WebSocketHandler(engine)

    # Mock WebSocket connection
    mock_ws = AsyncMock()
    
    # Mock receive/send operations
    from fastapi import WebSocketDisconnect
    mock_ws.receive_text.side_effect = [
        '{"type": "ping"}',
        '{"type": "subscribe", "stream_id": "s1"}',
        WebSocketDisconnect(code=1000)  # exit loop
    ]

    await handler.handle_connection(mock_ws, "client_1")
    
    # Assert websocket accepted connection
    mock_ws.accept.assert_called_once()
    # Assert pong and subscribed response JSONs were sent
    calls = mock_ws.send_json.call_args_list
    assert {"type": "pong"} in [c[0][0] for c in calls]
    assert {"type": "subscribed", "stream_id": "s1"} in [c[0][0] for c in calls]


def test_progress_tracker():
    tracker = ProgressTracker("Download", total=10)
    
    # Test update callback
    events = []
    tracker.on_progress(lambda e: events.append(e))

    tracker.update(5, "Downloading half")
    assert len(events) == 1
    assert events[0].percent == 50.0
    assert events[0].message == "Downloading half"
    assert events[0].elapsed_seconds >= 0.0

    # Test context manager finish
    with ProgressTracker("Parsing", total=100) as pt:
        pt.update(80)
        assert pt.percent == 80.0
        # Automatically finishes with 100% on exit


def test_stream_buffer():
    # Strategy: ON_SPACE
    buffer = StreamBuffer(strategy=FlushStrategy.ON_SPACE)
    
    r1 = buffer.add("Hello")
    assert r1 is None  # no space yet
    
    r2 = buffer.add(" ")
    assert r2 == "Hello "  # space found, flushed!

    # Strategy: ON_SIZE
    size_buffer = StreamBuffer(strategy=FlushStrategy.ON_SIZE, max_size=10)
    assert size_buffer.add("verylongtoken") == "verylongtoken"  # exceeds max_size of 10
    
    # Test stream buffering generator
    async def token_gen():
        yield "first"
        yield " "
        yield "second"

    async def run_stream():
        results = []
        async for chunk in buffer.stream(token_gen()):
            results.append(chunk)
        return results

    res = asyncio.run(run_stream())
    # Should yield: "first " (due to space flush) and "second" (remaining flush)
    assert res == ["first ", "second"]
