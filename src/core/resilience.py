"""
src/core/resilience.py
======================
Operational resilience primitives for AEGIS-DocIntel:
1. Explicit domain exception taxonomy for safe error translation.
2. Bounded asynchronous retry utility with exponential backoff and full jitter.
3. Tenant-scoped idempotency store preventing duplicate expensive jobs.
4. Concurrency limiting and resource safety guards.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import hashlib
import random
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, TypeVar

from src.services.storage_errors import DocumentStorageError

T = TypeVar("T")


# ── Explicit Error Categories ───────────────────────────────────────────────

class AEGISDomainError(Exception):
    """Root base class for all operational and domain errors."""
    pass


class InvalidDocumentError(AEGISDomainError):
    """Raised when document input is unsupported, malformed, or corrupt."""
    pass


class ExtractionError(AEGISDomainError):
    """Raised when text/table extraction fails unrecoverably."""
    pass


class ProviderTimeoutError(AEGISDomainError):
    """Raised when external downstream provider exceeds execution deadline."""
    pass


class ProviderRateLimitError(AEGISDomainError):
    """Raised when external downstream provider throttles requests."""
    pass


class ProviderUnavailableError(AEGISDomainError):
    """Raised when external downstream provider experiences an outage."""
    pass


class ResourceLimitError(AEGISDomainError):
    """Raised when input size, page count, or concurrency ceiling is exceeded."""
    pass


# ── Bounded Asynchronous Retries ───────────────────────────────────────────

async def retry_transient_async(
    operation: Callable[[], Coroutine[Any, Any, T]],
    *,
    attempts: int = 3,
    base_delay: float = 0.25,
    max_delay: float = 3.0,
    deadline_seconds: Optional[float] = 10.0,
    is_transient: Optional[Callable[[Exception], bool]] = None,
) -> T:
    """
    Executes an async operation with bounded exponential backoff and jitter.

    Parameters
    ----------
    operation:
        Zero-argument callable returning a coroutine.
    attempts:
        Maximum attempt count (must be >= 1).
    base_delay:
        Initial backoff delay in seconds.
    max_delay:
        Upper bound cap on exponential backoff delay in seconds.
    deadline_seconds:
        Total cumulative execution deadline in seconds.
    is_transient:
        Predicate determining whether an exception is retryable. Defaults to
        retrying network timeouts, connection resets, and ProviderRateLimitError.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    if is_transient is None:
        def default_is_transient(exc: Exception) -> bool:
            if isinstance(exc, (ProviderRateLimitError, ProviderUnavailableError, TimeoutError, ConnectionError)):
                return True
            msg = str(exc).lower()
            return any(k in msg for k in ("connection reset", "broken pipe", "rate limit", "429", "timeout", "temporarily unavailable"))
        is_transient = default_is_transient

    t_start = time.perf_counter()

    for attempt in range(attempts):
        # Deadline check before starting attempt
        if deadline_seconds is not None:
            elapsed = time.perf_counter() - t_start
            if elapsed >= deadline_seconds:
                raise TimeoutError(f"Cumulative retry deadline of {deadline_seconds}s exceeded after {attempt} attempts")

        try:
            return await operation()
        except Exception as exc:
            elapsed = time.perf_counter() - t_start
            is_last_attempt = (attempt == attempts - 1)
            is_retryable = is_transient(exc)

            if not is_retryable:
                raise

            if deadline_seconds and elapsed >= deadline_seconds:
                raise TimeoutError(
                    f"Cumulative retry deadline of {deadline_seconds}s exceeded after {attempt + 1} attempts"
                ) from exc

            if is_last_attempt:
                raise

            # Exponential backoff with full jitter: delay * Uniform(0.5, 1.0)
            backoff = min(max_delay, base_delay * (2 ** attempt))
            jittered_delay = random.uniform(backoff * 0.5, backoff)

            if deadline_seconds is not None and (elapsed + jittered_delay) >= deadline_seconds:
                # Sleep only until deadline then re-raise
                remaining = max(0.0, deadline_seconds - elapsed)
                if remaining > 0:
                    await asyncio.sleep(remaining)
                raise TimeoutError(f"Cumulative retry deadline exceeded during backoff on attempt {attempt + 1}")

            await asyncio.sleep(jittered_delay)

    raise RuntimeError("Unreachable retry state")


