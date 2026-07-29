"""
Unit tests for System Circuit Breakers & Resilience Manager (Tasks F-6, A-6).
"""

import asyncio
import pytest
from src.observability.circuit_breaker import (
    CircuitBreaker, CircuitBreakerManager, CircuitState, CircuitBreakerOpenException
)


@pytest.mark.asyncio
async def test_circuit_breaker_closed_state_success():
    cb = CircuitBreaker("test_service", failure_threshold=2)

    async def mock_primary():
        return "primary_ok"

    res = await cb.execute(mock_primary)
    assert res == "primary_ok"
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_trips_to_open_on_failures():
    cb = CircuitBreaker("test_service", failure_threshold=2, recovery_timeout=1.0)

    async def mock_failing():
        raise RuntimeError("Service unavailable")

    async def mock_fallback():
        return "fallback_response"

    # Call 1: fails
    res1 = await cb.execute(mock_failing, fallback=mock_fallback)
    assert res1 == "fallback_response"
    assert cb.state == CircuitState.CLOSED

    # Call 2: fails -> trips circuit breaker to OPEN
    res2 = await cb.execute(mock_failing, fallback=mock_fallback)
    assert res2 == "fallback_response"
    assert cb.state == CircuitState.OPEN

    # Call 3: circuit is OPEN -> directly uses fallback without executing primary
    res3 = await cb.execute(mock_failing, fallback=mock_fallback)
    assert res3 == "fallback_response"


@pytest.mark.asyncio
async def test_circuit_breaker_raises_when_open_and_no_fallback():
    cb = CircuitBreaker("test_service", failure_threshold=1)

    async def mock_failing():
        raise RuntimeError("Fail")

    with pytest.raises(RuntimeError):
        await cb.execute(mock_failing)

    assert cb.state == CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpenException):
        await cb.execute(mock_failing)


@pytest.mark.asyncio
async def test_circuit_breaker_manager_registry():
    mgr = CircuitBreakerManager()
    b1 = mgr.get_breaker("llm_api")
    b2 = mgr.get_breaker("llm_api")
    assert b1 is b2

    b1.state = CircuitState.OPEN
    mgr.reset_all()
    assert b1.state == CircuitState.CLOSED
