"""
tests/test_resilience_and_recovery.py
=====================================
Verification suite for P3.3:
1. Bounded async retries with exponential backoff and jitter (retry_transient_async).
2. Fail-fast on non-transient domain errors vs retries on transient errors.
3. Deadline enforcement for retries.
4. Tenant-scoped durable idempotency store (replay, in-progress detection, conflict on payload divergence).
5. Interrupted job restart recovery for processing/deleting documents.
6. API HTTP status code mapping for domain and provider errors.
"""
from __future__ import annotations

import asyncio
import os
import sqlite3
import tempfile
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.resilience import (
    ExtractionError,
    IdempotencyConflictError,
    IdempotencyInProgressError,
    IdempotencyStore,
    InvalidDocumentError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ResourceLimitError,
    retry_transient_async,
)
from src.main import create_app
from src.services.container import RealDocumentService, ServiceContainer


# ─────────────────────────────────────────────────────────────────
# 1. Bounded Retries & Backoff Tests
# ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_retry_transient_async_success_after_transient_errors():
    """Verify function retries transient errors and succeeds when a later attempt succeeds."""
    call_count = 0

    async def flaky_operation():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ProviderRateLimitError("Rate limit hit")
        return "success_val"

    result = await retry_transient_async(
        flaky_operation,
        attempts=4,
        base_delay=0.01,
        max_delay=0.05,
    )

    assert result == "success_val"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_transient_async_fails_fast_on_non_transient():
    """Verify non-transient domain errors (e.g. InvalidDocumentError) fail immediately without retrying."""
    call_count = 0

    async def bad_document_operation():
        nonlocal call_count
        call_count += 1
        raise InvalidDocumentError("Invalid PDF header")

    with pytest.raises(InvalidDocumentError, match="Invalid PDF header"):
        await retry_transient_async(
            bad_document_operation,
            attempts=5,
            base_delay=0.01,
        )

    # Must fail on the very first attempt
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_transient_async_exhausts_retries():
    """Verify function raises the underlying exception after max attempts is reached."""
    call_count = 0

    async def persistent_failure():
        nonlocal call_count
        call_count += 1
        raise ProviderUnavailableError("Provider offline")

    with pytest.raises(ProviderUnavailableError, match="Provider offline"):
        await retry_transient_async(
            persistent_failure,
            attempts=3,
            base_delay=0.01,
            max_delay=0.02,
        )

    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_transient_async_deadline_exceeded():
    """Verify deadline stops retries and raises TimeoutError."""
    call_count = 0

    async def slow_retried_operation():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.04)
        raise ProviderTimeoutError("Upstream timeout")

    with pytest.raises(TimeoutError, match="Cumulative retry deadline"):
        await retry_transient_async(
            slow_retried_operation,
            attempts=10,
            base_delay=0.05,
            deadline_seconds=0.05,
        )


# ─────────────────────────────────────────────────────────────────
# 2. Idempotency Store Tests
# ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_idempotency_store_lifecycle_and_replay():
    """Verify idempotency record acquisition, completion, and exact payload replay."""
    store = IdempotencyStore(ttl_seconds=60.0)
    tenant = "tenant-fintech-1"
    key = "req-idem-001"
    payload = b"Sample document bytes for invoice #1001"
    payload_hash = store.compute_payload_hash(payload)

    # 1. First attempt: check_and_start acquires key
    rec = await store.check_and_start(
        tenant_id=tenant,
        operation="upload",
        key=key,
        payload_hash=payload_hash,
    )
    assert rec is None, "First attempt must return None (indicating fresh execution)"

    # 2. Mark completed with response data
    response_payload = {"doc_id": "doc-invoice-1001", "status": "indexed"}
    await store.complete(
        tenant_id=tenant,
        operation="upload",
        key=key,
        response_code=201,
        response_body=response_payload,
    )

    # 3. Duplicate request with identical payload returns cached response
    rec_cached = await store.check_and_start(
        tenant_id=tenant,
        operation="upload",
        key=key,
        payload_hash=payload_hash,
    )
    assert rec_cached is not None
    assert rec_cached.status == "completed"
    assert rec_cached.response_body == response_payload
    assert rec_cached.response_code == 201


