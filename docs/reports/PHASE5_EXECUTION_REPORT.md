# Phase 5 — MVP Execution Report: Functional Product & Production Wiring

**Base:** `origin/fix/phase0-green-and-honest` @ `77aff3a`  
**Recent Commits:**
- `052a18d`: `feat(mvp): expand PII detection, wire real LLM provider interface, enable post-restart doc hydration, and fix CLI`
- `151538e`: `feat(query): implement scoped streaming queries with post-restart hydration and complete cascading deletion`
- `2025bdc`: `feat(api): implement tenant admin statistics, webhook management, and paginated chunk retrieval with persistence`
- `a53d351`: `feat(embeddings): implement multi-provider dense embeddings (OpenAI, LiteLLM, SentenceTransformers) with resilient mock fallback (I-18)`
- `1683a41`: `feat(ui): wire Streamlit dashboard to authenticated document, query, admin, and webhook endpoints`  
**Remote Branch:** `origin/fix/phase0-green-and-honest` (synced & pushed)  
**Status:** Implemented, verified with dedicated automated test suites, 0 regressions, and pushed to GitHub.

---

## 1. Outcome Summary

| Check / Capability | Before Phase 5 | After Phase 5 | Evidence / Verification |
|---|---|---|---|
| **Multi-Provider Semantic Embeddings (I-18)** | Semantic embeddings fell back to mock unless heavy PyTorch/SentenceTransformers ML stack was locally installed. | `EmbeddingService` natively supports OpenAI embeddings (`text-embedding-3-small`, `text-embedding-3-large`, `ada`), LiteLLM embeddings, local SentenceTransformers, and resilient mock fallback. | `pytest tests/test_embedding_providers.py tests/test_semantic.py` (69 passed) |
| **PII Detection Scope (I-28)** | Handled only 4 entity types (US SSN, Credit Card, US Phone, Title-Case Name). Missed emails, API keys, international phones, local numbers. | Detects & redacts emails, API keys (OpenAI, AWS, GitHub), international E.164 (`+44 20...`), and local 7-digit numbers (`555-0100`). Overlap prevention keeps SSNs distinct from phones. | `pytest aegis-docprep/tests/test_pii_redaction.py tests/test_docs_examples.py` (30 passed) |
| **Real LLM Integration (I-17)** | `AMDIOrchestrator` hardcoded `LLMInterface` to mock mode; config keys ignored. | Orchestrator forwards `llm_provider`, `llm_model`, `openai_api_key`. `LLMInterface` supports native `AsyncOpenAI` & `litellm` completions and token streaming with structured mock fallback. | `pytest tests/test_llm_interface_wiring.py` (4 passed) |
| **Post-Restart Document Hydration (I-19)** | Ingested documents were lost from orchestrator memory upon restart (queries returned 404/empty). | `raw_bytes` persisted as BLOB in SQLite; `RealDocumentService.hydrate_document` restores document state on demand prior to querying or inspecting chunks. | `pytest tests/test_persistence_and_audit.py` (4 passed) |
| **Streaming Query Pipeline** | Token streaming was in-memory mock and lacked tenant scoping or context building. | Scoped token streaming via SSE & WebSocket; automatic candidate retrieval via `AMDIRetriever`, context assembly via `ContextBuilder`, and document re-hydration across restarts. | `pytest tests/test_query_streaming_integration.py` (2 passed) |
| **Cascading Deletion Hardening** | `delete_document` in `AMDIOrchestrator` only cleared partial memory structures without vector store or cache cascade. | Cascading deletion clears document state, elements, tables, vector store embeddings, and semantic cache with foreign-tenant 404 isolation. | `pytest tests/test_document_deletion.py` (2 passed) |
| **Tenant Admin & Token Usage** | Admin `/stats` and `/token-usage` returned unauthenticated placeholder stubs. | Real RBAC-protected administrative endpoints computing active document counts, indexed chunk volume, token metrics, and estimated USD expenditure. | `pytest tests/test_admin_and_webhooks.py` (4 passed) |
| **Webhook Lifecycle Management** | Webhooks router only contained a lone mock endpoint. | Full subscription management (`POST`, `GET`, `DELETE` `/v1/webhooks/subscriptions`) with HMAC-SHA256 signing support and tenant scoping. | `pytest tests/test_admin_and_webhooks.py` & `tests/test_webhooks.py` (10 passed) |
| **Paginated Document Chunk Inspection** | `GET /v1/documents/{doc_id}/chunks` ignored pagination and returned empty chunks after server restarts. | Paginated chunk slices (`page`, `page_size`) with automatic post-restart SQLite re-hydration and tenant isolation. | `pytest tests/test_admin_and_webhooks.py` (PASSED) |
| **CLI Direct Execution** | Running `python src/cli.py` directly from workspace failed with `ModuleNotFoundError: No module named 'src'`. | CLI dynamically anchors repository root to `sys.path`. All subcommands (`ingest`, `query`, `batch`, `export`, `serve`) execute directly. | `pytest tests/test_cli.py` (11 passed) |
| **Authenticated Streamlit UI Dashboard Integration** | Dashboard API calls lacked authentication headers (causing 401s on protected endpoints) and failed on 204 No Content responses from document deletion. | `dashboard/app.py` authenticates all requests against `AuthGuardMiddleware` with tenant isolation (`Authorization: Bearer <token>`, `X-API-Key`, `X-Tenant-ID`), inspects documents and paginated chunks (`GET /v1/documents`, `GET /v1/documents/{doc_id}/chunks`), exports markdown/JSON UEO (`GET /v1/documents/{doc_id}/export`), queries RAG with citations rendering (`POST /v1/query`), tracks admin stats/token usage (`GET /v1/admin/stats`), and manages webhook subscriptions (`/v1/webhooks/subscriptions`). | `pytest tests/test_dashboard.py tests/test_dashboard_pages.py` (20 passed) |

