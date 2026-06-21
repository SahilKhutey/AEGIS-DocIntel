"""
Unit tests for the Hierarchical Memory Engine.
"""

from __future__ import annotations

import time
import pytest
import numpy as np

from src.engines.memory import (
    MemoryEngine,
    MemoryReport,
    HierarchicalMemory,
    MemoryStats,
    MemoryLevel,
    LevelMetadata,
    StorageManager,
    StorageBackend,
    CacheManager,
    CachePolicy,
    Promoter,
    PromotionPolicy,
    Evictor,
    EvictionPolicy,
    MemoryRetriever,
    RetrievalQuery,
    RetrievalResult,
    AccessTracker,
    AccessRecord,
    MemoryEngineError,
    LevelNotFoundError,
    CapacityExceededError,
    EvictionError,
    PromotionError,
)

def test_memory_levels() -> None:
    # Verify levels enum and priority
    assert MemoryLevel.L0_RAW.priority == 0
    assert MemoryLevel.L5_SUMMARIES.priority == 5
    assert MemoryLevel.L0_RAW.name_long == "raw"
    assert MemoryLevel.L5_SUMMARIES.name_long == "summaries"

    # Verify metadata defaults
    meta_l0 = LevelMetadata(level=MemoryLevel.L0_RAW)
    assert meta_l0.access_speed == 0.1
    
    meta_l5 = LevelMetadata(level=MemoryLevel.L5_SUMMARIES)
    assert meta_l5.access_speed == 2.0

def test_cache_manager_lru() -> None:
    # Cache capacity = 2
    mgr = CacheManager(capacity=2, policy=CachePolicy.LRU)
    mgr.put("a", 1)
    mgr.put("b", 2)
    assert mgr.get("a") == 1
    
    mgr.put("c", 3)  # Evicts "b" because "a" was accessed and "b" is LRU
    assert mgr.get("b") is None
    assert mgr.get("c") == 3
    assert mgr.get("a") == 1

def test_cache_manager_lfu() -> None:
    mgr = CacheManager(capacity=2, policy=CachePolicy.LFU)
    mgr.put("a", 1)
    mgr.put("b", 2)
    
    # Increase frequency of "a"
    mgr.get("a")
    
    mgr.put("c", 3)  # Evicts "b" because frequency(b) = 0 or 1 and a has been accessed twice
    assert mgr.get("b") is None
    assert mgr.get("a") == 1
    assert mgr.get("c") == 3

def test_cache_manager_arc() -> None:
    mgr = CacheManager(capacity=2, policy=CachePolicy.ARC)
    mgr.put("a", 1)
    mgr.put("b", 2)
    assert mgr.get("a") == 1
    
    mgr.put("c", 3)
    # Check that cache size is at most capacity
    assert mgr.size() <= 2
    assert len(mgr.keys()) <= 2

def test_storage_manager() -> None:
    # Config with very small capacity for testing limits
    config = {
        MemoryLevel.L0_RAW: LevelMetadata(
            level=MemoryLevel.L0_RAW,
            capacity_items=2,
            capacity_bytes=100,
        )
    }
    store = StorageManager(backend=StorageBackend.IN_MEMORY, level_config=config)
    
    # Verify store / get
    item1 = store.store("id1", MemoryLevel.L0_RAW, "data1", importance=0.8)
    assert item1.importance == 0.8
    assert store.exists("id1", MemoryLevel.L0_RAW)
    assert store.get("id1", MemoryLevel.L0_RAW).data == "data1"
    
    # Check duplicate overwrite
    store.store("id1", MemoryLevel.L0_RAW, "data1_new", importance=0.9, force=True)
    assert store.get("id1", MemoryLevel.L0_RAW).data == "data1_new"
    
    # Capacity exceeded
    store.store("id2", MemoryLevel.L0_RAW, "data2")
    with pytest.raises(CapacityExceededError):
        store.store("id3", MemoryLevel.L0_RAW, "data3")
        
    # Remove
    assert store.remove("id1", MemoryLevel.L0_RAW)
    assert not store.exists("id1", MemoryLevel.L0_RAW)
    
    # Move
    config[MemoryLevel.L1_TEMPLATES] = LevelMetadata(level=MemoryLevel.L1_TEMPLATES)
    store.store("id4", MemoryLevel.L0_RAW, "data4")
    assert store.move("id4", MemoryLevel.L0_RAW, MemoryLevel.L1_TEMPLATES)
    assert not store.exists("id4", MemoryLevel.L0_RAW)
    assert store.exists("id4", MemoryLevel.L1_TEMPLATES)

def test_access_tracker() -> None:
    tracker = AccessTracker(history_size=5)
    tracker.record_write("id1")
    tracker.record_read("id1")
    tracker.record_read("id1")
    
    rec = tracker.get("id1")
    assert rec.access_count == 2
    assert rec.write_count == 1
    assert rec.frequency > 0
    assert rec.recent_frequency >= 0
    
    # top_k
    tracker.record_write("id2")
    tracker.record_read("id2")
    top = tracker.top_k_by_frequency(1)
    assert top[0].item_id in ["id1", "id2"]
    
    tracker.remove("id1")
    assert tracker.get("id1") is None

