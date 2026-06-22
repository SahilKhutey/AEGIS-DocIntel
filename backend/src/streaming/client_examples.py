"""
Client Examples
================

Example clients for SSE and WebSocket streaming.
"""

# SSE Client Example (JavaScript)
SSE_CLIENT_EXAMPLE = """
// Browser JavaScript
const eventSource = new EventSource('/api/v1/stream/query?query=...');
eventSource.addEventListener('token', (e) => {
    const event = JSON.parse(e.data);
    document.getElementById('output').innerText += event.data.token;
});
eventSource.addEventListener('done', (e) => {
    eventSource.close();
});
eventSource.addEventListener('error', (e) => {
    console.error('Stream error:', e);
});
"""

# WebSocket Client Example (Python)
WEBSOCKET_CLIENT_EXAMPLE_PYTHON = '''
import asyncio
import websockets
import json

async def stream_query(query: str):
    uri = "ws://localhost:8000/api/v1/ws"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "type": "query",
            "query": query,
        }))
        while True:
            message = await ws.recv()
            event = json.loads(message)
            if event["event_type"] == "token":
                print(event["data"]["token"], end="", flush=True)
            elif event["event_type"] == "done":
                print()
                break
            elif event["event_type"] == "error":
                print(f"Error: {event['data']}")
                break

asyncio.run(stream_query("What is quantum entanglement?"))
'''

# cURL Example
CURL_EXAMPLE = """
curl -N -H "Accept: text/event-stream" \\
     -H "Authorization: Bearer YOUR_TOKEN" \\
     "http://localhost:8000/api/v1/stream/query?query=quantum"
"""
