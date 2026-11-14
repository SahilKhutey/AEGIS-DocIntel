# WP-04.02: Ingress Guard Hardening & Operational Endpoint Containment

**Document:** `04_AUTH_GUARD_AND_PUBLIC_ENDPOINTS.md`  
**Work Package:** PROT-04.02 — Production Authentication Hardening  
**Target:** Ingress Guard Allowlist, Prometheus Metrics Containment & Operational Exposure  
**Status:** **AUDITED, HARDENED & VERIFIED**  
**Classification:** Internal Security Implementation Report  

---

## 1. Operational Endpoint Exposure Review

The backend ingress pipeline (`src/api/auth_guard.py`) historically allowed anonymous access to:
- `/metrics` and all child prefixes.
- `/docs`, `/redoc`, `/openapi.json` (interactive documentation).

### 1.1 The `/metrics` Metadata Leakage Risk
The Prometheus metrics registry records document ingestion throughput, query latencies, and error counters tagged with active `tenant_id` labels.
In an evaluation deployment, exposing `/metrics` allows an untrusted caller to enumerate tenant IDs and monitor platform usage.

### 1.2 Hardened Allowlist Architecture
`src/api/auth_guard.py` now implements dynamic environment-aware allowlists:

```python
HARDENED_PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/",
        "/ui",
        "/health",
        "/health/live",
        "/health/ready",
        "/readiness",
    }
)

HARDENED_PUBLIC_PREFIXES: tuple[str, ...] = ()
```

- When `AEGIS_RESTRICT_OPERATIONAL_ENDPOINTS=true` or `AEGIS_EVALUATION_MODE=true`:
  - `/metrics` is removed from `PUBLIC_PREFIXES`. All requests to `/metrics` require valid authentication credentials; anonymous requests receive `HTTP 401 Unauthorized` (`AUTH-H-023`).
  - `/docs`, `/redoc`, and `/openapi.json` are removed from `PUBLIC_PATHS`. Unauthenticated requests receive `HTTP 401 Unauthorized` (`AUTH-H-024`).
  - Only `/`, `/ui`, `/health`, and `/readiness` probes are accessible unauthenticated.

---

## 2. Minimal Health Probe Hygiene

In accordance with Section 5.C of WP-04.02, health probe endpoints disclose only minimal operational telemetry:
- Unauthenticated response:
  ```json
  { "status": "ok" }
  ```
- **Information Protection:** Health probes strictly avoid returning:
  - Database connection strings or internal database hostnames.
  - Model provider status details or internal API keys.
  - Software build commit hashes or environment variable names.
  - Tenant identifiers or active license counts.

---

## 3. Test Verification

Automated regression tests in `tests/test_auth_guard.py`:
- `test_hardened_production_metrics_requires_auth` -> **PASSED** (Verifies `/metrics` returns 401 in hardened mode).
- `test_hardened_production_docs_requires_auth` -> **PASSED** (Verifies `/docs` and `/openapi.json` return 401 in hardened mode).
- `test_every_non_public_operation_rejects_anonymous_requests` -> **PASSED** (Verifies all 59 backend endpoints reject anonymous access).
- `test_public_path_matching` -> **PASSED** (Verifies canonicalization and traversal resistance).
