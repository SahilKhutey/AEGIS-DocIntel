"""
Additional tests for src.engines.memory.cache.CacheManager, extending
tests/test_memory.py's existing (shallow) coverage.

Repository Audit follow-up, memory-engine cache sweep. Two things were
checked here, with opposite results -- both worth recording precisely:

1. The ARC (Adaptive Replacement Cache) policy's ghost-list mechanism
   (B1/B2) and its adaptive parameter p were suspected buggy on a first,
   too-simple reproduction (an all-unique-key insertion workload, under
   which B1/B2 legitimately never populate per the real Megiddo/Modha
   algorithm -- ghost lists only matter for *repeated* access patterns,
   which a pure-unique-key workload never exercises). Re-derived the
   actual algorithm and re-tested against a workload that should trigger
   REPLACE() and populate a ghost list; it did, correctly, and a
   subsequent "ghost hit" correctly adapted p and promoted the item. This
   turned out to be a correctly-implemented algorithm -- recorded here as
   a verified negative result via test_arc_* below, not merely a claim.

2. The LFU policy's eviction tie-break (frequency, then last_access_order)
   had a real bug: _lfu_get() bumped an entry's frequency on a cache hit
   but never updated its last_access_order, so a frequency tie between
   two entries was broken using their *insertion* order regardless of
   which had actually been read more recently -- the entry accessed most
   recently could be evicted ahead of one not read in longer, purely
   because it happened to be inserted earlier. Fixed in both _lfu_get()
   and _lfu_put()'s update-existing-key path; test_lfu_tiebreak_prefers_
   more_recently_accessed_entry reproduces the exact failing sequence.
"""
from __future__ import annotations

from src.engines.memory.cache import CacheManager, CachePolicy


def test_lfu_tiebreak_prefers_more_recently_accessed_entry():
    """The primary bug this sweep found: among entries tied on frequency,
    the one accessed longer ago must be evicted, not the one accessed
    most recently."""
    mgr = CacheManager(capacity=2, policy=CachePolicy.LFU)
    mgr.put("x", 1)
    mgr.put("y", 2)

    mgr.get("y")  # y: frequency 2
    mgr.get("x")  # x: frequency 2 -- tied with y, but x accessed more recently

    mgr.put("z", 3)  # forces an eviction between the tied x/y

    assert "x" in mgr.cache, (
        "The more-recently-accessed of two frequency-tied entries was evicted "
        "-- the tie-break is using stale insertion-time ordering instead of "
        "actual last-access ordering."
    )
    assert "y" not in mgr.cache


def test_lfu_get_updates_last_access_order():
    """Directly confirms the fix's mechanism, not just its downstream
    eviction effect: a get() must actually advance last_access_order."""
    mgr = CacheManager(capacity=3, policy=CachePolicy.LFU)
    mgr.put("a", 1)
    order_at_insert = mgr.cache["a"].last_access_order

    mgr.get("a")
    order_after_get = mgr.cache["a"].last_access_order

    assert order_after_get > order_at_insert, (
        "get() did not advance last_access_order -- it only updated frequency."
    )


def test_lfu_put_on_existing_key_updates_last_access_order():
    """The same gap existed in _lfu_put's update-existing-key path,
    independent of _lfu_get -- confirmed fixed separately."""
    mgr = CacheManager(capacity=3, policy=CachePolicy.LFU)
    mgr.put("a", 1)
    order_at_insert = mgr.cache["a"].last_access_order

    mgr.put("a", 999)  # update existing key's value
    order_after_put = mgr.cache["a"].last_access_order

    assert order_after_put > order_at_insert
    assert mgr.cache["a"].value == 999


def test_lfu_strict_frequency_difference_still_respected():
    """Regression guard: the fix must not break the primary, non-tied case
    -- a strictly lower-frequency entry must still be evicted first
    regardless of recency."""
    mgr = CacheManager(capacity=2, policy=CachePolicy.LFU)
    mgr.put("rare", 1)
    mgr.put("common", 2)
    for _ in range(5):
        mgr.get("common")
    mgr.get("rare")  # touched more recently than "common"'s last get, but...

    mgr.put("new", 3)
    # "rare" has far lower frequency (2) than "common" (6) despite being
    # accessed more recently -- frequency must still dominate the decision.
    assert "common" in mgr.cache
    assert "rare" not in mgr.cache


def test_arc_ghost_list_populates_under_promote_then_evict_workload():
    """Verified negative result: ARC's ghost-list (B1) mechanism, initially
    suspected broken, is confirmed correct under a workload that actually
    exercises it -- fill T1 to capacity, promote one entry to T2 via a
    get(), then insert past capacity again so REPLACE() must run."""
    mgr = CacheManager(capacity=4, policy=CachePolicy.ARC)
    for k, v in [("a", 1), ("b", 2), ("c", 3), ("d", 4)]:
        mgr.put(k, v)
    mgr.get("a")  # promotes 'a' from T1 to T2
    mgr.put("e", 5)  # T1 is now full again relative to T1+B1 < c -- forces REPLACE()

    assert len(mgr._arc_b1) >= 1, (
        "Expected REPLACE() to move an evicted T1 entry into the B1 ghost "
        "list under this workload."
    )


def test_arc_ghost_hit_adapts_p_and_promotes_correctly():
    """A 'ghost hit' (re-inserting a key currently sitting in B1) must
    adapt the p parameter and promote the entry to T2 with its new value
    -- the core of ARC's actual adaptivity."""
    mgr = CacheManager(capacity=4, policy=CachePolicy.ARC)
    for k, v in [("a", 1), ("b", 2), ("c", 3), ("d", 4)]:
        mgr.put(k, v)
    mgr.get("a")
    mgr.put("e", 5)

    ghost_key = next(iter(mgr._arc_b1))
    p_before = mgr._arc_p

    mgr.put(ghost_key, 12345)

    assert mgr._arc_p > p_before, "p did not adapt upward on a B1 ghost hit."
    assert ghost_key in mgr._arc_t2, "Ghost-hit entry was not promoted to T2."
    assert ghost_key not in mgr._arc_b1
    assert mgr.get(ghost_key) == 12345


def test_arc_size_never_exceeds_capacity_under_sustained_unique_churn():
    """Regression guard for the scenario the existing shallow test in
    test_memory.py only lightly checks: capacity must hold under a long
    run of unique-key churn, not just three insertions."""
    mgr = CacheManager(capacity=8, policy=CachePolicy.ARC)
    for i in range(500):
        mgr.put(f"k{i}", i)
        assert mgr.size() <= 8
