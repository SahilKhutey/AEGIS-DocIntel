# AEGIS-DocIntel — Launch Feature Availability Matrix

This matrix establishes the verified launch truth for the **AEGIS-DocIntel Product Launch Edition (v1.2.0)**. Every capability marked as **Available** is backed by automated tests, verification scripts, or reproducible benchmark runs.

Status Key:
- **Available:** Fully operational, end-to-end usable, and validated by test suite.
- **Limited:** Usable under specific configuration constraints or deterministic policy.
- **Preview:** Interactive demonstration or UI showcase active with synthetic or preloaded data.
- **Planned:** Future roadmap item; clearly disclosed to avoid over-claiming.

---

## 1. Core Launch Features (P0 MVP)

| Capability | Priority | Launch Status | Description & Verification |
| :--- | :--- | :--- | :--- |
| **Document Upload & Ingestion** | P0 | **Available** | Multi-format upload (PDF, DOCX, PPTX, XLSX, HTML, TXT) up to 200MB. Layout-aware reading order extraction and table matrix recovery. Verified by `tests/test_ingest_workflow.py`. |
| **Document Inspection & Extraction** | P0 | **Available** | Inspect element bounding boxes, reading order DAGs, and extracted table cells. Interactive inspection in `/documents` workbench. |
| **Ask AEGIS (Evidence RAG)** | P0 | **Available** | Question answering over indexed documents using submodular knapsack context packing. Verified by `tests/test_retrieval_grounding.py`. |
| **Citation & Source Resolution** | P0 | **Available** | 100% citation verification resolving claims to exact source passages and page coordinates. Tested in `tests/test_retrieval_grounding.py`. |
| **Document Comparison** | P0 | **Available** | Cross-document fact extraction and contradiction detection (e.g. clock speed & TDP differences). Verified in `/compare` and `demo/scripts/verify_demo.py`. |
| **Tenant Isolation & Security** | P0 | **Available** | Parameterized SQL query scoping (`WHERE tenant_id = ?`), deny-by-default HTTP route guard, and isolated demo session. Verified by `tests/test_auth_guard.py` and `demo/tests/test_demo_isolation.py`. |
| **Data Persistence & Recovery** | P0 | **Available** | SQLite persistence of document metadata and raw bytes across service restarts. Tested by `tests/test_persistence_and_audit.py`. |

---

## 2. Advanced & Governance Features (P1)

| Capability | Priority | Launch Status | Description & Verification |
| :--- | :--- | :--- | :--- |
| **Submodular Context Packing** | P1 | **Available** | Provable $(1 - 1/e)/2$ knapsack approximation bound maximizing information gain per token. Verified by `aegis-docprep/tests/test_context_packer_invariants.py`. |
| **Tamper-Evident Audit Logging** | P1 | **Available** | Append-only log with SHA-256 hash chaining rooted at genesis hash. Verified by `tests/test_persistence_and_audit.py`. |
| **PII Detection & Redaction** | P1 | **Available** | Automated identification of emails, API tokens, phone numbers, and SSNs. Tested by `aegis-docprep/tests/test_pii_redaction.py`. |
| **Contradiction Detection Engine** | P1 | **Available** | Typed fact contradiction classification with divergence scores. Verified by `src/engines/intelligence/`. |
| **Human Review Queue & Decisions** | P1 | **Available** | Human-in-the-loop review queue for ambiguous extractions and conflicting facts. Tested by `tests/test_dashboard.py`. |
| **Mathematical Representations** | P1 | **Preview** | Interactive inspection of graph Laplacians, persistent homology, and simplicial complexes in `/mathematics`. |
| **Telemetry & Observability** | P1 | **Limited** | 9 Prometheus metrics instrumenting latency, tokens, and chunk counts; internal Grafana dashboards. Network-isolated. |

---

## 3. Developer & Integration Ecosystem (P2)

| Capability | Priority | Launch Status | Description & Verification |
| :--- | :--- | :--- | :--- |
| **Client SDK Parity** | P2 | **Available** | Canonical Python, TypeScript, Java, and C++ client libraries matching `/v1/` OpenAPI schema. Tested in `sdk/python/tests/`. |
| **Standalone `aegis-docprep`** | P2 | **Available** | Lightweight, numpy-only Python package distributed under Apache 2.0. Verified in `aegis-docprep/tests/`. |
| **Webhook Delivery & HMAC Integrity**| P2 | **Available** | Webhook subscriptions with tenant isolation, SSRF URL validation, and HMAC-SHA256 signatures. Verified by `tests/test_webhook_security.py`. |
| **External LLM Cloud Egress** | P2 | **Limited** | Configurable provider interface (OpenAI, LiteLLM) disabled by default for privacy (`AEGIS_ALLOW_EXTERNAL_LLM=false`). |
| **External Enterprise Pilot Validation**| P2 | **Planned** | External customer pilot trials remain an active milestone following public launch. |
| **Cryptographic Release Signing** | P2 | **Planned** | Third-party cosign binary provenance signing planned for v1.3.0. |
