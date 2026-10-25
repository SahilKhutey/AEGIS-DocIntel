# AEGIS-DocIntel — Performance & Capacity Benchmark Plan

This document establishes workload definitions, throughput and latency targets, and profiling methodology for evaluating AEGIS-DocIntel at scale.

---

## 1. Capacity & Latency Targets

| Dimension | Target Metric | Measured Verification Baseline |
| :--- | :--- | :--- |
| **Liveness / Readiness Latency** | p50 < 50ms, p95 < 200ms | Verified in `test_health_and_readiness_latency_distribution` (p50 < 80ms, p95 < 250ms). |
| **Metadata Listing / Retrieval** | p95 < 300ms | SQLite indexed queries with multi-tenant filtering. |
| **Max Payload Size** | Strict 200MB limit | Middleware enforces HTTP 413 prior to streaming body. |
| **Concurrent Multi-Tenant Traffic** | $\ge 24$ concurrent streams | Verified under ASGI transport without deadlocks. |
| **Process Memory Footprint** | Peak RSS < 2GB | Verified bounded memory growth over repeated operations. |
| **Idempotency Race Protection** | 100% mutual exclusion | Exactly 1 winner in 20-thread concurrency race. |

---

## 2. Benchmark Workload Profiles

### Profile A: Heavy Ingestion (Write-Intensive)
- **Payload:** 10-page to 50-page mixed PDF documents containing text, tables, and embedded diagrams.
- **Goal:** Measure OCR extraction throughput, chunking efficiency, and SQLite transaction persistence under sustained multi-tenant writes.
- **Tooling:** Locust / k6 scripts targeting `/v1/documents/upload` with varying concurrency (4 to 16 workers).

### Profile B: Interactive Context Assembly (Read-Intensive)
- **Payload:** Multimodal user queries targeting pre-indexed document collections.
- **Goal:** Benchmark the AMDI context compilation pipeline (query decomposition, BM25 + dense hybrid retrieval, reranking, and dynamic 0/1 knapsack packing).
- **Target:** Context assembly completed in < 400ms prior to LLM generation.

---

## 3. Profiling & Continuous Verification

The performance test suite is executed continuously via:

```bash
# Run latency percentiles, concurrency, and memory stability checks
python -m pytest tests/test_performance_and_capacity.py -v
```

Memory leaks are monitored using Python's `tracemalloc` to track peak memory allocations and diff object allocations across iterations.
