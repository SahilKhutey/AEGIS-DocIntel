# AEGIS-DocIntel — Architecture: Resilience, Retries & Recovery

This specification details the failure modes, error classification, retry behaviors, idempotency guarantees, and crash recovery mechanisms in AEGIS-DocIntel.

---

## 1. Domain Error Classification

Errors in AEGIS-DocIntel are categorized explicitly into domain error classes rooted in `AEGISDomainError`:

| Exception Class | HTTP Status Code | Description | Transient? |
| :--- | :--- | :--- | :--- |
| `InvalidDocumentError` | `400 Bad Request` | Unsupported file format, empty file, or malformed magic bytes. | No (fail-fast) |
| `IdempotencyConflictError` | `409 Conflict` | Same idempotency key supplied with different payload. | No |
| `IdempotencyInProgressError` | `409 Conflict` | Concurrent duplicate request currently processing. Returns `Retry-After: 1`. | Yes (retryable by client) |
| `ExtractionError` | `422 Unprocessable Content` | Parsing / OCR / Table extraction failed unrecoverably. | No |
| `ResourceLimitError` | `413 Content Too Large` | Document byte size or page count ceiling exceeded. | No |
| `ProviderTimeoutError` | `504 Gateway Timeout` | Downstream model or external OCR exceeded request deadline. | Yes |
| `ProviderRateLimitError` | `429 Too Many Requests` | Downstream LLM provider throttled requests. Returns `Retry-After: 5`. | Yes |
| `ProviderUnavailableError`| `503 Service Unavailable`| Downstream LLM service experiencing temporary outage. | Yes |
| `DocumentStorageError` | `500 Internal Server Error`| SQLite write transaction failure or disk lock error. | Transient / System |

---

## 2. Bounded Asynchronous Retries

Downstream provider requests (OCR, embeddings, LLM completions) utilize `retry_transient_async` with bounded exponential backoff and full jitter:

$$t_{\text{backoff}} = \min(t_{\text{max}}, t_{\text{base}} \times 2^{\text{attempt}}) \times U(0.5, 1.0)$$

### Key Properties
- **Transient-Only:** Non-transient errors (such as `InvalidDocumentError` or `ValueError`) bypass retries and fail immediately on the first attempt.
- **Deadline Enforcement:** If the cumulative elapsed time plus jittered sleep exceeds `deadline_seconds`, the retry loop terminates immediately and raises a timeout.
- **Full Jitter:** Avoids thundering herd problems when a downstream provider recovers.

---

## 3. Tenant-Scoped Durable Idempotency

Expensive or stateful operations (such as document ingestion) support the `Idempotency-Key` HTTP header:
1. When a client sends `Idempotency-Key: <key>`, the system computes a SHA-256 hash of the upload payload.
2. The `IdempotencyStore` checks `(tenant_id, operation, key)`:
   - **New Key:** Status marked `in_progress`; request proceeds.
   - **Matching Completed Key:** Cached response payload is returned immediately with identical status code.
   - **Key Conflict:** If the key was previously completed with a different payload hash, `IdempotencyConflictError` (HTTP 409) is raised.
   - **Concurrent In-Flight:** If another thread is actively processing the key, `IdempotencyInProgressError` (HTTP 409 + `Retry-After: 1`) is returned.
3. Multi-tenant isolation is strictly preserved: keys are partitioned by `tenant_id`.

---

## 4. Crash & Restart Recovery

If the host or container terminates abruptly during processing or deletion:
- On container initialization, `RealDocumentService` inspects persistent SQLite storage:
  - Any records in `status = 'processing'` are transitioned to `status = 'failed'` with `error_code = 'STALE_PROCESSING_INTERRUPTED'`.
  - Any records in `status = 'deleting'` are transitioned to `status = 'delete_failed'` with `error_code = 'STALE_DELETION_INTERRUPTED'`.
- This eliminates phantom in-progress states and informs client workflows that the operation was interrupted.
