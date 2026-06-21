import os
import sys
import tempfile
from pathlib import Path
import numpy as np
import pytest
from unittest.mock import MagicMock

# Configure Python path to find backend.optimization
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def test_optimization_imports():
    """Verify that all components can be imported from backend.optimization."""
    from backend.optimization import (
        OptimizationEngine,
        OptimizationResult,
        OptimizationSuite,
        TokenOptimizer,
        TokenOptimizationResult,
        TokenStrategy,
        MemoryOptimizer,
        MemoryOptimizationResult,
        MemoryStrategy,
        LatencyOptimizer,
        LatencyOptimizationResult,
        LatencyStrategy,
        RetrievalOptimizer,
        RetrievalOptimizationResult,
        RetrievalStrategy,
        CacheOptimizer,
        CacheOptimizationResult,
        BatchingOptimizer,
        BatchResult,
        Profiler,
        ProfileResult,
        profile,
        OptimizationReport,
        OptimizationMetrics,
        OptimizationError,
        OptimizationTargetError,
    )
    assert True


def test_exceptions():
    """Verify custom exceptions can be raised and caught."""
    from backend.optimization.exceptions import (
        OptimizationError,
        OptimizationTargetError,
        TokenBudgetExceededError,
        MemoryAllocationError,
    )
    
    with pytest.raises(OptimizationError):
        raise OptimizationTargetError("Target failed")
        
    with pytest.raises(TokenBudgetExceededError):
        raise TokenBudgetExceededError("Out of tokens")

    with pytest.raises(MemoryAllocationError):
        raise MemoryAllocationError("Out of RAM")


def test_profiling():
    """Verify Profiler tracks timings and memory usage."""
    from backend.optimization.profiling import Profiler, profile
    
    profiler = Profiler()
    
    # Context manager test
    with profiler.profile("test_op"):
        sum(i * i for i in range(1000))
        
    # Decorator test
    @profile(profiler, "decorated_op")
    def my_func():
        return sum(i for i in range(500))
        
    my_func()
    
    results = profiler.get_results()
    assert "test_op" in results
    assert "decorated_op" in results
    
    assert results["test_op"].total_calls == 1
    assert results["test_op"].mean_time_ms > 0.0
    
    profiler.reset()
    assert len(profiler.timings) == 0


def test_token_optimizer():
    """Verify TokenOptimizer strategies."""
    from backend.optimization.token_optimizer import TokenOptimizer, TokenStrategy
    
    opt = TokenOptimizer(target_reduction_pct=0.2)
    text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four. This is sentence five."
    
    # 1. Truncate
    res_trunc = opt.truncate(text, max_tokens=10)
    assert res_trunc.optimized_tokens <= 10
    assert res_trunc.reduction_pct > 0.0
    assert "text" in res_trunc.metadata
    
    # 2. Summarize (extractive heuristic)
    res_sum = opt.summarize(text, target_tokens=10)
    assert res_sum.optimized_tokens < opt.count_tokens(text)
    
    # 3. Compress (whitespace/stopwords removal)
    res_comp = opt.compress(text, target_reduction=0.5)
    assert res_comp.reduction_pct > 0.0
    assert "the" not in res_comp.metadata["text"].lower()  # stopwords removed due to target_reduction > 0.4
    
    # 4. Select
    texts = ["apple pie recipe", "quantum mechanics physics", "how to bake cake"]
    res_select = opt.select(texts, top_k=1, relevance_scores=[1.0, 5.0, 1.2])
    assert res_select.metadata["selected_texts"] == ["quantum mechanics physics"]
    
    # 5. Deduplicate
    texts_dup = ["Important fact 1", "Important fact 1", "Unrelated fact"]
    res_dedup = opt.deduplicate(texts_dup)
    assert len(res_dedup.metadata["selected_texts"]) == 2
    
    # 6. MMR Diversity
    embeddings = np.array([
        [1.0, 0.0],
        [0.99, 0.01],  # highly similar to 1st
        [0.0, 1.0],    # diverse
    ])
    res_mmr = opt.mmr_select(texts_dup, embeddings, top_k=2, lambda_param=0.5)
    selected = res_mmr.metadata["selected_texts"]
    assert len(selected) == 2
    
    # 7. Chain
    res_chain = opt.optimize_chain(texts_dup, target_tokens=3)
    assert res_chain.optimized_tokens <= 3


