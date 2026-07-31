# Architectural Bottlenecks & System Weak Points Analysis

## Executive Summary

AEGIS-DocIntel (AMDI-OS) is designed as a pre-LLM Document Intelligence Operating System operating across 16 mathematical domains. While the v0.3.0 release hardens process discipline, CI gates, and operational telemetry, scaling the system under production multi-tenant workloads reveals specific **architectural bottlenecks**, **concurrency bottlenecks**, and **resource limits**.

---

## 1. Ingestion Pipeline & Task Processing Bottlenecks

### A. GIL Contention in PyMuPDF & OCR Processing
* **Weak Point**: Document parsing routines (`PyMuPDF`, `pytesseract`, `python-docx`, `openpyxl`) execute CPU-bound tasks in standard Python threads or worker event loops.
* **Impact**: `PyMuPDF` (`fitz.Page.get_text()`) and `pytesseract` hold the CPython Global Interpreter Lock (GIL) during rendering and text extraction. Under concurrent multi-document upload surges, worker event loops stall, delaying SSE progress heartbeats and increasing `POST /v1/documents/upload` p95 latency.
* **Mitigation**: Move heavy CPU-bound parsers to dedicated `ProcessPoolExecutor` processes or isolated microservice workers running outside the main asyncio loop.

### B. Unbounded Job Queue & Lack of Backpressure
* **Weak Point**: The background job dispatch mechanism (`arq` + Redis) enqueues upload and processing jobs without a backpressure threshold on queue depth or active memory usage.
* **Impact**: A spike of multi-hundred-page PDFs can cause worker pods to consume excess Resident Set Size (RSS) memory (>2 GiB limit), triggering Kubernetes Out-Of-Memory (OOMKilled) terminations and job restarts.
* **Mitigation**: Implement adaptive admission control (HTTP 429 / 503 retry-after headers) when queue depth exceeds threshold, and enforce per-document page-count/byte limits prior to enqueueing.

---

## 2. Retrieval & Hybrid Fusion Bottlenecks

### A. Synchronous Method Fan-Out Latency Tail
* **Weak Point**: `HybridRetriever.search()` executes a 7-method fan-out using `asyncio.gather()` across BM25, Dense, Frequency, Geometry, Graph, Matrix, and Template search methods.
* **Impact**: The retrieval stage's total latency is bound by the **slowest individual method** (the tail latency problem). If the dense vector lookup or matrix decomposition calculation takes 400ms, the entire retrieval call waits 400ms regardless of how fast BM25 or Frequency search returns.
* **Mitigation**: Introduce speculative timeouts per method (e.g., cut off methods exceeding 150ms and proceed with partial fusion), and implement asynchronous speculative early-exit once top-K convergence threshold is satisfied.

### B. High Memory Overhead of Large Candidate Pools
* **Weak Point**: Each of the 7 retrieval methods fetches candidate pools of size `candidate_pool_size` (default: 50–100 items), creating up to 700 `Evidence` objects per query before fusion and deduplication.
* **Impact**: Under high query throughput (hundreds of QPS), object allocation churn in python GC (`Evidence` dictionaries, feature vectors, SimHash keys) leads to latency spikes and memory fragmentation.
* **Mitigation**: Pre-filter candidate lists inside method backends prior to object construction, and utilize compact NumPy typed arrays or native Cython/Rust struct allocations for internal candidate representation.

---

## 3. Compliance & Audit Storage Bottlenecks

### A. Disk I/O Bottlenecks in Audit Chain Logging
* **Weak Point**: The compliance audit engine writes SHA-256 hash-chained JSON records (`audit-%Y-%m-%d.log`) to disk with explicit file-flush operations to maintain tamper-evidence guarantees.
* **Impact**: Synchronous file flushing on every high-frequency API event or document access creates disk I/O bottlenecks (IOPS saturation) on standard EBS volumes or single-node SSDs.
* **Mitigation**: Implement buffered batch-flushing with write-ahead logging (WAL) and memory-mapped append logs, or offload append-only verification hashes to distributed append-only storage (e.g., AWS QLDB or Kafka append log).

---

## 4. Summary Matrix & Actionable Roadmap

| System Component | Primary Bottleneck / Risk | Severity | Root Cause | Proposed Long-Term Fix |
|---|---|---|---|---|
| **Ingestion** | Worker Pod OOM / GIL Stalls | **HIGH** | CPU-bound PDF/OCR parsing in main GIL | ProcessPool workers + admission backpressure |
| **Retrieval** | Fan-out tail latency | **HIGH** | Straggler method delays `asyncio.gather` | Soft timeout per method + speculative fusion |
| **Compliance** | Disk IOPS saturation | **MEDIUM** | Disk sync/flush per audit log event | Ring-buffer batching + WAL append log |
| **Memory** | Garbage collection churn | **MEDIUM** | Large candidate pool object creation | Typed struct allocations & pre-filtering |
