"""
AMDI-OS Webhook & Event System: Webhook Manager
================================================

Orchestrates webhook registrations (CRUD), matches events to subscription topics,
and dispatches payloads asynchronously with HMAC-SHA256 security signatures 
and retry/DLQ fallback logic.
"""

from typing import List, Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
import uuid
import hmac
import hashlib
import time
import json
import asyncio
import httpx

from .event_types import Event
from .event_filter import match_topic
from .retry_handler import execute_with_retry
from .dlq_manager import DeadLetterQueueManager


@dataclass
class WebhookSubscription:
    subscription_id: str
    tenant_id: str
    url: str
    secret_token: str
    topic_pattern: str
    is_active: bool = True
    created_at: float = field(default_factory=time.time)


class WebhookManager:
    """
    Manages subscriber records and executes async event dispatch pipelines.
    """
    def __init__(self, dlq_manager: Optional[DeadLetterQueueManager] = None):
        self.subscriptions: Dict[str, WebhookSubscription] = {}
        self.dlq_manager = dlq_manager or DeadLetterQueueManager()
        
        # Dispatch client function: can be overridden in tests to prevent real HTTP calls
        self.post_client_fn: Callable[[str, Dict[str, str], Dict[str, Any]], Awaitable[httpx.Response]] = self._real_http_post

    async def _real_http_post(self, url: str, headers: Dict[str, str], json_data: Dict[str, Any]) -> httpx.Response:
        """
        Performs actual outgoing HTTP POST request.
        """
        async with httpx.AsyncClient() as client:
            return await client.post(url, headers=headers, json=json_data, timeout=5.0)

    def create_subscription(
        self, 
        tenant_id: str, 
        url: str, 
        secret_token: str, 
        topic_pattern: str
    ) -> WebhookSubscription:
        """
        Registers a new webhook subscriber.
        """
        sub_id = f"sub_{uuid.uuid4().hex[:12]}"
        sub = WebhookSubscription(
            subscription_id=sub_id,
            tenant_id=tenant_id,
            url=url,
            secret_token=secret_token,
            topic_pattern=topic_pattern
        )
        self.subscriptions[sub_id] = sub
        return sub

    def get_subscription(self, sub_id: str) -> Optional[WebhookSubscription]:
        return self.subscriptions.get(sub_id)

    def delete_subscription(self, sub_id: str) -> bool:
        if sub_id in self.subscriptions:
            del self.subscriptions[sub_id]
            return True
        return False

    def list_subscriptions(self, tenant_id: Optional[str] = None) -> List[WebhookSubscription]:
        subs = list(self.subscriptions.values())
        if tenant_id:
            subs = [s for s in subs if s.tenant_id == tenant_id]
        return subs

    def generate_hmac_signature(self, payload_str: str, secret: str) -> str:
        """
        Generates HMAC-SHA256 signature for payload verification.
        """
        return hmac.new(
            secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    async def dispatch_event(self, event: Event, tenant_id: str) -> List[asyncio.Task]:
        """
        Finds active matching subscriptions for the tenant and launches dispatch tasks.
        Returns:
            List of asyncio tasks handling the dispatch requests.
        """
        active_subs = [
            sub for sub in self.subscriptions.values()
            if sub.tenant_id == tenant_id and sub.is_active and match_topic(sub.topic_pattern, event.topic)
        ]
        
        tasks = []
        for sub in active_subs:
            task = asyncio.create_task(self._deliver_to_subscription(event, sub))
            tasks.append(task)
            
        return tasks

    async def _deliver_to_subscription(self, event: Event, sub: WebhookSubscription) -> bool:
        """
        Delivers the event payload to a single subscription.
        Calculates signatures, executes retry loops, and pushes to DLQ on failure.
        """
        payload = event.to_dict()
        payload_str = json.dumps(payload, sort_keys=True)
        timestamp_str = str(int(time.time()))
        
        # Prepare secure headers
        signature = self.generate_hmac_signature(f"{timestamp_str}.{payload_str}", sub.secret_token)
        headers = {
            "Content-Type": "application/json",
            "X-AMDI-Signature": signature,
            "X-AMDI-Timestamp": timestamp_str,
            "X-AMDI-Tenant-ID": sub.tenant_id
        }

        attempts_made = 0

        async def attempt_delivery():
            nonlocal attempts_made
            attempts_made += 1
            response = await self.post_client_fn(sub.url, headers, payload)
            # Treat non-2xx codes as exceptions to trigger retry logic
            if response.status_code < 200 or response.status_code >= 300:
                raise httpx.HTTPStatusError(
                    f"HTTP Error {response.status_code}", 
                    request=response.request, 
                    response=response
                )
            return response

        try:
            # Dispatch with exponential backoff retries
            await execute_with_retry(
                func=attempt_delivery,
                max_attempts=3,
                base=0.5,
                factor=2.0,
                max_delay=5.0
            )
            return True
        except Exception as e:
            # Deliver to Dead Letter Queue
            self.dlq_manager.enqueue(
                event_id=event.event_id,
                topic=event.topic,
                payload=payload,
                destination_url=sub.url,
                failure_reason=str(e),
                attempts_made=attempts_made
            )
            return False