def test_memory_optimizer():
    """Verify MemoryOptimizer strategies."""
    from backend.optimization.memory_optimizer import MemoryOptimizer, MemoryStrategy
    
    opt = MemoryOptimizer(target_reduction_pct=0.2)
    
    # 1. GC
    res_gc = opt.force_gc()
    assert res_gc.strategy == "gc"
    
    # 2. Quantize (float32 to float16)
    arr = np.random.rand(10, 10).astype(np.float32)
    quantized, res_q = opt.quantize_array(arr, "float16")
    assert quantized.dtype == np.float16
    assert res_q.reduction_pct == 0.5  # half size
    
    # Quantize to int8 (integer scale)
    quant_int8, res_qi8 = opt.quantize_array(arr, "int8")
    assert quant_int8.dtype == np.int8
    
    # 3. Chunk processing
    arr_large = np.random.rand(100)
    process_fn = lambda x: x * 2
    results, res_chunk = opt.chunk_process(arr_large, chunk_size=20, process_fn=process_fn)
    assert len(results) == 5
    assert res_chunk.reduction_pct == 0.8
    
    # 4. Sparse compression
    sparse_arr = np.zeros((10, 10))
    sparse_arr[0, 0] = 1.0
    sparse_arr[5, 5] = 2.0
    compressed, res_c = opt.compress_array(sparse_arr)
    assert res_c.reduction_pct > 0.0  # Sparsity makes it compress well
    
    # Not sparse enough
    dense_arr = np.ones((10, 10))
    _, res_d = opt.compress_array(dense_arr)
    assert res_d.reduction_pct == 0.0
    
    # 5. Stream iterate
    data_list = [np.random.rand(100) for _ in range(50)]
    stream_res, res_stream = opt.stream_iterate(data_list, lambda b: [x * 2 for x in b], batch_size=10)
    assert len(stream_res) == 50
    assert res_stream.reduction_pct > 0.0
    
    # 6. Combined apply_all
    _, res_all = opt.apply_all(sparse_arr)
    assert res_all.reduction_pct > 0.0


def test_latency_optimizer():
    """Verify LatencyOptimizer parallelization and caching."""
    from backend.optimization.latency_optimizer import LatencyOptimizer, memoize
    
    opt = LatencyOptimizer()
    
    # 1. Parallelize
    ops = [
        lambda: sum(i for i in range(100)),
        lambda: sum(i * 2 for i in range(100)),
    ]
    results, res_par = opt.parallelize(ops, max_workers=2)
    assert len(results) == 2
    assert res_par.strategy == "parallelize"
    
    # 2. Cache
    call_count = 0
    def slow_fn():
        nonlocal call_count
        call_count += 1
        return "result"
        
    # First call: misses cache
    res1, info1 = opt.cached_call("my_key", slow_fn)
    assert res1 == "result"
    assert call_count == 1
    assert info1.metadata["cache_hit"] is False
    
    # Second call: hits cache
    res2, info2 = opt.cached_call("my_key", slow_fn)
    assert res2 == "result"
    assert call_count == 1
    assert info2.metadata["cache_hit"] is True
    
    # 3. Precompute
    res_pc = opt.precompute("pc_key", lambda: 42)
    assert res_pc == 42
    res_pc_cached = opt.precompute("pc_key", lambda: 99, use_cached=True)
    assert res_pc_cached == 42
    
    # 4. Batch Operations
    items = [1, 2, 3, 4]
    def double_batch(batch):
        return [x * 2 for x in batch]
    res_batch, info_batch = opt.batch_operations(items, double_batch, batch_size=2)
    assert res_batch == [2, 4, 6, 8]
    assert info_batch.strategy == "batch"
    
    # 5. Memoize decorator
    decorator_calls = 0
    @memoize()
    def dec_fn(x):
        nonlocal decorator_calls
        decorator_calls += 1
        return x * 10
        
    assert dec_fn(2) == 20
    assert dec_fn(2) == 20
    assert decorator_calls == 1


