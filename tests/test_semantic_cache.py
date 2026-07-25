"""
Tests for src.memory_engine.semantic_cache.SemanticCache.

Repository Audit follow-up, semantic-cache sweep: this component's tenant
scoping (per-tenant dict-keyed FAISS indices) was already correctly
designed -- confirmed here, not merely assumed, by test_cross_tenant_query_
does_not_see_other_tenants_entries -- but two independent correctness bugs
were found by actually exercising the code, not by inspection:

1. invalidate_by_doc() filtered the entries list correctly but rebuilt the
   FAISS index as *empty* without re-adding the surviving entries'
   embeddings, permanently desynchronizing the two data structures. Net
   effect: after the first document delete/reindex touching a tenant's
   cache, every subsequent query for that tenant misses regardless of
   whether it matches a still-valid surviving entry -- silently defeating
   the cache's entire purpose for the rest of that tenant's session.

2. TTL-expired entries were skipped when returning a query result but
   never actually removed from either the entries list or the FAISS
   index, so they accumulated indefinitely (unbounded memory growth) and
   permanently occupied search-result slots that could otherwise surface
   a still-valid entry.

Both are exercised directly below by constructing the actual failure
sequence and checking the real, observed behavior -- not by asserting
internal implementation details alone.
"""
from __future__ import annotations

import time

import numpy as np
import pytest

from src.memory_engine.semantic_cache import SemanticCache

DIM = 1024


def _rand_embedding() -> np.ndarray:
    return np.random.rand(DIM).astype(np.float32)


@pytest.mark.asyncio
async def test_exact_embedding_hits_after_caching():
    """Baseline sanity check before the more targeted bug-reproduction
    tests below: a query with the exact cached embedding must hit."""
    cache = SemanticCache(redis_client=None)
    emb = _rand_embedding()
    await cache.cache_response("q1", emb, {"answer": "a1"}, tenant_id="t1", doc_ids=["docA"])

    hit = await cache.query_cache(emb, tenant_id="t1", doc_ids=["docA"])
    assert hit == {"answer": "a1"}


@pytest.mark.asyncio
async def test_cross_tenant_query_does_not_see_other_tenants_entries():
    """Confirms the per-tenant dict-keyed index design actually isolates
    tenants -- this was found correctly designed, not broken, but is worth
    a real test rather than only a code-review conclusion, especially
    given how many places elsewhere in this codebase had a tenant_id
    parameter that looked like it enforced isolation but didn't."""
    cache = SemanticCache(redis_client=None)
    emb = _rand_embedding()
    await cache.cache_response("q1", emb, {"answer": "tenant-a-secret"}, tenant_id="tenant-a", doc_ids=["docA"])

    hit_wrong_tenant = await cache.query_cache(emb, tenant_id="tenant-b", doc_ids=["docA"])
    assert hit_wrong_tenant is None, (
        "Tenant B's query matched Tenant A's cached entry by exact embedding "
        "similarity alone, with no tenant boundary enforced."
    )

    hit_right_tenant = await cache.query_cache(emb, tenant_id="tenant-a", doc_ids=["docA"])
    assert hit_right_tenant == {"answer": "tenant-a-secret"}


@pytest.mark.asyncio
async def test_invalidation_does_not_desync_index_from_entries():
    """The primary bug this session found and fixed: invalidating one
    document's cache entries must not silently break queries for a
    *different*, still-valid, surviving entry belonging to the same
    tenant."""
    cache = SemanticCache(redis_client=None)
    emb_a = _rand_embedding()
    emb_b = _rand_embedding()
    await cache.cache_response("q_a", emb_a, {"answer": "a"}, tenant_id="t1", doc_ids=["docA"])
    await cache.cache_response("q_b", emb_b, {"answer": "b"}, tenant_id="t1", doc_ids=["docB"])

    removed = await cache.invalidate_by_doc("docA", tenant_id="t1")
    assert removed == 1

    hit_survivor = await cache.query_cache(emb_b, tenant_id="t1", doc_ids=["docB"])
    assert hit_survivor == {"answer": "b"}, (
        "A surviving cache entry became unqueryable after invalidating an "
        "unrelated document's entry -- the entries list and the FAISS "
        "index desynchronized."
    )

    # And the invalidated entry itself must genuinely be gone, not merely
    # coincidentally still matching.
    hit_invalidated = await cache.query_cache(emb_a, tenant_id="t1", doc_ids=["docA"])
    assert hit_invalidated is None


@pytest.mark.asyncio
async def test_invalidate_all_entries_leaves_empty_but_consistent_state():
    """Edge case at the other end from the primary bug: invalidating every
    entry for a tenant (survivors == 0) must leave a valid, queryable-but-
    empty state, not raise on the now-empty vstack."""
    cache = SemanticCache(redis_client=None)
    emb = _rand_embedding()
    await cache.cache_response("q1", emb, {"answer": "a1"}, tenant_id="t1", doc_ids=["docA"])

    removed = await cache.invalidate_by_doc("docA", tenant_id="t1")
    assert removed == 1
    assert cache._indices["t1"].ntotal == 0
    assert cache._entries["t1"] == []

    # A subsequent cache_response for the same tenant must still work
    # normally against the now-empty, correctly-reset index.
    emb2 = _rand_embedding()
    await cache.cache_response("q2", emb2, {"answer": "a2"}, tenant_id="t1", doc_ids=["docC"])
    hit = await cache.query_cache(emb2, tenant_id="t1", doc_ids=["docC"])
    assert hit == {"answer": "a2"}


@pytest.mark.asyncio
async def test_expired_entries_are_purged_not_accumulated():
    """The secondary bug this session found: TTL-expired entries must
    actually be removed (bounding memory and search-slot usage), not just
    skipped-over at query time forever."""
    cache = SemanticCache(redis_client=None)
    cache.ttl = 0.05  # short TTL so the test doesn't need to sleep long

    emb_old = _rand_embedding()
    await cache.cache_response("old", emb_old, {"answer": "old"}, tenant_id="t1", doc_ids=["docA"])
    assert cache._indices["t1"].ntotal == 1

    time.sleep(0.1)  # let the first entry expire

    emb_new = _rand_embedding()
    await cache.cache_response("new", emb_new, {"answer": "new"}, tenant_id="t1", doc_ids=["docB"])

    assert len(cache._entries["t1"]) == 1, (
        "Expired entry was not purged on the next cache write -- it "
        "accumulates indefinitely instead of being bounded."
    )
    assert cache._indices["t1"].ntotal == 1
    assert cache._entries["t1"][0]["question"] == "new"


@pytest.mark.asyncio
async def test_purge_expired_public_method():
    """The public purge_expired() entry point (for a scheduled maintenance
    task, independent of waiting for the next cache_response() write) must
    work standalone."""
    cache = SemanticCache(redis_client=None)
    cache.ttl = 0.05

    emb = _rand_embedding()
    await cache.cache_response("q1", emb, {"answer": "a1"}, tenant_id="t1", doc_ids=["docA"])
    time.sleep(0.1)

    removed = await cache.purge_expired("t1")
    assert removed == 1
    assert cache._entries["t1"] == []
    assert cache._indices["t1"].ntotal == 0


@pytest.mark.asyncio
async def test_purge_expired_on_tenant_with_no_entries_is_a_noop():
    """Calling purge on a tenant with no cache entries at all must not
    raise -- a plausible edge case for a newly-onboarded tenant."""
    cache = SemanticCache(redis_client=None)
    removed = await cache.purge_expired("brand-new-tenant")
    assert removed == 0
