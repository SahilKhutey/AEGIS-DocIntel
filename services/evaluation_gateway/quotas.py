"""
AEGIS-DocIntel Evaluation Gateway — Server-Side Quota Enforcement
Tracks and strictly enforces usage limits per evaluation license:
- Max 5 document uploads
- Max 20 queries / 24 hours
- Max 5 comparisons / 24 hours
- Max upload file size: 10 MB
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

class QuotaExceededError(Exception):
    def __init__(self, resource: str, current: int, limit: int, message: Optional[str] = None):
        self.resource = resource
        self.current = current
        self.limit = limit
        msg = message or f"Evaluation quota exceeded for {resource}: {current}/{limit}. Contact sales@aegis-docintel.io for full access."
        super().__init__(msg)


@dataclass
class LicenseUsage:
    uploaded_doc_ids: set[str] = field(default_factory=set)
    query_timestamps: List[float] = field(default_factory=list)
    comparison_timestamps: List[float] = field(default_factory=list)
    request_timestamps: List[float] = field(default_factory=list)


class QuotaManager:
    def __init__(
        self,
        default_max_documents: int = 5,
        default_max_queries_per_day: int = 20,
        default_max_comparisons_per_day: int = 5,
        max_file_size_bytes: int = 10 * 1024 * 1024,  # 10 MB
        rate_limit_per_minute: int = 60
    ):
        self.default_max_documents = default_max_documents
        self.default_max_queries_per_day = default_max_queries_per_day
        self.default_max_comparisons_per_day = default_max_comparisons_per_day
        self.max_file_size_bytes = max_file_size_bytes
        self.rate_limit_per_minute = rate_limit_per_minute
        self._usage: Dict[str, LicenseUsage] = defaultdict(LicenseUsage)

    def _prune_sliding_window(self, timestamps: List[float], window_seconds: float) -> List[float]:
        now = time.time()
        cutoff = now - window_seconds
        return [ts for ts in timestamps if ts >= cutoff]

    def check_rate_limit(self, license_id: str) -> None:
        """Enforces requests per minute rate limit to prevent abuse / scraping."""
        now = time.time()
        usage = self._usage[license_id]
        usage.request_timestamps = self._prune_sliding_window(usage.request_timestamps, 60.0)
        if len(usage.request_timestamps) >= self.rate_limit_per_minute:
            raise QuotaExceededError(
                resource="rate_limit",
                current=len(usage.request_timestamps),
                limit=self.rate_limit_per_minute,
                message=f"Rate limit exceeded: {self.rate_limit_per_minute} requests/minute."
            )
        usage.request_timestamps.append(now)

    def record_document_upload(self, license_id: str, doc_id: str, file_size_bytes: int, max_limit: Optional[int] = None) -> None:
        """Checks and records a document upload against quota and file size limits."""
        if file_size_bytes > self.max_file_size_bytes:
            raise ValueError(
                f"File size {file_size_bytes} bytes exceeds maximum evaluation limit of {self.max_file_size_bytes} bytes (10 MB)."
            )

        limit = max_limit if max_limit is not None else self.default_max_documents
        usage = self._usage[license_id]
        
        # If document is already counted, allow re-upload/update
        if doc_id in usage.uploaded_doc_ids:
            return

        if len(usage.uploaded_doc_ids) >= limit:
            raise QuotaExceededError(
                resource="documents",
                current=len(usage.uploaded_doc_ids),
                limit=limit,
                message=f"Document upload limit reached ({len(usage.uploaded_doc_ids)}/{limit}). Upgrade to AEGIS Enterprise for unlimited ingestion."
            )
        usage.uploaded_doc_ids.add(doc_id)

    def record_query(self, license_id: str, max_limit: Optional[int] = None) -> int:
        """Checks and records an Ask AEGIS query against daily quota."""
        limit = max_limit if max_limit is not None else self.default_max_queries_per_day
        usage = self._usage[license_id]
        # 24-hour sliding window: 86400 seconds
        usage.query_timestamps = self._prune_sliding_window(usage.query_timestamps, 86400.0)

        if len(usage.query_timestamps) >= limit:
            raise QuotaExceededError(
                resource="queries",
                current=len(usage.query_timestamps),
                limit=limit,
                message=f"Daily evaluation query quota reached ({len(usage.query_timestamps)}/{limit}). Quota resets automatically after 24 hours."
            )
        now = time.time()
        usage.query_timestamps.append(now)
        return len(usage.query_timestamps)

    def record_comparison(self, license_id: str, max_limit: Optional[int] = None) -> int:
        """Checks and records a document comparison against daily quota."""
        limit = max_limit if max_limit is not None else self.default_max_comparisons_per_day
        usage = self._usage[license_id]
        usage.comparison_timestamps = self._prune_sliding_window(usage.comparison_timestamps, 86400.0)

        if len(usage.comparison_timestamps) >= limit:
            raise QuotaExceededError(
                resource="comparisons",
                current=len(usage.comparison_timestamps),
                limit=limit,
                message=f"Daily document comparison quota reached ({len(usage.comparison_timestamps)}/{limit})."
            )
        now = time.time()
        usage.comparison_timestamps.append(now)
        return len(usage.comparison_timestamps)

    def get_quota_status(self, license_id: str, quotas: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Returns current utilization summary for the specified license."""
        usage = self._usage[license_id]
        usage.query_timestamps = self._prune_sliding_window(usage.query_timestamps, 86400.0)
        usage.comparison_timestamps = self._prune_sliding_window(usage.comparison_timestamps, 86400.0)

        q = quotas or {}
        max_docs = q.get("max_documents", self.default_max_documents)
        max_queries = q.get("max_queries_per_day", self.default_max_queries_per_day)
        max_comparisons = q.get("max_comparisons_per_day", self.default_max_comparisons_per_day)

        return {
            "documents": {
                "used": len(usage.uploaded_doc_ids),
                "limit": max_docs,
                "remaining": max(0, max_docs - len(usage.uploaded_doc_ids))
            },
            "queries": {
                "used": len(usage.query_timestamps),
                "limit": max_queries,
                "remaining": max(0, max_queries - len(usage.query_timestamps))
            },
            "comparisons": {
                "used": len(usage.comparison_timestamps),
                "limit": max_comparisons,
                "remaining": max(0, max_comparisons - len(usage.comparison_timestamps))
            }
        }

    def reset_usage(self, license_id: str) -> None:
        """Resets all usage counters for a given license (for tests/demo resets)."""
        if license_id in self._usage:
            del self._usage[license_id]


# Global manager instance
quota_manager = QuotaManager()
