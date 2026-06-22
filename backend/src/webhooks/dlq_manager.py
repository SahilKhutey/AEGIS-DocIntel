"""
AMDI-OS Webhook & Event System: Dead Letter Queue (DLQ) Manager
===============================================================

Handles storage, serialization, and retrieval of failed webhook delivery payloads 
after all retry attempts are exhausted.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time
import json


@dataclass
class DLQRecord:
    dlq_id: str
    event_id: str
    topic: str
    payload: Dict[str, Any]
    destination_url: str
    failure_reason: str
    failed_at: float
    attempts_made: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dlq_id": self.dlq_id,
            "event_id": self.event_id,
            "topic": self.topic,
            "payload": self.payload,
            "destination_url": self.destination_url,
            "failure_reason": self.failure_reason,
            "failed_at": self.failed_at,
            "attempts_made": self.attempts_made
        }


class DeadLetterQueueManager:
    """
    Manages failed webhook payloads for auditing, analysis, and manual retries.
    """
    def __init__(self):
        self.queue: Dict[str, DLQRecord] = {}

    def enqueue(
        self, 
        event_id: str, 
        topic: str, 
        payload: Dict[str, Any], 
        destination_url: str, 
        failure_reason: str, 
        attempts_made: int
    ) -> DLQRecord:
        """
        Stores a failed delivery record in the DLQ.
        """
        dlq_id = f"dlq_{int(time.time())}_{event_id}"
        record = DLQRecord(
            dlq_id=dlq_id,
            event_id=event_id,
            topic=topic,
            payload=payload,
            destination_url=destination_url,
            failure_reason=failure_reason,
            failed_at=time.time(),
            attempts_made=attempts_made
        )
        self.queue[dlq_id] = record
        return record

    def list_records(self, topic: Optional[str] = None) -> List[DLQRecord]:
        """
        Lists all DLQ records, optionally filtered by topic.
        """
        records = list(self.queue.values())
        if topic:
            records = [r for r in records if r.topic == topic]
        # Sort by failed_at descending
        records.sort(key=lambda x: x.failed_at, reverse=True)
        return records

    def get_record(self, dlq_id: str) -> Optional[DLQRecord]:
        """
        Retrieves a specific DLQ record.
        """
        return self.queue.get(dlq_id)

    def remove_record(self, dlq_id: str) -> bool:
        """
        Removes/purges a DLQ record after inspection or manual retry.
        """
        if dlq_id in self.queue:
            del self.queue[dlq_id]
            return True
        return False

    def clear(self) -> None:
        """
        Purges all records from the DLQ.
        """
        self.queue.clear()

    def export_json(self) -> str:
        """
        Serializes all DLQ records to a JSON string.
        """
        data = [r.to_dict() for r in self.queue.values()]
        return json.dumps(data, indent=2)
