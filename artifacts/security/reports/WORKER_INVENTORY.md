# AEGIS-DocIntel — Background Worker & Job Queue Inventory

> **Document ID**: `WORKER_INVENTORY.md`  
> **Work Item**: WP-07.05  
> **Status**: **VERIFIED**  

---

## 1. Background Worker Roles

| Worker Type | Primary Responsibility | Queue / Topic | Lease Window | Max Retries | Error Policy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ingestion Worker** | File registration, checksum validation, magic bytes check | `queue.ingest` | 60 seconds | 3 | Format errors permanent; IO retryable. |
| **Processing Worker** | Text extraction, OCR rasterization, layout DAG | `queue.process` | 180 seconds | 3 | Transient timeouts retryable; corrupt PDF permanent. |
| **Indexing Worker** | BM25 tokenization, dense vector embedding generation | `queue.index` | 120 seconds | 3 | Embedder timeouts retryable with jitter. |
| **Report Worker** | Report synthesis, claim validation, multi-format render | `queue.report` | 120 seconds | 2 | Scope errors permanent. |
| **Deletion Worker** | Multi-target cascading deletion, tombstone commit | `queue.deletion` | 60 seconds | 5 | All targets must succeed before completion. |

---

## 2. Worker Reliability Invariants

1. **At-Least-Once Delivery with Idempotent Execution**: If a message broker redelivers a job, the handler detects prior execution via `idempotency_key` and returns the existing result without duplicating records.
2. **Lease Renewal & Heartbeats**: Workers running long operations ping the job repository every `lease_window / 3` seconds. If a worker dies, its lease expires, allowing another worker to safely reclaim or fail the job.
3. **Dead-Letter State Machine**: When `retry_count >= max_retries`, the job transitions to `FAILED` with explicit `error_code` and diagnostic metadata. It is never silently dropped.
