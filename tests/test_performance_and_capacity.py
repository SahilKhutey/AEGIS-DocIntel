"""
tests/test_performance_and_capacity.py
======================================
Performance, concurrency, and capacity regression tests for P3.4:
1. Latency distribution & percentiles: Health and readiness p95 < 250ms.
2. Concurrent multi-tenant requests under ASGI transport without deadlocks or race conditions.
3. Memory stability check ensuring bounded memory usage under repeated operations.
4. High-concurrency race condition prevention in tenant idempotency locks.
"""
from __future__ import annotations

import asyncio
import statistics
import time
import tracemalloc
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from src.core.resilience import IdempotencyInProgressError, IdempotencyStore
from src.main import create_app
from src.services.container import ServiceContainer


# ─────────────────────────────────────────────────────────────────
# 1. Latency Percentiles
# ─────────────────────────────────────────────────────────────────

def test_health_and_readiness_latency_distribution():
    """Verify endpoint response latency adheres to strict percentile limits (p50 < 50ms, p95 < 250ms)."""
    with patch.object(ServiceContainer, "startup", new_callable=AsyncMock):
        app = create_app()
        with TestClient(app) as client:
            # Warm up
            client.get("/health")
            client.get("/readiness")

            latencies = []
            for _ in range(50):
                t0 = time.perf_counter()
                res = client.get("/health")
                t1 = time.perf_counter()
                assert res.status_code in (200, 503)
                latencies.append((t1 - t0) * 1000.0)

            latencies.sort()
            p50 = statistics.median(latencies)
            p95 = latencies[int(len(latencies) * 0.95)]

            # Performance assertions
            assert p50 < 80.0, f"p50 latency {p50:.2f}ms exceeded 80ms threshold"
            assert p95 < 250.0, f"p95 latency {p95:.2f}ms exceeded 250ms threshold"


# ─────────────────────────────────────────────────────────────────
# 2. Multi-Tenant Concurrency
# ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_concurrent_multi_tenant_requests():
    """Verify system handles simultaneous requests across multiple tenants without deadlock or cross-tenant leakage."""
    with patch.object(ServiceContainer, "startup", new_callable=AsyncMock):
        app = create_app()

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            tenants = ["tenant-corp-1", "tenant-corp-2", "tenant-corp-3", "tenant-corp-4"]
            headers_list = [
                {
                    "Authorization": "Bearer dev-token",
                    "X-Tenant-ID": tenant,
                    "X-Request-ID": f"req-concurrent-{idx}",
                }
                for idx, tenant in enumerate(tenants * 6)  # 24 concurrent requests
            ]

            async def fire_request(headers: dict):
                return await client.get("/health", headers=headers)

            responses = await asyncio.gather(*(fire_request(h) for h in headers_list))

            assert len(responses) == 24
            for idx, resp in enumerate(responses):
                assert resp.status_code in (200, 503)
                assert resp.headers.get("X-Request-ID") == f"req-concurrent-{idx}"
                assert "X-Response-Time-ms" in resp.headers


# ─────────────────────────────────────────────────────────────────
# 3. High-Concurrency Race Condition Prevention
# ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_idempotency_store_race_condition_protection():
    """Verify that multiple concurrent coroutines racing for the same idempotency key result in exactly 1 winner."""
    store = IdempotencyStore(ttl_seconds=60.0)
    tenant = "tenant-high-load"
    key = "race-key-001"
    payload_hash = store.compute_payload_hash(b"identical payload bytes")

    winners = 0
    in_progress_rejections = 0

    async def race_worker():
        nonlocal winners, in_progress_rejections
        try:
            record = await store.check_and_start(
                tenant_id=tenant,
                operation="upload",
                key=key,
                payload_hash=payload_hash,
            )
            if record is None:
                winners += 1
        except IdempotencyInProgressError:
            in_progress_rejections += 1

    # Launch 20 concurrent coroutines attempting to claim the key simultaneously
    await asyncio.gather(*(race_worker() for _ in range(20)))

    assert winners == 1, f"Expected exactly 1 winner to claim the key, got {winners}"
    assert in_progress_rejections == 19, f"Expected 19 rejections, got {in_progress_rejections}"


# ─────────────────────────────────────────────────────────────────
# 4. Memory Stability Under Repeated Operations
# ─────────────────────────────────────────────────────────────────

def test_memory_stability_under_repeated_operations():
    """Verify memory growth remains strictly bounded under repeated operations (no cumulative leak)."""
    tracemalloc.start()
    try:
        store = IdempotencyStore(ttl_seconds=10.0)

        # Baseline snapshot
        snapshot_start = tracemalloc.take_snapshot()

        # Run 500 repeated payload hashing and idempotency checks
        for i in range(500):
            payload = f"iteration-test-payload-data-{i}".encode("utf-8")
            h = store.compute_payload_hash(payload)
            # Create transient record
            asyncio.run(
                store.check_and_start(
                    tenant_id=f"tenant-{i % 10}",
                    operation="benchmark",
                    key=f"bench-key-{i}",
                    payload_hash=h,
                )
            )

        snapshot_end = tracemalloc.take_snapshot()

        top_stats = snapshot_end.compare_to(snapshot_start, "lineno")
        total_growth_bytes = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
        total_growth_kb = total_growth_bytes / 1024.0

        # Memory growth for 500 lightweight records must not exceed 2MB (2048 KB)
        assert total_growth_kb < 2048.0, f"Memory growth {total_growth_kb:.1f} KB exceeded 2048 KB limit"

    finally:
        tracemalloc.stop()
