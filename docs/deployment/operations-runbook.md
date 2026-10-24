# AEGIS-DocIntel — Operations Runbook

This runbook guides operators through Day-2 maintenance, observability monitoring, incident triage, and capacity scaling.

---

## 1. Monitoring & Metrics Catalog

AEGIS-DocIntel exports Prometheus metrics at `/metrics` (or port `9090` when configured).

### Key Service Metrics

| Metric Name | Type | Description | Alert Threshold |
| :--- | :--- | :--- | :--- |
| `aegis_documents_ingested_total` | Counter | Total documents ingested by pseudonymized tenant and status (`success`, `failed`). | Rate of failed > 5% over 5m. |
| `aegis_chunks_indexed_total` | Counter | Total chunks extracted and indexed. | Rate drop to 0 during active ingestion. |
| `aegis_retrieval_latency_seconds` | Histogram | Latency distribution across retrieval stages (BM25, dense, rerank). | p95 > 2.0s over 5m. |
| `aegis_query_errors_total` | Counter | Errors encountered in query decomposition, retrieval, and LLM synthesis. | Rate > 1/min. |
| `aegis_active_documents` | Gauge | Count of active documents per tenant. | Unbounded growth / deviation. |
| `aegis_cache_hits_total` / `misses` | Counter | Semantic cache performance metrics. | Hit ratio < 20% on repeated queries. |

---

## 2. Structured Logging & Triage

Production environments emit single-line structured JSON logs to standard output.

### Log Schema Fields

- `timestamp`: ISO-8601 UTC timestamp.
- `level`: Log severity (`info`, `warning`, `error`, `critical`).
- `event`: Canonical machine-readable event identifier (e.g. `document_upload`, `query_decomposed`).
- `request_id`: Tracing correlation identifier matching `X-Request-ID` header.
- `tenant_id_hash`: Irreversible pseudonymized tenant identifier (`t_<12-hex>`).
- `latency_ms`: Duration of request or processing step in milliseconds.

> [!IMPORTANT]
> The logging pipeline automatically redacts authorization headers, API keys, JWTs, passwords, session tokens, and raw document contents. Never modify the structlog filter to expose unredacted payloads.

### Querying Logs with jq

```bash
# Filter errors in last 100 log lines
tail -n 100 /var/log/aegis/service.log | jq 'select(.level=="error")'

# Filter requests by specific Request ID
tail -n 500 /var/log/aegis/service.log | jq 'select(.request_id=="req-trace-abc123")'
```

---

## 3. Incident Triage Procedures

### Alert: High 504 Gateway Timeout or 503 Provider Unavailable

1. Check downstream LLM or OCR provider status.
2. Inspect log records with `.level == "error"` and `.event == "provider_failure"`.
3. If downstream provider is rate-limiting, the internal bounded retry engine will back off automatically. Verify whether client applications send requests with exponential jitter.

### Alert: Readiness Probe Failing (`503 Service Unavailable`)

1. Check persistent SQLite disk space:
   ```bash
   df -h /app/data
   ```
2. Verify SQLite database file locks:
   ```bash
   fuser /app/data/documents.db
   ```
3. Test SQLite integrity:
   ```bash
   sqlite3 /app/data/documents.db "PRAGMA integrity_check;"
   ```

### Alert: Excessive 413 Content Too Large

- Client uploads exceed `AEGIS_MAX_UPLOAD_BYTES` (default 200MB).
- Verify whether client attempted to upload uncompressed files or adjust `AEGIS_MAX_UPLOAD_BYTES` if authorized.
