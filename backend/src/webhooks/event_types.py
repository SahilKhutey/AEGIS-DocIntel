"""
AMDI-OS Webhook & Event System: Event Types
===========================================

Defines the structure, topics, and serialization formats for events dispatched 
within the system.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import uuid
import time
from enum import Enum


class EventTopic(str, Enum):
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_FAILED = "document.failed"
    QUERY_COMPLETED = "query.completed"
    BILLING_INVOICE_CREATED = "billing.invoice_created"
    TENANT_CREATED = "tenant.created"
    TENANT_SUSPENDED = "tenant.suspended"


@dataclass
class Event:
    """
    Represents an event triggered by AMDI-OS to be sent to subscribers.
    """
    topic: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.event_id,
            "topic": self.topic,
            "timestamp": self.timestamp,
            "payload": self.payload
        }
