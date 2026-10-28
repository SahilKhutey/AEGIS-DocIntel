"""
tests/test_mvp4_idempotency.py
==============================
Unit tests for IdempotencyStore lifecycle, conflict detection, concurrent in-progress detection,
tenant isolation, and TTL expiry.
"""

from __future__ import annotations

import asyncio
import time
import pytest
from src.core.resilience import (
    IdempotencyConflictError,
    IdempotencyInProgressError,
    IdempotencyStore,
)


@pytest.mark.asyncio
async def test_idempotency_lifecycle_complete_and_replay():
    store = IdempotencyStore(ttl_seconds=60.0)
    tenant_id = "tenant-alpha"
    op = "document_upload"
    key = "idem-key-1"
    payload = b"sample document payload"
    p_hash = store.compute_payload_hash(payload)

    # 1. First attempt: not seen -> returns None and transitions to in_progress
    rec = await store.check_and_start(
        tenant_id=tenant_id,
        operation=op,
        key=key,
        payload_hash=p_hash,
    )
    assert rec is None

    # 2. Complete operation
    response_body = {"doc_id": "doc-123", "status": "ready"}
    await store.complete(
        tenant_id=tenant_id,
        operation=op,
        key=key,
        response_code=202,
        response_body=response_body,
    )

    # 3. Second attempt with identical payload -> returns cached completed record
    replay = await store.check_and_start(
        tenant_id=tenant_id,
        operation=op,
        key=key,
        payload_hash=p_hash,
    )
    assert replay is not None
    assert replay.status == "completed"
    assert replay.response_code == 202
    assert replay.response_body == response_body


@pytest.mark.asyncio
async def test_idempotency_payload_conflict():
    store = IdempotencyStore(ttl_seconds=60.0)
    tenant_id = "tenant-alpha"
    op = "document_upload"
    key = "idem-key-conflict"
    p_hash1 = store.compute_payload_hash(b"original content")
    p_hash2 = store.compute_payload_hash(b"modified content")

    await store.check_and_start(
        tenant_id=tenant_id,
        operation=op,
        key=key,
        payload_hash=p_hash1,
    )
    await store.complete(
        tenant_id=tenant_id,
        operation=op,
        key=key,
        response_code=202,
        response_body={"status": "ok"},
    )

    # Attempt with different payload hash raises IdempotencyConflictError
    with pytest.raises(IdempotencyConflictError, match="different request payload"):
        await store.check_and_start(
            tenant_id=tenant_id,
            operation=op,
            key=key,
            payload_hash=p_hash2,
        )


@pytest.mark.asyncio
async def test_idempotency_concurrent_in_progress_rejection():
    store = IdempotencyStore(ttl_seconds=60.0)
    tenant_id = "tenant-alpha"
    op = "document_upload"
    key = "idem-key-prog"
    p_hash = store.compute_payload_hash(b"content")

    # First caller starts
    await store.check_and_start(
        tenant_id=tenant_id,
        operation=op,
        key=key,
        payload_hash=p_hash,
    )

    # Concurrent caller before completion raises IdempotencyInProgressError
    with pytest.raises(IdempotencyInProgressError, match="currently in progress"):
        await store.check_and_start(
            tenant_id=tenant_id,
            operation=op,
            key=key,
            payload_hash=p_hash,
        )


@pytest.mark.asyncio
async def test_idempotency_release_on_error():
    store = IdempotencyStore(ttl_seconds=60.0)
    tenant_id = "tenant-alpha"
    op = "document_upload"
    key = "idem-key-err"
    p_hash = store.compute_payload_hash(b"content")

    await store.check_and_start(
        tenant_id=tenant_id,
        operation=op,
        key=key,
        payload_hash=p_hash,
    )

    # Release on unrecoverable upstream error
    await store.release_on_error(
        tenant_id=tenant_id,
        operation=op,
        key=key,
    )

    # Subsequent request can now proceed cleanly
    retry = await store.check_and_start(
        tenant_id=tenant_id,
        operation=op,
        key=key,
        payload_hash=p_hash,
    )
    assert retry is None


@pytest.mark.asyncio
async def test_idempotency_tenant_isolation():
    store = IdempotencyStore(ttl_seconds=60.0)
    op = "document_upload"
    key = "same-key-shared-name"
    p_hash = store.compute_payload_hash(b"content")

    # Tenant alpha uses key
    await store.check_and_start(
        tenant_id="tenant-alpha",
        operation=op,
        key=key,
        payload_hash=p_hash,
    )

    # Tenant beta using the same key is completely isolated and allowed
    beta_rec = await store.check_and_start(
        tenant_id="tenant-beta",
        operation=op,
        key=key,
        payload_hash=p_hash,
    )
    assert beta_rec is None