@pytest.mark.asyncio
async def test_idempotency_store_conflict_on_divergent_payload():
    """Verify reuse of same Idempotency-Key with different payload raises IdempotencyConflictError."""
    store = IdempotencyStore(ttl_seconds=60.0)
    tenant = "tenant-fintech-1"
    key = "req-idem-002"
    hash_a = store.compute_payload_hash(b"Document Version A")
    hash_b = store.compute_payload_hash(b"Document Version B")

    await store.check_and_start(
        tenant_id=tenant,
        operation="upload",
        key=key,
        payload_hash=hash_a,
    )
    await store.complete(
        tenant_id=tenant,
        operation="upload",
        key=key,
        response_code=200,
        response_body={"doc_id": "doc-a"},
    )

    with pytest.raises(IdempotencyConflictError, match="different request payload"):
        await store.check_and_start(
            tenant_id=tenant,
            operation="upload",
            key=key,
            payload_hash=hash_b,
        )


@pytest.mark.asyncio
async def test_idempotency_store_in_progress_rejection():
    """Verify concurrent requests with same key while operation is in-progress raise InProgress error."""
    store = IdempotencyStore(ttl_seconds=60.0)
    tenant = "tenant-fintech-1"
    key = "req-idem-003"
    hash_val = store.compute_payload_hash(b"Document Payload")

    # Start first request
    await store.check_and_start(
        tenant_id=tenant,
        operation="upload",
        key=key,
        payload_hash=hash_val,
    )

    # Second concurrent request arrives before first finishes
    with pytest.raises(IdempotencyInProgressError, match="currently in progress"):
        await store.check_and_start(
            tenant_id=tenant,
            operation="upload",
            key=key,
            payload_hash=hash_val,
        )


@pytest.mark.asyncio
async def test_idempotency_store_tenant_isolation():
    """Verify identical keys from different tenants do not conflict."""
    store = IdempotencyStore(ttl_seconds=60.0)
    key = "shared-key-123"
    hash_val = store.compute_payload_hash(b"Same bytes")

    # Tenant 1 acquires and completes
    await store.check_and_start(
        tenant_id="tenant-alpha",
        operation="upload",
        key=key,
        payload_hash=hash_val,
    )
    await store.complete(
        tenant_id="tenant-alpha",
        operation="upload",
        key=key,
        response_code=200,
        response_body={"tenant": "alpha"},
    )

    # Tenant 2 can acquire same key without conflict
    rec2 = await store.check_and_start(
        tenant_id="tenant-beta",
        operation="upload",
        key=key,
        payload_hash=hash_val,
    )
    assert rec2 is None, "Tenant 2 must have an independent namespace for idempotency keys"


@pytest.mark.asyncio
async def test_idempotency_store_release_on_error():
    """Verify failing operations can release their idempotency lock so retries can proceed."""
    store = IdempotencyStore(ttl_seconds=60.0)
    tenant = "tenant-fintech-1"
    key = "req-idem-004"
    hash_val = store.compute_payload_hash(b"Payload")

    await store.check_and_start(
        tenant_id=tenant,
        operation="upload",
        key=key,
        payload_hash=hash_val,
    )
    # Simulate failed operation -> release lock
    await store.release_on_error(
        tenant_id=tenant,
        operation="upload",
        key=key,
    )

    # Retry should now succeed in starting
    rec_after = await store.check_and_start(
        tenant_id=tenant,
        operation="upload",
        key=key,
        payload_hash=hash_val,
    )
    assert rec_after is None, "Lock must be released after failure"


# ─────────────────────────────────────────────────────────────────
# 3. Interrupted Document Startup Recovery
# ─────────────────────────────────────────────────────────────────

