# Phase 13 Execution Report: API & SDK Stabilization

**Execution Date:** 2026-10-23  
**Status:** Completed & Evidence-Linked  
**Target:** Phase 13 of [docs/ROADMAP.md](../ROADMAP.md)

---

## 1. Executive Summary

Phase 13 establishes public contract stability across the AEGIS-DocIntel REST API and its official SDKs. Historically, client SDKs (Python, TypeScript, Java, and C++) attempted requests against nonexistent `/api/v1/...` routes while the server served `/v1/...`. Furthermore, SDK tests relied on mocked response bodies without ever touching a running API router.

This phase aligns all client libraries to canonical `/v1/...` paths defined in [openapi.json](../../openapi.json), implements an in-process live API integration test harness in `sdk/python/tests/test_integration.py`, and enforces zero route collisions and duplicate operation IDs via regression tests.

---

## 2. API Contract & OpenAPI Specification

1. **Route Alignment:**
   - Canonical prefix: `/v1/` across all endpoints (`/v1/documents`, `/v1/documents/upload`, `/v1/query`, `/v1/admin/stats`, `/v1/webhooks/subscriptions`).
   - OpenAPI schema generated from FastAPI and validated in root `openapi.json` (>100KB contract).
2. **Collision Elimination (`tests/test_api_route_integrity.py`):**
   - Verified 0 duplicate route collisions across routers.
   - Enforced unique OpenAPI `operationId` attributes preventing client code generator ambiguities.
   - Unified `POST /v1/query` combining dense semantic search, BM25 retrieval, and AEL export routing.

---

## 3. SDK Synchronization & Parity

### 3.1 Python SDK (`sdk/python/`)
- Package structure: `amdi_os` client library with typed models (`DocumentSummary`, `Document`, `RetrievalResult`, `EngineOutput`).
- Model deserialization resilience: Handled optional/null values for `latency_ms` and `total_candidates` preventing `TypeError`.
- Offline compatibility: Added `HF_HUB_OFFLINE=1` and `LLM_PROVIDER=mock` guards for deterministic offline test execution.
- In-process integration tests: [sdk/python/tests/test_integration.py](../../sdk/python/tests/test_integration.py) executes live HTTP requests against the FastAPI ASGI app:
  - `upload`: Multi-part stream upload returning 202.
  - `search`: Scoped query execution against `/v1/query`.
  - `get`: Retrieval of stored document metadata by UUID.
  - `delete`: Cascading deletion verifying subsequent 404.
  - `process` / `reindex`: Reindexing pipeline trigger against `/v1/documents/{doc_id}/reindex`.

### 3.2 TypeScript SDK (`sdk/typescript/`)
- Mapped all methods in `DocumentsAPI` and `RetrievalAPI` to `/v1/documents`, `/v1/documents/upload`, and `/v1/query`.
- Axios error mapping: Typed `AmdiAuthError` (401/403), `AmdiNotFoundError` (404), `AmdiRateLimitError` (429), and `AmdiValidationError` (422).

### 3.3 Java & C++ SDKs (`sdk/java/`, `sdk/cpp/`)
- Aligned route definitions in client builders to `/v1/documents` and `/v1/query`.

---

## 4. Verification Evidence

| API / SDK Guard | Command | Result |
|---|---|---|
| Python SDK Live Integration Suite | `pytest sdk/python/tests/` | **6 passed in 23.21s** |
| API Route Integrity & Collision Ratchet | `pytest tests/test_api_route_integrity.py` | **5 passed in 3.62s** |
| End-to-End API Workflow Lifecycle | `pytest tests/test_e2e_api_workflow.py` | **2 passed in 6.50s** |
| OpenAPI Specification File Validation | `tests/test_repo_hygiene.py` | **Passed (valid openapi.json > 100KB)** |
| Docs Claims Verification | `python scripts/check_docs_claims.py` | **OK — all 6 rules passed** |
| Dependency Synchronization | `python scripts/check_dependency_sync.py` | **OK — 5 files match pyproject.toml** |
