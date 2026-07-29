"""
System Circuit Breakers & Resilience Manager (Tasks F-6, A-6).

Stateful circuit breaker implementation for external service dependencies (LLM APIs,
Vector DB, Memory Storage) with automatic fallback execution.
"""

from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Callable, Any, Dict, Optional, TypeVar, Coroutine


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(Exception):
    """Raised when a call is made to an open circuit breaker without a fallback."""
    pass


T = TypeVar("T")


class CircuitBreaker:
    """
    Monitors execution failure rates and trips open when failures exceed threshold.
    Auto-recovers to HALF_OPEN after recovery_timeout.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 5.0,
        success_threshold: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
        self.last_failure_time = 0.0

    def _check_state(self) -> None:
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.last_state_change = now

    def record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_state_change = time.time()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
            if self.failure_count >= self.failure_threshold or self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.last_state_change = time.time()

    async def execute(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        fallback: Optional[Callable[..., Coroutine[Any, Any, T]]] = None,
        **kwargs: Any,
    ) -> T:
        self._check_state()

        if self.state == CircuitState.OPEN:
            if fallback:
                return await fallback(*args, **kwargs)
            raise CircuitBreakerOpenException(
                f"Circuit breaker '{self.name}' is OPEN and no fallback was provided."
            )

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            if fallback:
                return await fallback(*args, **kwargs)
            raise


class CircuitBreakerManager:
    """Central registry of circuit breakers across infrastructure dependencies."""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 5.0,
    ) -> CircuitBreaker:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
            )
        return self._breakers[name]

    def reset_all(self) -> None:
        for b in self._breakers.values():
            b.state = CircuitState.CLOSED
            b.failure_count = 0
            b.success_count = 0
