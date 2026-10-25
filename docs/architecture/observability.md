# AEGIS-DocIntel — Architecture: Observability & Telemetry

This document outlines the telemetry, metrics, structured logging, and privacy-preserving audit capabilities of AEGIS-DocIntel.

---

## 1. Observability Goals

The telemetry pipeline is designed to achieve four core objectives:
1. **Correlation:** Propagate immutable request identifiers across all middleware and pipeline steps.
2. **Standardization:** Emit machine-readable structured JSON logs in production environments.
3. **Privacy Compliance:** Protect sensitive tenant data and confidential document content from telemetry leakages.
4. **Actionable Telemetry:** Expose Prometheus metrics enabling latency, throughput, error-budget, and cache analysis.

---

## 2. Request Correlation (`X-Request-ID`)

Incoming requests are assigned a unique correlation ID via HTTP middleware:
- If a client supplies `X-Request-ID`, it is validated against strict alphanumeric criteria (max 64 characters, `^[a-zA-Z0-9_\-]+$`).
- If missing, invalid, or oversized, a fresh UUIDv4 is generated.
- The request ID is bound to structlog context variables for the duration of the request.
- The ID is echoed back to the client in the `X-Request-ID` response header along with `X-Response-Time-ms`.

---

## 3. Privacy-Preserving Telemetry & Tenant Pseudonymization

Telemetry data must never compromise customer confidential documents or reveal tenant relationships:

### A. Automatic Field Scrubbing
A custom structlog processor inspects all log records. Any key matching credentials, tokens, or raw document content is scrubbed:
- `authorization`, `token`, `jwt`, `api_key`, `password`, `secret`
- `raw_bytes`, `document_text`, `extracted_text`, `prompt`
- `credit_card`, `ssn`

Scrubbed fields are replaced with `[REDACTED]`.

### B. Tenant Pseudonymization
To observe tenant-level performance without exposing raw tenant identities, tenant IDs are hashed using salted SHA-256:
$$\text{pseudonym} = \text{t\_} + \text{SHA256}(\text{salt} \parallel \text{tenant\_id})[0:12]$$
This allows grouping metrics and logs by tenant while ensuring logs remain irreversible and anonymized.

---

## 4. Prometheus Metrics Architecture

Metrics are defined in [`src/observability/metrics.py`](../../src/observability/metrics.py) and scraped via `/metrics`:

- **Counters:** Ingested documents (`aegis_documents_ingested_total`), indexed chunks (`aegis_chunks_indexed_total`), LLM tokens (`aegis_llm_tokens_total`), cache hits/misses.
- **Histograms:** Retrieval stage latencies (`aegis_retrieval_latency_seconds`) bucketed from 10ms to 10s.
- **Gauges:** Active indexed documents (`aegis_active_documents`), ingest lag (`aegis_ingest_queue_lag`).

All Prometheus metrics use pseudonymized labels or aggregate counts to prevent high-cardinality leakage.
