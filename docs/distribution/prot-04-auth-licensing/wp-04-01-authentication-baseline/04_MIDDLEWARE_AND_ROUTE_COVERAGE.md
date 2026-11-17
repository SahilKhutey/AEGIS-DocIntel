# WP-04.01: Global Middleware Pipeline & Route Coverage Audit

**Document:** `04_MIDDLEWARE_AND_ROUTE_COVERAGE.md`  
**Work Package:** PROT-04.01 — Authentication Baseline & Threat Model  
**Component:** ASGI Ingress Guard, Public Endpoint Allowlist & Exposure Analysis  
**Status:** **AUDITED & VERIFIED**  
**Classification:** Internal Security Audit Report  

---

## 1. Historical Vulnerability & The Fail-Closed Paradigm

### 1.1 The Legacy Opt-In Failure Model
Prior to the implementation of `AuthGuardMiddleware` (`src/api/auth_guard.py`), backend route security relied entirely on per-route dependency injection (`Depends(get_current_tenant)`).

A comprehensive architectural audit of all **59 API operations** in the core FastAPI backend revealed that **45 operations lacked route-level authentication guards**:
- Unauthenticated callers could export arbitrary documents (`GET /v1/documents/{id}/export`).
- Unauthenticated callers could issue batch document wipeouts (`DELETE /v1/document -> 204 No Content`).
- Legacy query routers, annotation endpoints, and webhook receivers accepted arbitrary anonymous payloads.

Opt-in security inherently **fails open**: when an engineer adds a new router or forgets `Depends(...)`, the endpoint is exposed publicly by default.

### 1.2 Fail-Closed Inversion (`AuthGuardMiddleware`)
The introduction of `AuthGuardMiddleware` fundamentally inverted this security posture:
- The middleware executes at the outermost ASGI boundary before router matching.
- **Rule:** A request is rejected with `HTTP 401 Unauthorized` **unless** its destination path is on the explicit public allowlist, or the request carries valid credentials accepted by `_validate_jwt()` or `_validate_api_key()`.
- **Result:** 100% of newly added endpoints are secure by default.

---

## 2. Public Route Allowlist Audit

`AuthGuardMiddleware` maintains an explicit set of public paths:

```python
PUBLIC_PATHS: frozenset[str] = frozenset({
    "/",
    "/ui",
    "/health",
    "/health/live",
    "/health/ready",
    "/readiness",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    "/openapi.json",
})

PUBLIC_PREFIXES: tuple[str, ...] = ("/metrics",)
```

### 2.1 Route Evaluation Matrix

| Route Path | Type | Production Justification | Exposure Severity | Evaluation Hardening |
| :--- | :--- | :--- | :--- | :--- |
| `/` | Root | Service info / index redirect | None (Informational) | Retain public |
| `/ui`, `/ui/` | Static UI | Serves evaluation frontend bundle | None (Public Assets) | Retain public |
| `/health`, `/readiness` | Probes | Container orchestrator liveness / readiness | Low (No data) | Retain public |
| `/docs`, `/redoc` | Swagger UI | Interactive developer documentation | Medium (Schema leak) | **Disable in demo** (`docs_url=None`) |
| `/openapi.json` | API Schema | OpenAPI 3.0 specification | Medium (API exposure) | **Disable in demo** (`openapi_url=None`) |
| `/metrics` (Prefix) | Telemetry | Prometheus operational scrape endpoint | **HIGH (Metadata leak)**| **Isolate behind Docker VPC** |

---

## 3. The `/metrics` Telemetry Exposure Risk

### 3.1 Known Exposure Analysis
`src/api/auth_guard.py` explicitly documents:
> *"/metrics : Prometheus scrape endpoint. Conventional to protect with network policy rather than app auth. KNOWN EXPOSURE: series are labelled with tenant_id, so this must not be internet-reachable."*

Prometheus metric series in AEGIS expose operational counters labeled with active `tenant_id`s, document ingestion rates, and query latency distributions. If publicly accessible, an attacker can:
1. Harvest valid tenant IDs for targeted brute force attacks.
2. Monitor real-time document processing volumes and concurrent system load.

### 3.2 Evaluation Network Containment
In the Protected Demo Edition deployment:
1. **No External Port Binding:** The `/metrics` endpoint is not mapped to the host interface (`127.0.0.1` or `0.0.0.0`).
2. **Docker Internal Network:** The scrape target is bound exclusively to the internal Docker network (`aegis-internal-net`), accessible only by the isolated Prometheus container.
3. **Local Reverse Proxy:** The demo launcher's local NGINX/reverse-proxy explicitly blocks any external HTTP request targeting `/metrics` with `HTTP 403 Forbidden`.

---

## 4. Path Normalization & Traversal Resistance

Path matching in `AuthGuardMiddleware` enforces strict canonicalization:
```python
def _is_public(path: str, public_paths: frozenset[str], public_prefixes: Iterable[str]) -> bool:
    norm = path.rstrip("/") or "/"
    if norm in public_paths:
        return True
    return any(norm == p or norm.startswith(p + "/") for p in public_prefixes)
```

### 4.1 Traversal & Boundary Test Verification
`tests/test_auth_guard.py` verifies that malicious path manipulation cannot bypass the guard:
- `/health` -> `True` (Public probe allowed)
- `/healthz` -> `False` (Prefix spoof rejected -> 401)
- `/healthcheck` -> `False` (Prefix spoof rejected -> 401)
- `/metricsx` -> `False` (Prefix spoof rejected -> 401)
- `/metrics-private` -> `False` (Prefix spoof rejected -> 401)
- `/docs/../v1/documents` -> `False` (Path traversal rejected -> 401)
- `/v1/documents` -> `False` (Protected route rejected -> 401)
- `/v1/admin/stats` -> `False` (Protected route rejected -> 401)

All 42 test scenarios in `tests/test_auth_guard.py` pass without regression.
