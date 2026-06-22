import os
import sys
from pathlib import Path
import pytest
import asyncio
import time
import json
import httpx

# Configure Python path to find backend packages
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.src.webhooks import (
    Event,
    EventTopic,
    match_topic,
    calculate_backoff,
    execute_with_retry,
    DeadLetterQueueManager,
    WebhookManager,
)


def test_topic_matching():
    assert match_topic("*", "document.processed") is True
    assert match_topic("document.*", "document.processed") is True
    assert match_topic("document.*", "document.failed") is True
    assert match_topic("document.*", "query.completed") is False
    assert match_topic("document.processed", "document.processed") is True
    assert match_topic("document.processed", "document.failed") is False
    assert match_topic("query.*", "query.completed") is True
    assert match_topic("query.*", "query") is False


def test_backoff_calculation():
    # Attempt 0: delay should be 1.0 without jitter
    assert calculate_backoff(0, base=1.0, factor=2.0, max_delay=30.0, jitter=False) == 1.0
    # Attempt 2: delay = 1.0 * (2^2) = 4.0
    assert calculate_backoff(2, base=1.0, factor=2.0, max_delay=30.0, jitter=False) == 4.0
    # Max delay clamping
    assert calculate_backoff(10, base=1.0, factor=2.0, max_delay=5.0, jitter=False) == 5.0

    # With jitter
    delay_with_jitter = calculate_backoff(3, base=1.0, factor=2.0, max_delay=30.0, jitter=True)
    # Expected base delay: 1.0 * (2^3) = 8.0. Jitter can add up to 50% => between 8.0 and 12.0
    assert 8.0 <= delay_with_jitter <= 12.0

    with pytest.raises(ValueError):
        calculate_backoff(-1)


@pytest.mark.asyncio
async def test_execute_with_retry():
    attempts = 0

    async def faulty_function():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Failure")
        return "Success"

    # Will succeed on 3rd attempt
    res = await execute_with_retry(
        func=faulty_function,
        max_attempts=3,
        base=0.01,
        factor=2.0
    )
    assert res == "Success"
    assert attempts == 3


def test_webhook_crud():
    manager = WebhookManager()
    sub = manager.create_subscription(
        tenant_id="tenant_A",
        url="https://example.com/receiver",
        secret_token="token123",
        topic_pattern="document.*"
    )

    assert sub.subscription_id.startswith("sub_")
    assert sub.tenant_id == "tenant_A"
    assert sub.url == "https://example.com/receiver"
    assert sub.secret_token == "token123"
    assert sub.topic_pattern == "document.*"

    # Get
    assert manager.get_subscription(sub.subscription_id) == sub

    # List
    assert len(manager.list_subscriptions("tenant_A")) == 1
    assert len(manager.list_subscriptions("tenant_B")) == 0

    # Delete
    assert manager.delete_subscription(sub.subscription_id) is True
    assert manager.get_subscription(sub.subscription_id) is None


@pytest.mark.asyncio
async def test_webhook_event_delivery_success():
    manager = WebhookManager()
    sub = manager.create_subscription(
        tenant_id="tenant_A",
        url="https://example.com/receiver",
        secret_token="secret_key",
        topic_pattern="document.*"
    )

    # Mock dispatcher to return 200 OK Response without making network call
    called_url = None
    called_headers = {}
    called_payload = None

    async def mock_post(url, headers, json_data):
        nonlocal called_url, called_headers, called_payload
        called_url = url
        called_headers = headers
        called_payload = json_data
        
        # Build mock response
        request = httpx.Request("POST", url)
        return httpx.Response(status_code=200, request=request)

    manager.post_client_fn = mock_post

    event = Event(
        topic=EventTopic.DOCUMENT_PROCESSED,
        payload={"doc_id": "doc123", "pages": 15}
    )

    tasks = await manager.dispatch_event(event, tenant_id="tenant_A")
    assert len(tasks) == 1
    
    # Wait for delivery to finish
    success = await tasks[0]
    assert success is True
    assert called_url == "https://example.com/receiver"

    # Verify signature headers
    assert "X-AMDI-Signature" in called_headers
    assert "X-AMDI-Timestamp" in called_headers
    assert called_headers["X-AMDI-Tenant-ID"] == "tenant_A"

    # Recompute signature locally to verify payload integrity
    timestamp = called_headers["X-AMDI-Timestamp"]
    payload_str = json.dumps(event.to_dict(), sort_keys=True)
    expected_sig = manager.generate_hmac_signature(f"{timestamp}.{payload_str}", "secret_key")
    assert called_headers["X-AMDI-Signature"] == expected_sig


@pytest.mark.asyncio
async def test_webhook_delivery_failure_to_dlq():
    dlq = DeadLetterQueueManager()
    manager = WebhookManager(dlq_manager=dlq)
    
    sub = manager.create_subscription(
        tenant_id="tenant_A",
        url="https://example.com/receiver",
        secret_token="secret_key",
        topic_pattern="document.*"
    )

    # Mock POST to fail consistently
    async def mock_failed_post(url, headers, json_data):
        request = httpx.Request("POST", url)
        return httpx.Response(status_code=500, request=request)

    manager.post_client_fn = mock_failed_post

    event = Event(
        topic=EventTopic.DOCUMENT_FAILED,
        payload={"doc_id": "doc123", "error": "ocr_failed"}
    )

    tasks = await manager.dispatch_event(event, tenant_id="tenant_A")
    assert len(tasks) == 1
    
    success = await tasks[0]
    assert success is False

    # Check Dead Letter Queue
    dlq_records = dlq.list_records()
    assert len(dlq_records) == 1
    record = dlq_records[0]
    
    assert record.event_id == event.event_id
    assert record.topic == EventTopic.DOCUMENT_FAILED
    assert record.destination_url == "https://example.com/receiver"
    assert "HTTP Error 500" in record.failure_reason
    assert record.attempts_made == 3  # Max attempts is 3 inside manager

    # Verify JSON export
    exported_json = dlq.export_json()
    exported_data = json.loads(exported_json)
    assert len(exported_data) == 1
    assert exported_data[0]["event_id"] == event.event_id
