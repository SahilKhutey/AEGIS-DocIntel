# PROT-03: API Disclosure & Error Sanitization Audit

**Document:** 04_API_DISCLOSURE_AUDIT.md  
**Audit Scope:** Public API contracts, internal routes, exception handling, and error response leakage.  

---

## 1. Public API Allowlist vs. Internal Routes

To prevent attackers from discovering or probing unreleased, administrative, or debug endpoints, the downloadable client is restricted strictly to the endpoints in `distribution/audit/prot-03/public_api_allowlist.yaml`:

| API Path | Method | Allowed in Demo? | Purpose & Entitlement Check |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | **YES** | Local proxy and container readiness probe (unauthenticated) |
| `/api/v1/gateway/health` | `GET` | **YES** | Remote Evaluation Gateway health check |
| `/api/v1/gateway/activate` | `POST` | **YES** | Instance activation & license issuance (rate-limited) |
| `/api/v1/gateway/license/status` | `GET` | **YES** | License validity & remaining quota inspection |
| `/api/v1/gateway/documents` | `POST` | **YES** | Ingestion of evaluation documents (max 5 docs, 10MB limit) |
| `/api/v1/gateway/documents` | `GET` | **YES** | List caller's documents (strictly tenant-isolated) |
| `/api/v1/gateway/documents/{doc_id}` | `GET` | **YES** | Fetch single document metadata (anti-IDOR 404 on mismatch) |
| `/api/v1/gateway/query` | `POST` | **YES** | Ask AEGIS grounded question with evidence citations |
| `/api/v1/gateway/compare` | `POST` | **YES** | Cross-document contradiction & invariant analysis |
| `/api/v1/gateway/demo/seed` | `POST` | **YES** | Populate evaluation session with synthetic benchmark data |
| `/api/v1/gateway/demo/reset` | `POST` | **YES** | Reset session documents and quota counters |
| `/api/v1/admin/*` | `ALL` | **BLOCKED (403)** | Administrative interfaces explicitly blocked in Nginx proxy |
| `/api/v1/orchestrator/*` | `ALL` | **BLOCKED (403)** | Internal pipeline control routes withheld |
| `/api/v1/telemetry/raw` | `ALL` | **BLOCKED (403)** | Raw system telemetry withheld |

---

## 2. Error Message Sanitization & Hygiene

### Initial Vulnerability (`src/api/routes/query.py`):
Earlier code handled exceptions by returning raw Python exception strings:
```python
except Exception as e:
    log.error('Ingest failed: %s', e, exc_info=True)
    raise HTTPException(500, f'Ingest failed: {e}')
```
And:
```python
except Exception as e:
    raise HTTPException(500, str(e))
```

### Attack Vector Analysis:
If an invalid PDF, corrupt archive, or database timeout occurred:
1. `str(e)` leaked internal filesystem paths (e.g., `C:\Users\ASUS\...` or `/app/data/...`).
2. Disclosed underlying database drivers, table names, and internal class hierarchies.
3. Provided attackers with structural information useful for crafting targeted injection exploits.

### Technical Remediation Implemented:
All exception handlers in `src/api/routes/query.py` and `services/evaluation_gateway/app.py` were refactored to enforce **opaque, sanitized client errors** while retaining rich server-side debugging logs:

```python
except Exception as e:
    req_id = str(uuid.uuid4())[:8]
    log.error('Ingest failed [ref=%s]: %s', req_id, e, exc_info=True)
    raise HTTPException(
        status_code=500,
        detail=f'Document ingestion failed. Internal error ref: {req_id}'
    )
```

### Verification Result:
Automated test `SEC-DEMO-012` and `IP-TEST-008` trigger malformed requests and assert that responses contain:
- Zero Python tracebacks (`Traceback (most recent call last)` is absent);
- Zero filesystem path strings (`C:\`, `/home/`, `/app/` are absent);
- Only standardized JSON error envelopes with tracking IDs.
