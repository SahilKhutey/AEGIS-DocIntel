"""
AEGIS-DocIntel Evaluation Feedback Repository
PROT-FINAL-08: Feedback, Defect Storage and Sanitization
"""

from __future__ import annotations

import re
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.schemas.evaluation.feedback import (
    EvaluationFeedback,
    FeedbackCategory,
    FeedbackSeverity,
    FeedbackStatus,
)


class FeedbackNotFoundError(Exception):
    pass


class FeedbackRepository:
    """Thread-safe in-memory store for evaluator feedback and defects."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._feedback_records: Dict[str, EvaluationFeedback] = {}
        self._redaction_patterns = [
            re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE),
            re.compile(r"key-[a-zA-Z0-9_\-]{16,}", re.IGNORECASE),
            re.compile(r"(-----BEGIN [A-Z ]+KEY-----[\s\S]+?-----END [A-Z ]+KEY-----)"),
            re.compile(r"\b(?:\d[ -]*?){13,16}\b"),  # Credit card numbers
        ]

    def sanitize(self, text: str) -> str:
        """Redact secrets, authorization tokens, private keys, or PANs."""
        sanitized = text
        for pat in self._redaction_patterns:
            sanitized = pat.sub("[REDACTED_SECRET]", sanitized)
        return sanitized

    def create(self, feedback: EvaluationFeedback) -> EvaluationFeedback:
        with self._lock:
            # Enforce server-side sanitization on description and repro steps
            clean_desc = self.sanitize(feedback.description)
            clean_steps = self.sanitize(feedback.reproduction_steps) if feedback.reproduction_steps else None
            sanitized_record = feedback.model_copy(
                update={"description": clean_desc, "reproduction_steps": clean_steps}
            )
            self._feedback_records[feedback.id] = sanitized_record
            return sanitized_record

    def get_by_id(self, feedback_id: str) -> Optional[EvaluationFeedback]:
        with self._lock:
            return self._feedback_records.get(feedback_id)

    def list_records(
        self,
        evaluator_id: Optional[str] = None,
        category: Optional[FeedbackCategory] = None,
        severity: Optional[FeedbackSeverity] = None,
        status: Optional[FeedbackStatus] = None,
    ) -> List[EvaluationFeedback]:
        with self._lock:
            records = list(self._feedback_records.values())
            if evaluator_id is not None:
                records = [r for r in records if r.evaluator_id == evaluator_id]
            if category is not None:
                records = [r for r in records if r.category == category]
            if severity is not None:
                records = [r for r in records if r.severity == severity]
            if status is not None:
                records = [r for r in records if r.status == status]
            return records

    def update_status(
        self,
        feedback_id: str,
        new_status: FeedbackStatus,
        status_notes: Optional[str] = None,
        assigned_to: Optional[str] = None,
    ) -> EvaluationFeedback:
        with self._lock:
            record = self.get_by_id(feedback_id)
            if not record:
                raise FeedbackNotFoundError(f"Feedback record '{feedback_id}' not found")

            now_iso = datetime.now(timezone.utc).isoformat()
            updated = record.model_copy(
                update={
                    "status": new_status,
                    "status_notes": status_notes or record.status_notes,
                    "assigned_to": assigned_to or record.assigned_to,
                    "updated_at": now_iso,
                }
            )
            self._feedback_records[feedback_id] = updated
            return updated
