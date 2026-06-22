"""
Feedback Loop
==============

User feedback integration for continuous learning.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Deque, Dict, List, Optional


class FeedbackType(Enum):
    """Types of user feedback."""

    EXPLICIT_RATING = "explicit_rating"  # 1-5 stars
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    IMPLICIT_CLICK = "implicit_click"
    IMPLICIT_DWELL = "implicit_dwell"
    IMPLICIT_COPY = "implicit_copy"
    IMPLICIT_SHARE = "implicit_share"
    CORRECTION = "correction"
    FOLLOWUP = "followup"
    ABANDONMENT = "abandonment"


@dataclass
class UserRating:
    """An explicit user rating."""

    user_id: str
    query: str
    response: str
    rating: int  # 1-5
    comment: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedbackEvent:
    """A single feedback event."""

    event_id: str
    feedback_type: FeedbackType
    user_id: str
    query: str
    response: str
    response_id: str
    rating: Optional[float] = None  # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "feedback_type": self.feedback_type.value,
            "user_id": self.user_id,
            "query": self.query,
            "response": self.response[:200],
            "response_id": self.response_id,
            "rating": self.rating,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class FeedbackLoop:
    """
    Process user feedback for meta-learning.
    """

    def __init__(self, max_history: int = 10_000) -> None:
        self.history: Deque[FeedbackEvent] = deque(maxlen=max_history)
        # aggregates per query
        self.query_feedback: Dict[str, List[FeedbackEvent]] = {}
        # aggregates per document type
        self.type_feedback: Dict[str, List[FeedbackEvent]] = {}

    def record_explicit_rating(
        self,
        user_id: str,
        query: str,
        response: str,
        rating: int,
        response_id: str = "",
        comment: Optional[str] = None,
    ) -> FeedbackEvent:
        """Record an explicit 1-5 star rating."""
        event = FeedbackEvent(
            event_id=f"fb_{int(time.time() * 1000)}",
            feedback_type=FeedbackType.EXPLICIT_RATING,
            user_id=user_id,
            query=query,
            response=response,
            response_id=response_id,
            rating=(rating - 1) / 4.0,  # normalize to 0-1
            metadata={"comment": comment, "raw_rating": rating},
        )
        self._record(event)
        return event

    def record_thumbs(self, user_id: str, query: str, response: str, up: bool) -> FeedbackEvent:
        """Record a thumbs up/down."""
        event = FeedbackEvent(
            event_id=f"fb_{int(time.time() * 1000)}",
            feedback_type=FeedbackType.THUMBS_UP if up else FeedbackType.THUMBS_DOWN,
            user_id=user_id,
            query=query,
            response=response,
            response_id="",
            rating=1.0 if up else 0.0,
        )
        self._record(event)
        return event

    def record_implicit(
        self,
        feedback_type: FeedbackType,
        user_id: str,
        query: str,
        response: str,
        response_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FeedbackEvent:
        """Record an implicit feedback signal."""
        # implicit rating based on type
        rating_map = {
            FeedbackType.IMPLICIT_CLICK: 0.6,
            FeedbackType.IMPLICIT_DWELL: 0.7,
            FeedbackType.IMPLICIT_COPY: 0.9,
            FeedbackType.IMPLICIT_SHARE: 0.95,
            FeedbackType.FOLLOWUP: 0.7,
            FeedbackType.ABANDONMENT: 0.2,
        }
        event = FeedbackEvent(
            event_id=f"fb_{int(time.time() * 1000)}",
            feedback_type=feedback_type,
            user_id=user_id,
            query=query,
            response=response,
            response_id=response_id,
            rating=rating_map.get(feedback_type, 0.5),
            metadata=metadata or {},
        )
        self._record(event)
        return event

    def _record(self, event: FeedbackEvent) -> None:
        self.history.append(event)
        # group by query
        q_key = event.query[:100]
        if q_key not in self.query_feedback:
            self.query_feedback[q_key] = []
        self.query_feedback[q_key].append(event)

    def get_query_feedback(self, query: str) -> Dict[str, float]:
        """Get aggregated feedback for a query."""
        events = self.query_feedback.get(query[:100], [])
        if not events:
            return {"count": 0, "avg_rating": 0.0, "positive": 0, "negative": 0}
        ratings = [e.rating for e in events if e.rating is not None]
        positive = sum(1 for r in ratings if r >= 0.6)
        negative = sum(1 for r in ratings if r < 0.4)
        return {
            "count": len(events),
            "avg_rating": sum(ratings) / len(ratings) if ratings else 0.0,
            "positive": positive,
            "negative": negative,
        }

    def get_recent_signals(self, n: int = 100) -> List[FeedbackEvent]:
        return list(self.history)[-n:]

    def get_stats(self) -> Dict[str, Any]:
        events = list(self.history)
        if not events:
            return {"total_events": 0}
        ratings = [e.rating for e in events if e.rating is not None]
        return {
            "total_events": len(events),
            "avg_rating": sum(ratings) / len(ratings) if ratings else 0.0,
            "thumbs_up": sum(1 for e in events if e.feedback_type == FeedbackType.THUMBS_UP),
            "thumbs_down": sum(1 for e in events if e.feedback_type == FeedbackType.THUMBS_DOWN),
            "explicit_ratings": sum(1 for e in events if e.feedback_type == FeedbackType.EXPLICIT_RATING),
        }
