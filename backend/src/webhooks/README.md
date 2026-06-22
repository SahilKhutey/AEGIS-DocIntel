# AMDI-OS Webhook & Event System

The Webhook & Event System provides robust subscription CRUD, wildcard topic filtering, secure payload signatures, exponential backoff retries, and dead letter queue routing.

---

## Security Verification (HMAC-SHA256)

Webhook requests include security headers to protect receivers from spoofing and replay attacks.
- `X-AMDI-Signature`: The computed HMAC signature.
- `X-AMDI-Timestamp`: The Unix timestamp of when the request was dispatched.
- `X-AMDI-Tenant-ID`: The tenant initiating the event.

To verify a payload at your endpoint:
1. Concatenate the timestamp header, a literal dot `.`, and the raw JSON request body:
   `signature_payload = timestamp + "." + raw_request_body`
2. Calculate HMAC-SHA256 using your subscription's `secret_token` as the key.
3. Compare the hex digest with the `X-AMDI-Signature` header value (using a constant-time comparison).

---

## Code Example

```python
import asyncio
from backend.src.webhooks import WebhookManager, Event, EventTopic

async def main():
    manager = WebhookManager()
    
    # Create subscription matching all document events
    manager.create_subscription(
        tenant_id="tenant_123",
        url="https://api.acme.com/webhooks/receiver",
        secret_token="super_secret_token",
        topic_pattern="document.*"
    )

    # Trigger event
    event = Event(
        topic=EventTopic.DOCUMENT_PROCESSED,
        payload={"doc_id": "doc_999", "status": "completed"}
    )

    # Dispatches asynchronously
    tasks = await manager.dispatch_event(event, tenant_id="tenant_123")
    await asyncio.gather(*tasks)

asyncio.run(main())
```