def test_stale_processing_and_deleting_documents_recovered_on_startup():
    """Verify that documents left in 'processing' or 'deleting' state from crash/restart are reconciled."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_db_path = tf.name

    try:
        # Initialize schema and seed stale records
        with sqlite3.connect(temp_db_path) as conn:
            conn.execute("""
                CREATE TABLE documents (
                    doc_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    status TEXT NOT NULL,
                    page_count INTEGER DEFAULT 0,
                    chunk_count INTEGER DEFAULT 0,
                    is_scanned BOOLEAN DEFAULT 0,
                    language TEXT DEFAULT 'en',
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    raw_bytes BLOB,
                    content_type TEXT DEFAULT 'application/pdf',
                    byte_size INTEGER DEFAULT 0,
                    sha256 TEXT DEFAULT '',
                    error_code TEXT
                )
            """)
            conn.execute("""
                INSERT INTO documents (doc_id, tenant_id, filename, status)
                VALUES
                    ('doc-stale-proc', 't1', 'file1.pdf', 'processing'),
                    ('doc-stale-del', 't1', 'file2.pdf', 'deleting'),
                    ('doc-ready', 't1', 'file3.pdf', 'ready')
            """)
            conn.commit()

        # Initialize RealDocumentService on this database (triggers _load_docs recovery)
        service = RealDocumentService(orchestrator=None, db_path=temp_db_path)

        # Inspect DB state
        with sqlite3.connect(temp_db_path) as conn:
            rows = conn.execute("SELECT doc_id, status, error_code FROM documents ORDER BY doc_id").fetchall()

        doc_map = {row[0]: (row[1], row[2]) for row in rows}

        # Interrupted processing document -> marked failed
        assert doc_map["doc-stale-proc"][0] == "failed"
        assert doc_map["doc-stale-proc"][1] == "STALE_PROCESSING_INTERRUPTED"

        # Interrupted deleting document -> marked delete_failed
        assert doc_map["doc-stale-del"][0] == "delete_failed"
        assert doc_map["doc-stale-del"][1] == "STALE_DELETION_INTERRUPTED"

        # Ready document remains ready
        assert doc_map["doc-ready"][0] == "ready"

    finally:
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except OSError:
                pass


# ─────────────────────────────────────────────────────────────────
# 4. Exception Handlers Status Code Mapping
# ─────────────────────────────────────────────────────────────────

def test_api_resilience_exception_handlers():
    """Verify HTTP status codes and headers returned by FastAPI exception handlers for typed errors."""
    with patch.object(ServiceContainer, "startup", new_callable=AsyncMock):
        app = create_app()

        # Define temporary routes raising each domain error to test the handlers directly
        @app.get("/test/invalid-doc")
        async def raise_invalid_doc():
            raise InvalidDocumentError("Malformed header")

        @app.get("/test/conflict")
        async def raise_conflict():
            raise IdempotencyConflictError("Payload mismatch")

        @app.get("/test/in-progress")
        async def raise_in_progress():
            raise IdempotencyInProgressError("Operation running")

        @app.get("/test/extraction-error")
        async def raise_extraction_error():
            raise ExtractionError("Corrupted font streams")

        @app.get("/test/resource-limit")
        async def raise_resource_limit():
            raise ResourceLimitError("Max memory exceeded")

        @app.get("/test/provider-timeout")
        async def raise_provider_timeout():
            raise ProviderTimeoutError("LLM socket timeout")

        @app.get("/test/provider-ratelimit")
        async def raise_provider_ratelimit():
            raise ProviderRateLimitError("Rate limit exceeded")

        @app.get("/test/provider-unavailable")
        async def raise_provider_unavailable():
            raise ProviderUnavailableError("503 service down")

        auth_headers = {"Authorization": "Bearer dev-token"}
        with TestClient(app) as client:
            r1 = client.get("/test/invalid-doc", headers=auth_headers)
            assert r1.status_code == 400
            assert "Malformed header" in r1.json()["detail"]

            r2 = client.get("/test/conflict", headers=auth_headers)
            assert r2.status_code == 409
            assert "Payload mismatch" in r2.json()["detail"]

            r3 = client.get("/test/in-progress", headers=auth_headers)
            assert r3.status_code == 409
            assert r3.headers.get("Retry-After") == "1"

            r4 = client.get("/test/extraction-error", headers=auth_headers)
            assert r4.status_code == 422
            assert "Corrupted font streams" in r4.json()["detail"]

            r5 = client.get("/test/resource-limit", headers=auth_headers)
            assert r5.status_code == 413

            r6 = client.get("/test/provider-timeout", headers=auth_headers)
            assert r6.status_code == 504

            r7 = client.get("/test/provider-ratelimit", headers=auth_headers)
            assert r7.status_code == 429
            assert r7.headers.get("Retry-After") == "5"

            r8 = client.get("/test/provider-unavailable", headers=auth_headers)
            assert r8.status_code == 503