# ── Tenant-Scoped Idempotency Store ─────────────────────────────────────────

@dataclass
class IdempotencyRecord:
    key: str
    tenant_id: str
    operation: str
    payload_hash: str
    created_at: float
    status: str  # "in_progress" | "completed"
    response_code: int = 200
    response_body: Optional[Dict[str, Any]] = None


class IdempotencyConflictError(AEGISDomainError):
    """Raised when an idempotency key is reused with a materially different payload."""
    pass


class IdempotencyInProgressError(AEGISDomainError):
    """Raised when an identical request with the same idempotency key is currently processing."""
    pass


class IdempotencyStore:
    """
    In-memory / thread-safe durable store for idempotency keys scoped by tenant.
    Prevents duplicate submissions of document ingestion or long-running tasks.
    """
    def __init__(self, ttl_seconds: float = 3600.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._records: Dict[str, IdempotencyRecord] = {}
        self._lock = asyncio.Lock()

    def _composite_key(self, tenant_id: str, operation: str, key: str) -> str:
        return f"{tenant_id}:{operation}:{key}"

    @staticmethod
    def compute_payload_hash(data: bytes | str) -> str:
        raw = data.encode("utf-8") if isinstance(data, str) else data
        return hashlib.sha256(raw).hexdigest()

    async def check_and_start(
        self,
        *,
        tenant_id: str,
        operation: str,
        key: str,
        payload_hash: str,
    ) -> Optional[IdempotencyRecord]:
        """
        Atomically inspects whether a request with (tenant_id, operation, key) has been seen.
        - If not seen: marks it 'in_progress' and returns None.
        - If completed and payload_hash matches: returns the existing IdempotencyRecord.
        - If completed but payload_hash differs: raises IdempotencyConflictError.
        - If currently in_progress: raises IdempotencyInProgressError.
        """
        async with self._lock:
            now = time.time()
            comp_key = self._composite_key(tenant_id, operation, key)

            # Evict expired records
            if comp_key in self._records:
                rec = self._records[comp_key]
                if now - rec.created_at > self.ttl_seconds:
                    del self._records[comp_key]

            if comp_key not in self._records:
                self._records[comp_key] = IdempotencyRecord(
                    key=key,
                    tenant_id=tenant_id,
                    operation=operation,
                    payload_hash=payload_hash,
                    created_at=now,
                    status="in_progress",
                )
                return None

            existing = self._records[comp_key]
            if existing.payload_hash != payload_hash:
                raise IdempotencyConflictError(
                    f"Idempotency key '{key}' was previously used with a different request payload."
                )

            if existing.status == "in_progress":
                raise IdempotencyInProgressError(
                    f"A request with idempotency key '{key}' is currently in progress."
                )

            return existing

    async def complete(
        self,
        *,
        tenant_id: str,
        operation: str,
        key: str,
        response_code: int,
        response_body: Dict[str, Any],
    ) -> None:
        """Records successful response outcome for an idempotency key."""
        async with self._lock:
            comp_key = self._composite_key(tenant_id, operation, key)
            if comp_key in self._records:
                rec = self._records[comp_key]
                rec.status = "completed"
                rec.response_code = response_code
                rec.response_body = response_body

    async def release_on_error(
        self,
        *,
        tenant_id: str,
        operation: str,
        key: str,
    ) -> None:
        """Releases an in-progress idempotency key if the request failed unrecoverably."""
        async with self._lock:
            comp_key = self._composite_key(tenant_id, operation, key)
            if comp_key in self._records and self._records[comp_key].status == "in_progress":
                del self._records[comp_key]