def test_cache_optimizer():
    """Verify CacheOptimizer profiling and capacity selection."""
    from backend.optimization.cache_optimizer import CacheOptimizer, OptimizedLRUCache
    
    # OptimizedLRUCache test
    cache = OptimizedLRUCache(capacity=3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    
    assert cache.get("a") == 1
    # Add another: evicts least recently used ("b" since "a" was accessed)
    cache.put("d", 4)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    
    assert cache.hit_rate() == 2 / 3  # hit 'a', miss 'b', hit 'a'
    assert cache.avg_lookup_ms() > 0.0
    
    # CacheOptimizer test
    optimizer = CacheOptimizer(min_capacity=2, max_capacity=20)
    access_pattern = ["a", "b", "c", "a", "b", "c", "d", "e", "f", "a", "b", "c"]
    
    # Find capacity matching hit rate
    cap = optimizer.find_optimal_capacity(access_pattern, target_hit_rate=0.4)
    assert cap >= 2
    
    # Recommendations
    stats = {
        "access_pattern": access_pattern,
        "num_unique_keys": 6,
    }
    rec = optimizer.recommend(stats)
    assert rec["recommended_capacity"] == 6
    assert rec["policy"] == "lru"


def test_batching_optimizer():
    """Verify BatchingOptimizer batch sizes selection."""
    from backend.optimization.batching_optimizer import BatchingOptimizer
    
    optimizer = BatchingOptimizer(min_batch=2, max_batch=16)
    
    items = list(range(50))
    def mock_process(batch):
        # artificial sleep to simulate runtime
        import time
        time.sleep(0.001 * len(batch))
        return [x * 2 for x in batch]
        
    # Find optimal batch size
    best_size = optimizer.find_optimal_batch_size(items, mock_process, target_time_ms=50.0)
    assert 2 <= best_size <= 16
    
    # Batch processing
    res = optimizer.batch_process(items, mock_process, batch_size=10)
    assert len(res.results) == 50
    assert res.num_batches == 5
    assert res.avg_batch_time_ms > 0.0
    assert res.throughput_items_per_sec > 0.0


def test_retrieval_optimizer():
    """Verify RetrievalOptimizer search speedups."""
    from backend.optimization.retrieval_optimizer import RetrievalOptimizer, RetrievalStrategy
    
    optimizer = RetrievalOptimizer()
    
    # Setup mock vector index
    np.random.seed(42)
    embeddings = np.random.rand(100, 8).astype(np.float32)
    query = np.random.rand(8).astype(np.float32)
    
    # 1. IVF Index Partitioning
    indices, res_idx = optimizer.optimize_index(embeddings, query, top_k=5, n_centroids=5)
    assert len(indices) == 5
    assert res_idx.recall_at_k >= 0.0
    assert res_idx.speedup > 0.0
    
    # 2. Prune search space
    candidates = [{"id": i, "category": "physics" if i % 2 == 0 else "biology"} for i in range(20)]
    filter_fn = lambda c: c["category"] == "physics"
    search_fn = lambda list_c: list_c[:3]  # simple top-3 search simulation
    
    res_pruned, res_pr = optimizer.prune_search_space(candidates, filter_fn, search_fn)
    assert len(res_pruned) == 3
    assert res_pr.strategy == "prune"
    
    # 3. Hybrid search (RRF)
    dense = ["docA", "docB", "docC"]
    sparse = ["docB", "docD", "docA"]
    fused, res_hyb = optimizer.hybrid_retrieval(dense, sparse, weight_dense=0.6)
    # RRF combines and ranks them
    assert fused[0] in ["docA", "docB"]
    
    # 4. Quantize embeddings
    _, res_q = optimizer.quantize_embeddings(embeddings)
    assert res_q.strategy == "quantize"
    
    # 5. Rerank
    candidates_list = ["doc1", "doc2", "doc3", "doc4"]
    rerank_fn = lambda coarse: sorted(coarse, key=lambda x: len(x), reverse=True)
    res_rr, res_rr_info = optimizer.rerank(candidates_list, rerank_fn, top_n=2)
    assert len(res_rr) == 2
    assert res_rr_info.strategy == "rerank"


def test_optimization_report():
    """Verify OptimizationReport metric compilation."""
    from backend.optimization.optimization_report import OptimizationReport
    from backend.optimization.token_optimizer import TokenOptimizationResult
    from backend.optimization.latency_optimizer import LatencyOptimizationResult
    
    report = OptimizationReport("Tuning")
    
    report.add_token_result(TokenOptimizationResult("deduplicate", 100, 80, 20, 0.2, 1.0))
    report.add_latency_result(LatencyOptimizationResult("cache", 120.0, 60.0, 2.0, 0.5))
    
    metrics = report.compute_metrics()
    assert metrics.token_reduction_pct == 0.2
    assert metrics.latency_reduction_pct == 0.5
    assert metrics.status == "OPTIMIZED"
    
    # JSON & Markdown check
    json_str = report.to_json()
    assert '"suite_name": "Tuning"' in json_str
    
    md_str = report.to_markdown()
    assert "# Optimization Report: Tuning" in md_str
    assert "Token Reduction" in md_str


def test_optimization_engine():
    """Verify OptimizationEngine execution coordinating optimizers."""
    from backend.optimization import (
        OptimizationEngine,
        OptimizationSuite,
        TokenStrategy,
        MemoryStrategy,
        LatencyStrategy,
        RetrievalStrategy,
    )
    
    suite = OptimizationSuite("Production Upgrade")
    
    # Add token optimization
    text = "The quick brown fox jumps over the lazy dog."
    suite.add_token_optimization(TokenStrategy.COMPRESS, text)
    
    # Add memory optimization
    arr = np.random.rand(10, 10).astype(np.float32)
    suite.add_memory_optimization(MemoryStrategy.QUANTIZE, arr, target_dtype="float16")
    
    # Add latency optimization
    suite.add_latency_optimization(LatencyStrategy.CACHE, [lambda: sum(i for i in range(50))], key="sum_op")
    
    # Add retrieval optimization
    query = np.random.rand(10).astype(np.float32)
    suite.add_retrieval_optimization(RetrievalStrategy.INDEX, arr, query, top_k=2, n_centroids=2)
    
    # Execute with engine
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = OptimizationEngine(
            target_token_reduction=0.0,
            target_memory_reduction=0.0,
            target_latency_reduction=0.0,
            target_retrieval_speedup=0.0,
        )
        res = engine.run_suite(suite, output_dir=tmp_dir)
        
        assert res.suite_name == "Production Upgrade"
        assert res.passed is True
        assert res.metrics.status == "OPTIMIZED"
        
        # Verify output files
        assert os.path.exists(os.path.join(tmp_dir, "optimization_report.json"))
        assert os.path.exists(os.path.join(tmp_dir, "optimization_report.md"))
