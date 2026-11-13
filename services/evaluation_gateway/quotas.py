"""
AEGIS-DocIntel Evaluation Gateway — Server-Side Atomic Quota Enforcement
Tracks and strictly enforces usage limits per evaluation license:
- Max 5 document uploads (configurable up to 20)
- Max 20 queries / 24 hours (configurable up to 100)
- Max 5 comparisons / 24 hours (configurable up to 10)
- Max upload file size: 10 MB
- Max total storage: 100 MB
- Atomic reservation and settlement with thread-safety for multi-concurrency (PROT-04 WP-04.06)
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple


class QuotaExceededError(Exception):
    def __init__(self, resource: str, current: int, limit: int, message: Optional[str] = None):
        self.resource = resource
        self.current = current
        self.limit = limit
        msg = message or f"Evaluation quota exceeded for {resource}: {current}/{limit}. Contact sales@aegis-docintel.io for full access."
        super().__init__(msg)


@dataclass
class LicenseUsage:
    uploaded_doc_ids: Set[str] = field(default_factory=set)
    uploaded_bytes: int = 0
    query_timestamps: List[float] = field(default_factory=list)
    comparison_timestamps: List[float] = field(default_factory=list)
    request_timestamps: List[float] = field(default_factory=list)
    # Active reservations for in-flight requests: reservation_id -> (metric, amount, timestamp)
    pending_reservations: Dict[str, Tuple[str, int, float]] = field(default_factory=dict)


class QuotaManager:
    def __init__(
        self,
        default_max_documents: int = 5,
        default_max_queries_per_day: int = 20,
        default_max_comparisons_per_day: int = 5,
        max_file_size_bytes: int = 10 * 1024 * 1024,  # 10 MB
        max_storage_bytes: int = 100 * 1024 * 1024,  # 100 MB
        rate_limit_per_minute: int = 60,
    ):
        self.default_max_documents = default_max_documents
        self.default_max_queries_per_day = default_max_queries_per_day
        self.default_max_comparisons_per_day = default_max_comparisons_per_day
        self.max_file_size_bytes = max_file_size_bytes
        self.max_storage_bytes = max_storage_bytes
        self.rate_limit_per_minute = rate_limit_per_minute
        self._usage: Dict[str, LicenseUsage] = defaultdict(LicenseUsage)
        self._lock = threading.Lock()

    def _prune_sliding_window(self, timestamps: List[float], window_seconds: float) -> List[float]:
        now = time.time()
        cutoff = now - window_seconds
        return [ts for ts in timestamps if ts >= cutoff]

    def check_rate_limit(self, license_id: str) -> None:
        """Enforces requests-per-minute rate limit to prevent abuse or brute-force."""
        with self._lock:
            now = time.time()
            usage = self._usage[license_id]
            usage.request_timestamps = self._prune_sliding_window(usage.request_timestamps, 60.0)
            if len(usage.request_timestamps) >= self.rate_limit_per_minute:
                raise QuotaExceededError(
                    resource="rate_limit",
                    current=len(usage.request_timestamps),
                    limit=self.rate_limit_per_minute,
                    message=f"Rate limit exceeded: {self.rate_limit_per_minute} requests/minute. Please back off."
                )
            usage.request_timestamps.append(now)

    def reserve_quota(
        self,
        license_id: str,
        metric: str,
        amount: int = 1,
        max_limit: Optional[int] = None,
        reservation_id: Optional[str] = None
    ) -> str:
        """
        Atomically reserves quota before executing an expensive operation.
        Prevents race conditions in parallel requests (QUOTA-003).
        """
        import uuid
        res_id = reservation_id or str(uuid.uuid4())

        with self._lock:
            usage = self._usage[license_id]
            now = time.time()

            if metric == "queries":
                usage.query_timestamps = self._prune_sliding_window(usage.query_timestamps, 86400.0)
                active_query_reservations = sum(
                    amt for (m, amt, _) in usage.pending_reservations.values() if m == "queries"
                )
                limit = max_limit if max_limit is not None else self.default_max_queries_per_day
                if (len(usage.query_timestamps) + active_query_reservations + amount) > limit:
                    raise QuotaExceededError(
                        resource="queries",
                        current=len(usage.query_timestamps) + active_query_reservations,
                        limit=limit,
                        message=f"Query quota exceeded ({len(usage.query_timestamps) + active_query_reservations}/{limit})."
                    )
                usage.pending_reservations[res_id] = ("queries", amount, now)

            elif metric == "comparisons":
                usage.comparison_timestamps = self._prune_sliding_window(usage.comparison_timestamps, 86400.0)
                active_comp_reservations = sum(
                    amt for (m, amt, _) in usage.pending_reservations.values() if m == "comparisons"
                )
                limit = max_limit if max_limit is not None else self.default_max_comparisons_per_day
                if (len(usage.comparison_timestamps) + active_comp_reservations + amount) > limit:
                    raise QuotaExceededError(
                        resource="comparisons",
                        current=len(usage.comparison_timestamps) + active_comp_reservations,
                        limit=limit,
                        message=f"Comparison quota exceeded ({len(usage.comparison_timestamps) + active_comp_reservations}/{limit})."
                    )
                usage.pending_reservations[res_id] = ("comparisons", amount, now)

            elif metric == "documents":
                limit = max_limit if max_limit is not None else self.default_max_documents
                active_doc_reservations = sum(
                    amt for (m, amt, _) in usage.pending_reservations.values() if m == "documents"
                )
                if (len(usage.uploaded_doc_ids) + active_doc_reservations + amount) > limit:
                    raise QuotaExceededError(
                        resource="documents",
                        current=len(usage.uploaded_doc_ids) + active_doc_reservations,
                        limit=limit,
                        message=f"Document upload limit reached ({len(usage.uploaded_doc_ids) + active_doc_reservations}/{limit})."
                    )
                usage.pending_reservations[res_id] = ("documents", amount, now)

            else:
                raise ValueError(f"Unknown quota metric: {metric}")

        return res_id

    def settle_reservation(self, license_id: str, reservation_id: str) -> None:
        """Settles an in-flight reservation into permanent usage accounting."""
        with self._lock:
            usage = self._usage[license_id]
            if reservation_id not in usage.pending_reservations:
                return
            metric, amount, _ = usage.pending_reservations.pop(reservation_id)
            now = time.time()
            if metric == "queries":
                for _ in range(amount):
                    usage.query_timestamps.append(now)
            elif metric == "comparisons":
                for _ in range(amount):
                    usage.comparison_timestamps.append(now)

    def rollback_reservation(self, license_id: str, reservation_id: str) -> None:
        """Rolls back an in-flight reservation if an operation fails."""
        with self._lock:
            usage = self._usage[license_id]
            usage.pending_reservations.pop(reservation_id, None)

    def record_document_upload(
        self,
        license_id: str,
        doc_id: str,
        file_size_bytes: int,
        max_limit: Optional[int] = None,
    ) -> None:
        """Atomically checks and records document upload against count and storage quotas."""
        if file_size_bytes > self.max_file_size_bytes:
            raise ValueError(
                f"File size {file_size_bytes} bytes exceeds maximum evaluation limit of {self.max_file_size_bytes} bytes (10 MB)."
            )

        with self._lock:
            usage = self._usage[license_id]

            if (usage.uploaded_bytes + file_size_bytes) > self.max_storage_bytes:
                raise QuotaExceededError(
                    resource="storage",
                    current=usage.uploaded_bytes + file_size_bytes,
                    limit=self.max_storage_bytes,
                    message=f"Total storage quota exceeded ({usage.uploaded_bytes // (1024*1024)} MB / 100 MB).",
                )

            # If document is already counted, allow re-upload/update
            if doc_id in usage.uploaded_doc_ids:
                return

            limit = max_limit if max_limit is not None else self.default_max_documents
            if len(usage.uploaded_doc_ids) >= limit:
                raise QuotaExceededError(
                    resource="documents",
                    current=len(usage.uploaded_doc_ids),
                    limit=limit,
                    message=f"Document upload limit reached ({len(usage.uploaded_doc_ids)}/{limit}). Upgrade to AEGIS Enterprise for unlimited ingestion."
                )

            usage.uploaded_doc_ids.add(doc_id)
            usage.uploaded_bytes += file_size_bytes

    def record_query(self, license_id: str, max_limit: Optional[int] = None) -> int:
        """Atomically checks and records an Ask AEGIS query against daily quota."""
        limit = max_limit if max_limit is not None else self.default_max_queries_per_day
        with self._lock:
            usage = self._usage[license_id]
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
        """Atomically checks and records a document comparison against daily quota."""
        limit = max_limit if max_limit is not None else self.default_max_comparisons_per_day
        with self._lock:
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
        with self._lock:
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
                    "remaining": max(0, max_docs - len(usage.uploaded_doc_ids)),
                },
                "queries": {
                    "used": len(usage.query_timestamps),
                    "limit": max_queries,
                    "remaining": max(0, max_queries - len(usage.query_timestamps)),
                },
                "comparisons": {
                    "used": len(usage.comparison_timestamps),
                    "limit": max_comparisons,
                    "remaining": max(0, max_comparisons - len(usage.comparison_timestamps)),
                },
                "storage_bytes": {
                    "used": usage.uploaded_bytes,
                    "limit": self.max_storage_bytes,
                    "remaining": max(0, self.max_storage_bytes - usage.uploaded_bytes),
                },
            }

    def reset_usage(self, license_id: str) -> None:
        """Resets all usage counters for a given license (for tests and session resets)."""
        with self._lock:
            if license_id in self._usage:
                del self._usage[license_id]


# Global manager instance
quota_manager = QuotaManager()