def test_promoter() -> None:
    storage = StorageManager(backend=StorageBackend.IN_MEMORY)
    tracker = AccessTracker()
    promoter = Promoter(policy=PromotionPolicy.HYBRID, thresholds={MemoryLevel.L0_RAW: 0.1})
    
    storage.store("id1", MemoryLevel.L0_RAW, "data1", importance=0.8)
    tracker.record_write("id1")
    tracker.record_read("id1")
    
    # Score calculation
    rec = tracker.get("id1")
    score = promoter.compute_score(rec.frequency, 0.8, 1.0)
    assert score > 0
    
    # Promotes to next level
    dec = promoter.should_promote("id1", MemoryLevel.L0_RAW, storage, tracker)
    assert dec is not None
    assert dec.from_level == MemoryLevel.L0_RAW
    assert dec.to_level == MemoryLevel.L1_TEMPLATES
    
    # Batch promote
    decisions = promoter.promote_batch(MemoryLevel.L0_RAW, storage, tracker)
    assert len(decisions) == 1
    assert decisions[0].item_id == "id1"
    assert storage.exists("id1", MemoryLevel.L1_TEMPLATES)

def test_evictor() -> None:
    storage = StorageManager(backend=StorageBackend.IN_MEMORY)
    tracker = AccessTracker()
    evictor = Evictor(policy=EvictionPolicy.HYBRID)
    
    storage.store("id1", MemoryLevel.L0_RAW, "data1", importance=0.1)
    storage.store("id2", MemoryLevel.L0_RAW, "data2", importance=0.9)
    tracker.record_write("id1")
    tracker.record_write("id2")
    
    # Select victims: id1 has lower importance and should be evicted first
    victims = evictor.select_victims(MemoryLevel.L0_RAW, storage, tracker, n=1)
    assert len(victims) == 1
    assert victims[0].item_id == "id1"
    
    # Perform eviction
    evicted = evictor.evict(MemoryLevel.L0_RAW, storage, tracker, n=1)
    assert evicted == ["id1"]
    assert not storage.exists("id1", MemoryLevel.L0_RAW)
    assert storage.exists("id2", MemoryLevel.L0_RAW)

def test_retriever() -> None:
    storage = StorageManager(backend=StorageBackend.IN_MEMORY)
    tracker = AccessTracker()
    cache = CacheManager(capacity=10)
    retriever = MemoryRetriever(storage=storage, tracker=tracker, cache=cache)
    
    # Store items
    storage.store("id1", MemoryLevel.L4_SEMANTIC, "The brown fox jumped", importance=0.9)
    storage.store("id2", MemoryLevel.L5_SUMMARIES, {"embedding": [0.1, 0.2]}, importance=0.8)
    
    # Exact lookup
    res_exact = retriever.retrieve_by_id("id1")
    assert res_exact is not None
    assert res_exact.item_id == "id1"
    assert res_exact.data == "The brown fox jumped"
    
    # Query retrieval
    query = RetrievalQuery(query="fox", target_levels=[MemoryLevel.L4_SEMANTIC])
    result = retriever.retrieve(query)
    assert len(result.items) == 1
    assert result.items[0].item_id == "id1"
    
    # Scoring utility
    scorer = lambda x, y: np.dot(x, y)
    query_emb = RetrievalQuery(query="", embedding=np.array([0.1, 0.2]))
    result_emb = retriever.retrieve(query_emb, embedding_scorer=scorer)
    assert len(result_emb.items) > 0

@pytest.mark.asyncio
async def test_hierarchical_memory_e2e() -> None:
    memory = HierarchicalMemory(enable_cache=True)
    
    # Store
    item = memory.store("itemA", MemoryLevel.L0_RAW, "raw doc content", importance=0.8)
    assert item.item_id == "itemA"
    
    # Get polymorphism: single key
    val = memory.get("itemA")
    assert val == "raw doc content"
    
    # Get polymorphism: level and key
    val_lvl = memory.get(MemoryLevel.L0_RAW, "itemA")
    assert val_lvl == "raw doc content"
    
    # Set / alias
    memory.set("itemB", "summary text", level=MemoryLevel.L5_SUMMARIES)
    assert memory.get("itemB") == "summary text"
    
    # Put / async alias
    await memory.put("itemC", "template pattern", level=MemoryLevel.L1_TEMPLATES)
    assert memory.get("itemC") == "template pattern"
    
    # Stats
    stats = memory.get_stats()
    assert stats.total_items == 3
    assert stats.items_per_level[MemoryLevel.L0_RAW] == 1
    assert stats.items_per_level[MemoryLevel.L5_SUMMARIES] == 1
    
    # Legacy statistics dictionary
    legacy_stats = memory.statistics()
    assert "RAW" in legacy_stats
    assert legacy_stats["RAW"]["entries"] == 1
    
    # Invalidation
    memory.invalidate("item")
    assert memory.get("itemA") is None
    assert memory.get("itemB") is None

@pytest.mark.asyncio
async def test_memory_engine_facade() -> None:
    engine = MemoryEngine(enable_cache=True)
    
    # Connect/close
    await engine.connect()
    
    # Store multi
    items = [
        {"item_id": "doc1::k1", "level": MemoryLevel.L0_RAW, "data": "raw content 1"},
        {"item_id": "doc1::k2", "level": MemoryLevel.L5_SUMMARIES, "data": "summary content 1"}
    ]
    engine.store_multi(items)
    assert engine.get("doc1::k1") == "raw content 1"
    
    # Report
    report = engine.generate_report(metadata={"user": "admin"})
    assert report.metadata == {"user": "admin"}
    assert report.stats.total_items == 2
    assert "raw" in report.active_levels
    
    # to_dict
    rep_dict = report.to_dict()
    assert rep_dict["cache_policy"] == "lru"
    assert rep_dict["stats"]["total_items"] == 2
    
    await engine.close()
