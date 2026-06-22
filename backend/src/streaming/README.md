# Streaming Support

## Components

| File | Purpose |
|------|---------|
| `streaming_engine.py` | Core streaming primitives |
| `sse_handler.py` | Server-Sent Events (HTTP) |
| `websocket_handler.py` | WebSocket streaming |
| `progress_tracker.py` | Progress reporting |
| `stream_buffer.py` | Token buffering |

## Usage

### Server (FastAPI)

```python
from backend.src.streaming import StreamingEngine, SSEHandler

engine = StreamingEngine()
sse = SSEHandler(engine)

@app.get("/api/v1/stream/query")
async def stream_query(request: Request, query: str):
    async def token_gen():
        ai_response = "This is a streaming response from the AMDI-OS intelligence gateway."
        for word in ai_response.split():
            yield word + " "
            await asyncio.sleep(0.05)
    
    event_stream = engine.stream_tokens(token_gen())
    return await sse.stream_response(request, event_stream)
```

### Client (Browser)

```javascript
const eventSource = new EventSource('/api/v1/stream/query?query=hello');
eventSource.addEventListener('token', (e) => {
    const event = JSON.parse(e.data);
    console.log(event.data.token);
});
eventSource.addEventListener('done', () => eventSource.close());
```