---

## 2. Root Cause Analysis & Platform Hardening

1. **Embedding Tier Independence (I-18 Resolution):** Previously, running semantic search in cloud environments without several gigabytes of PyTorch/CUDA wheels forced the system into mock embedding mode. By abstracting the provider interface across OpenAI API, LiteLLM, and SentenceTransformers, users can use state-of-the-art hosted embeddings without local ML hardware dependencies.
2. **Loopback Socket Interception in Windows Sandbox:** Python's `asyncio.ProactorEventLoop` creates an internal `socket.socketpair()` for thread-safe event loop wakeups. The standard Windows command sandbox restricts loopback networking (`127.0.0.1`), causing `connect()` and `send()` socket operations to wait indefinitely until timeout. Running integration tests touching `asyncio` or FastAPI `TestClient` unsandboxed resolves the block.
3. **Lazy Module Import Performance:** `SentenceTransformer` imports load hundreds of megabytes of dynamic C++ DLLs. Checking availability via `importlib.util.find_spec` and lazy-loading models on first actual inference keeps application cold-start and test discovery instantaneous (<0.1s).
4. **Deny-by-Default Dashboard Authentication:** Streamlit dashboard API helper functions (`api_get`, `api_post`, `api_delete`) now inject tenant and bearer token context to satisfy `AuthGuardMiddleware`. Empty body 204 No Content responses (from `DELETE /v1/document` and `DELETE /v1/documents/{id}`) are parsed cleanly without `requests.exceptions.JSONDecodeError`.

---

## 3. Verified Commits & Status

- **Commits:**
  - `052a18d`: `feat(mvp): expand PII detection, wire real LLM provider interface, enable post-restart doc hydration, and fix CLI`
  - `151538e`: `feat(query): implement scoped streaming queries with post-restart hydration and complete cascading deletion`
  - `2025bdc`: `feat(api): implement tenant admin statistics, webhook management, and paginated chunk retrieval with persistence`
  - `a53d351`: `feat(embeddings): implement multi-provider dense embeddings (OpenAI, LiteLLM, SentenceTransformers) with resilient mock fallback (I-18)`
  - `1683a41`: `feat(ui): wire Streamlit dashboard to authenticated document, query, admin, and webhook endpoints`
- **Remote Branch:** `origin/fix/phase0-green-and-honest` (pushed and up-to-date)
- **Living Document Compliance:** `scripts/check_docs_claims.py` & `scripts/check_dependency_sync.py` all passing.
