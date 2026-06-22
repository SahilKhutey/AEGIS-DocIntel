"""
AMDI-OS Webhook & Event System
==============================

Handles event subscription, wildcard filtering, exponential backoff retries,
secure payload signatures, and dead letter queue serialization.
"""

from .event_types import (
    Event,
    EventTopic,
)
from .event_filter import (
    match_topic,
)
from .retry_handler import (
    calculate_backoff,
    execute_with_retry,
)
from .dlq_manager import (
    DLQRecord,
    DeadLetterQueueManager,
)
from .webhook_manager import (
    WebhookSubscription,
    WebhookManager,
)

__all__ = [
    "Event",
    "EventTopic",
    "match_topic",
    "calculate_backoff",
    "execute_with_retry",
    "DLQRecord",
    "DeadLetterQueueManager",
    "WebhookSubscription",
    "WebhookManager",
]
