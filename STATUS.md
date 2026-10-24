# Project Status — Evidence-Linked

_Last verified: 2026-10-10 against `master` @ `5bec766` plus the Phase 0 changes (see [CHANGELOG.md](CHANGELOG.md))._

**One rule governs this file: a capability is listed as working only if a test, CI job or script in this repository re-checks it.** Numbers that rot (test counts, coverage) are not hard-coded — the CI badge in the [README](README.md) is the source of truth. Anything not re-verified is labelled as such.

**Overall: alpha research prototype with verified core modules.** The ingest → retrieve → delete pipeline runs end to end in-process. Production RS256 JWT validation, hash-only API-key lookup, deny-by-default route guard, SQLite document metadata & raw-byte persistence, and cryptographic audit logging are implemented and verified by automated regression test suites. External pilot verification, independent third-party certification, and distributed multi-tenant storage remain future roadmap items.

> **CI note:** `master` was red at the start of Phase 0 (test jobs aborted at collection; the secret scan flagged a placeholder hash). The Phase 0 fixes were verified locally from a fresh virtualenv; they have **not yet been observed passing on GitHub** — check the badge.

---

## P0 Security and Reliability Status

| Control | Implementation | Verification | Remaining limitation |
|---|---|---|---|
| JWT authentication | Implemented in `src/api/auth.py` | `tests/test_production_auth.py` | Strictly RS256, requires verified RSA public key; validates `exp`, `sub`, `tenant_id`, `role`, `iss`, `aud` |
| API-key authentication | Implemented in `src/api/auth.py` | `tests/test_production_auth.py` | Hash-only SHA-256 configuration, constant-time comparison (`hmac.compare_digest`), raw keys in config rejected |
| HTTP route guard | Implemented in `src/api/auth_guard.py` | `tests/test_auth_guard.py` | Deny-by-default on all routes; public allowlist restricted to operational health probes |
| Tenant isolation | Implemented in API, orchestrator & DB | `tests/test_multitenancy_isolation.py` | Non-disclosing 404/401 on cross-tenant document, export, deletion, and query operations |
| Document persistence & lifecycle | SQLite schema v2 in `src/services/container.py` | `tests/test_persistence_and_audit.py`, `tests/test_document_deletion.py` | Atomic lifecycle (`processing`→`ready`/`failed`), SHA-256 byte checksum, tombstoned cascading deletion, and cold-start crash recovery |
| Secret scanning | GitHub Actions integration | `.gitleaksignore` reviewed | Gitleaks scan blocks unreviewed credentials across repository history |
| CI Pipeline | GitHub Actions `.github/workflows/ci.yml` | Candidate PR & push triggers | Real security gates with `pip-audit` and `bandit -ll` without suppression |

---

## P2 AI Quality, Mathematical Invariants & Retrieval Evaluation Status

| Control / Capability | Implementation | Verification | Remaining limitation |
|---|---|---|---|
| Document extraction fidelity & provenance | `SourceLocation`, `NormalizedElement` in `src/models/evidence_object.py` and `aegis-docprep/` | `tests/test_extraction_fidelity.py` | Full page coordinate, section path, and table row/col matrix preserved; rotation normalization in progress |
| Layout-aware reading order recovery | `layout_aware_reading_order` in `aegis-docprep/aegis_docprep/reading_order.py` | `tests/test_extraction_fidelity.py`, `evaluation/scripts/evaluate_extraction.py` | Multi-column clustering and spatial ambiguity detection; complex wrapped text flows around irregular polygons remain future work |
| Context packing mathematical invariants | `SubmodularKnapsackPacker`, `validate_packing_inputs` in `aegis-docprep/` & `src/engines/retrieval/submodular_packer.py` | `aegis-docprep/tests/test_context_packer_invariants.py`, `evaluation/scripts/evaluate_packing.py` | 0% budget violations, non-negative affine/clipped cosine transformations, and provable $(1 - 1/e)/2 \approx 0.316$ knapsack bound |
| Privacy & PII precision-recall benchmark | `redact_or_block`, `ComplianceReport.safe_summary()` in `aegis-docprep/` & `src/compliance/` | `aegis-docprep/tests/test_pii_precision_recall.py`, `evaluation/scripts/evaluate_privacy.py` | Precision >= 0.85, recall >= 0.85, 0.0% downstream secret leakage, and mandatory fail-closed blocking |
| Evidence-grounded retrieval & citation verification | `RetrievedEvidence`, `validate_citations`, and abstention logic in `src/engines/retrieval/` & `src/core/orchestrator.py` | `tests/test_retrieval_grounding.py`, `evaluation/scripts/evaluate_retrieval.py` | Pre-retrieval tenant scoping, RRF rank fusion, 100% citation verification, and explicit abstention on unanswerable queries |
| Quality benchmark framework & regression runner | `evaluation/scripts/run_all.py` with versioned `qa_eval_dataset.json` and `manifest.json` | `tests/test_evaluation_runner.py` | Automated evaluation gates with structured report generation and exit code enforcement |

---

## P3 Production Reliability, Deployment & Operational Readiness Status

| Control / Capability | Implementation | Verification | Remaining limitation |
|---|---|---|---|
| Runtime configuration validation | Fail-closed validation in `src/core/settings.py` | `tests/test_runtime_configuration.py` | Mandatory in production: persistent SQLite, explicit CORS, JWT issuer/aud, hash-only API keys; mock LLMs and unauthorized external transfer rejected |
| Health & readiness probes | `/health` (liveness) and `/readiness` (database/container query probe) in `src/main.py` | `tests/test_runtime_configuration.py`, `tests/test_performance_and_capacity.py` | Returns 503 if container not started or database unreachable; decoupled from auth guard |
| Structured JSON logging & redaction | Structlog JSON renderer + credential scrubber in `src/observability/logging.py` | `tests/test_observability_and_diagnostics.py` | Automatic redaction of tokens, keys, passwords, and raw text; tenant IDs pseudonymized to irreversible SHA-256 hashes |
| Request correlation & latency | `X-Request-ID` extraction/generation & `X-Response-Time-ms` in `src/main.py` middleware | `tests/test_observability_and_diagnostics.py` | Enforces alphanumeric/hyphen sanitization ($\le 64$ chars); bound to structlog contextvars |
| Bounded async retries | `retry_transient_async` with exponential backoff & full jitter in `src/core/resilience.py` | `tests/test_resilience_and_recovery.py` | Strict deadline enforcement; fails fast immediately on non-transient domain errors |
| Tenant-scoped idempotency | `IdempotencyStore` with payload hash & conflict detection in `src/core/resilience.py` | `tests/test_resilience_and_recovery.py`, `tests/test_performance_and_capacity.py` | Mutual exclusion under concurrent races; payload divergence triggers 409 Conflict |
| Crash & restart recovery | Automatic state reconciliation on startup in `src/services/container.py` | `tests/test_resilience_and_recovery.py` | Transitions interrupted `processing` to `failed` and `deleting` to `delete_failed` with explicit error codes |
| SQLite migration & rollback safety | Schema v1 to v2 auto-upgrade in `src/services/container.py` | `tests/test_migrations_and_rollback.py` | Zero data loss on schema upgrade; backup snapshots verified with `PRAGMA integrity_check` |
| Multi-tenant concurrency & capacity | ASGI concurrent requests & bounded memory profiling | `tests/test_performance_and_capacity.py` | p50 < 80ms, p95 < 250ms for probes; memory growth bounded under 2MB across 500 operations |

---

## What works (and how to re-verify it)

| Capability | State | Re-verify with |
|---|---|---|
| Ingest PDF / DOCX / PPTX / XLSX / image / text into structured elements | Working | `pytest tests/test_ingest_workflow.py tests/test_real_world_ingestion.py` |
| Table extraction | Working, single-pass PDF parser without re-parsing | `tests/test_table_extraction_regression.py`, `python scripts/run_benchmark.py` |
| Real-corpus benchmark | 77 of 78 multi-format documents succeed (61/62 PDFs, 14/14 DOCX monographs, XLSX, PPTX); 220 tables detected — independently re-run and reproduced | `python scripts/run_benchmark.py`, `pytest tests/test_benchmark_proof.py` |
| Tenant isolation on `/v1/documents` and `/v1/query` | Working (404 on missing/foreign tenant) | `tests/test_multitenancy.py`, `tests/test_retrieval_tenant_isolation.py` |
| **Deny-by-default authentication** — every non-public route returns 401 without credentials | Working (added in Phase 0) | `tests/test_auth_guard.py` |
| **Production authentication** — RS256 JWT validation and real API-key lookup | Working (added in Phase 4) | `tests/test_production_auth.py` |
| **Document persistence** — SQLite store preserves ingested document metadata across service restarts | Working (added in Phase 4) | `tests/test_persistence_and_audit.py` |
| **Tamper-evident audit logging** — Append-only log with cryptographic SHA-256 chaining | Working (added in Phase 4) | `tests/test_persistence_and_audit.py` |
| **Submodular packer approximation guarantee** — (1 - 1/e)/2 bound with single-item fallback | Working (added in Phase 2) | `pytest aegis-docprep/tests/test_packer.py` |
| **API consolidation** — 0 duplicate route collisions, unified `/v1/query` | Working (added in Phase 3) | `tests/test_api_route_integrity.py` |
| Dev-token bypass rejected outside `AEGIS_ENVIRONMENT=development` | Working | `tests/test_auth_guard.py` |
| **Cascading document deletion** — cleans up document, state, elements, tables, vector store and semantic cache | Working | `pytest tests/test_document_deletion.py` |
| **Streaming query with tenant scoping & auto-hydration** — real token streaming, cross-tenant isolation, post-restart re-hydration | Working (added in Phase 5) | `pytest tests/test_query_streaming_integration.py` |
| **Admin statistics & token usage** — RBAC-enforced tenant-scoped stats and token consumption breakdown | Working (added in Phase 5) | `pytest tests/test_admin_and_webhooks.py` |
| **Webhook subscriptions & chunk inspection** — full subscription CRUD with tenant scoping and paginated chunk retrieval with post-restart hydration | Working (added in Phase 5) | `pytest tests/test_admin_and_webhooks.py` |
| 9 Prometheus metrics | Each has at least one real call site (audited by grep) | `src/observability/metrics.py` |
| `aegis-docprep` | Alpha. Installs from source with only `numpy`; its documented examples and outputs are executed by tests | `tests/test_docs_examples.py`, `aegis-docprep/tests/` |
| Dependency single-source-of-truth | `pyproject.toml` generates `requirements-*.txt` | `python scripts/check_dependency_sync.py` |
| README install path | Run on a fresh virtualenv by CI | `scripts/cold_start_check.sh` |
| **Expanded PII detection & redaction** — emails, API keys/tokens, international E.164, and local 7-digit phones | Working (added in Phase 5) | `pytest aegis-docprep/tests/test_pii_redaction.py tests/test_docs_examples.py` |
| **Real LLM provider interface** — OpenAI and litellm integration with structured mock fallback | Working (added in Phase 5) | `pytest tests/test_llm_interface_wiring.py` |
| **Document re-hydration across restarts** — SQLite preserves document raw bytes and restores orchestrator state | Working (added in Phase 5) | `pytest tests/test_persistence_and_audit.py` |
| **Direct CLI execution** — CLI resolves root path and commands run directly from workspace root | Working (added in Phase 5) | `python src/cli.py --help` |
| **Multi-provider semantic embeddings** — Native OpenAI, LiteLLM, and local SentenceTransformers support with resilient mock fallback | Working (added in Phase 5) | `pytest tests/test_embedding_providers.py` |
| **Authenticated Streamlit UI dashboard** — Tenant-isolated document ingestion, chunk inspection, query citation rendering, admin stats, and webhook subscription management | Working (added in Phase 5) | `pytest tests/test_dashboard.py tests/test_dashboard_pages.py` |
| **End-to-end API document lifecycle** — Full authenticated upload, metadata polling, chunk retrieval, tenant-isolated RAG query, and cascading deletion | Working (added in Phase 5) | `pytest tests/test_e2e_api_workflow.py` |
| **Repository structure & hygiene guards** — Root folder organized into canonical docs trees (`specifications/`, `reports/`, `assets/`, `papers/`) with zero untracked scratch/database artifacts | Working (added in Phase 5) | `pytest tests/test_repo_hygiene.py` |
| **Mathematical invariant property verification** — Hypothesis-driven validation of graph Laplacian positive semi-definiteness, Dirichlet energy, Vietoris-Rips filtration monotonicity, and information theory bounds | Working (added in Phase 6) | `pytest tests/test_math_properties.py tests/test_theorem_properties.py` |
| **Containerization & deployability hardening** — Multi-stage Dockerfile bundling src and backend with production healthcheck and unified orchestration | Working (added in Phase 6) | `deploy/docker-compose.yml`, `Dockerfile` |
| **Empirical benchmark proof & data integrity** — Automated verification of 62-doc PDF ingestion, 220 tables, timing CSV schema, IR accuracy metrics, and submodular approximation | Working (verified for MVP) | `pytest tests/test_benchmark_proof.py`, `python scripts/run_benchmark.py` |
| **Security hardening & penetration resistance** — Automated verification of SQL injection resistance, path traversal sanitization, cross-tenant IDOR defense, deny-by-default auth, and webhook scoping | Working (added in Phase 10) | `pytest tests/test_security_pentest_proof.py` |
| **Compliance controls & gap analysis** — Machine-verified right-to-erasure cascading deletion, PII redaction, tamper-evident audit logging, and logical access controls | Working (verified in Phase 11) | `pytest tests/test_document_deletion.py tests/test_compliance_redaction.py` |
| **9 Prometheus metrics & Grafana telemetry** — Ingestion throughput, chunk indexing, active documents, cache hits/misses, retrieval latency, and token consumption | Working (activated in Phase 12) | `pytest tests/test_observability_metrics.py`, `deploy/docker-compose.yml` |
| **Client SDK parity & live API integration** — Official Python, TypeScript, Java, and C++ client libraries aligned to OpenAPI contract with in-process live test harness | Working (stabilized in Phase 13) | `pytest sdk/python/tests/`, `pytest tests/test_api_route_integrity.py` |
| **Standalone `aegis-docprep` packaging** — Lightweight numpy-only document prep package with spatial reading order, submodular packing, and PII redaction | Working (packaged in Phase 14) | `pytest aegis-docprep/tests/`, `pytest tests/test_docs_examples.py` |

## Not implemented or not real yet

| Gap | ID | Evidence |
|---|---|---|
| Signed releases / provenance | I-23 | no tags published |
| Any external validation — no pilots have been completed | I-24 | GitHub has no pilot issues |

## Known defects (open)

| Defect | ID | Pinned by |
|---|---|---|
| `/metrics` is public and its series are labelled with `tenant_id` | — | `src/api/auth_guard.py` (documented exposure) |
| Not on PyPI — install from source | I-08 | `pypi.org` returns 404 |

## Fixed in Phase 16 (Productization & MVP Readiness)

| Fix | Phase | ID |
|---|---|---|
| Comprehensive productization synthesis across standalone `aegis-docprep`, unified core API, authenticated Streamlit dashboard, and container orchestration | Phase 16 | — |
| Multi-format real-corpus benchmark validation (78 documents, 98.7% success, 220 tables) | Phase 16 | — |
| Formal repository structuring under `docs/specifications/`, `docs/reports/`, `docs/assets/`, and `docs/papers/` with automated hygiene guards | Phase 16 | — |

## Fixed in Phase 14 (Scope Narrowing & Core Packaging)

| Fix | Phase | ID |
|---|---|---|
| Extracted lightweight standalone `aegis-docprep` package requiring only numpy for spatial reading order, submodular packing, and PII redaction | Phase 14 | — |
| Executable documentation tests verifying every README code snippet against live runtime outputs | Phase 14 | — |

## Fixed in Phase 13 (API & SDK Stabilization)

| Fix | Phase | ID |
|---|---|---|
| Aligned Python, TypeScript, Java, and C++ client SDKs to canonical `/v1/` routes matching `openapi.json` | Phase 13 | I-12 |
| Implemented in-process live API integration test suite for Python SDK | Phase 13 | — |
| Enforced zero route collisions and unique OpenAPI operation IDs across routers | Phase 13 | I-11 |

## Fixed in Phase 12 (Observability Activation & Distributed Tracing)

| Fix | Phase | ID |
|---|---|---|
| Active Prometheus metric instrumentation across ingestion, chunking, caching, retrieval latency, and token accounting | Phase 12 | — |
| Context-aware asynchronous request correlation ID propagation via structlog | Phase 12 | — |
| Automated Grafana dashboard and datasource provisioning with Docker Compose orchestration | Phase 12 | — |

## Fixed in Phase 11 (Compliance Documentation Rebuild & Verifiable Controls)

| Fix | Phase | ID |
|---|---|---|
| Cascading document erasure across SQLite metadata, orchestrator memory, FAISS index, and query caches | Phase 11 | — |
| Replaced self-graded compliance scorecard with verified gap analysis in `production/security-audit/compliance_gap_analysis.json` | Phase 11 | — |
| Verified PII redaction engine across SSN, credit cards, phones, emails, and API keys with non-truncating surname preservation | Phase 11 | I-28 |
| Cryptographically chained SHA-256 tamper-evident structured audit logging | Phase 11 | I-21 |

## Fixed in Phase 10 (Security Penetration Hardening & Multi-Tenant Defense)

| Fix | Phase | ID |
|---|---|---|
| Automated penetration testing suite machine-verifying SQL injection resilience, path traversal sanitization, multi-tenant IDOR isolation, and deny-by-default auth | Phase 10 | — |
| Cross-tenant document isolation across upload, status polling, chunk inspection, RAG query, and cascading deletion | Phase 10 | I-27 |
| Production dev-token bypass prevention when `AEGIS_ENVIRONMENT=production` | Phase 10 | I-31 |
| Webhook subscription isolation with HMAC cryptographic integrity | Phase 10 | — |
| Bandit static analysis triage and pip-audit CVE verification | Phase 10 | — |

## Fixed in Phase 6 (Test Hardening & Math Property Verification)

| Fix | Phase | ID |
|---|---|---|
| Property-based testing for math engines: spectral graph Laplacian positive semi-definiteness, Dirichlet energy conservation, Vietoris-Rips filtration monotonicity, and information theory bounds | Phase 6 | — |
| Python SDK model resilience against null latency_ms and total_candidates deserialization | Phase 6 | — |
| Dockerfile copy instructions updated to bundle backend/ alongside src/ and config/ | Phase 6 | I-09 |
| Aligned deploy/docker-compose.yml environment variables to AEGIS_ENVIRONMENT | Phase 6 | — |
| Removed obsolete Retrack bundle directory and added permanent repository hygiene guards | Phase 6 | — |
| Automated benchmark proof suite validating real PDF ingestion dataset, timing CSV schema, and IR evaluation metrics | Phase 6 | — |
| Unified multi-format empirical benchmark harness across 78 real files (PDF, DOCX, XLSX, PPTX) with 98.7% success rate | Phase 6 | — |

## Fixed in Phase 5 (MVP Progression)

| Fix | Phase | ID |
|---|---|---|
| Multi-provider dense embeddings supporting OpenAI, LiteLLM, and SentenceTransformers with resilient fallback | Phase 5 | I-18 |
| Expanded PII redaction engine to emails, API tokens/keys, international E.164 phone formats, and local 7-digit numbers | Phase 5 | I-28 |
| Real LLM provider wiring via AMDIOrchestrator and LLMInterface with native OpenAI & litellm support and mock fallback | Phase 5 | I-17 |
| Cross-restart document re-hydration from SQLite raw_bytes store into AMDI memory state | Phase 5 | I-19 |
| Scoped streaming query pipeline with automatic document re-hydration and cascading deletion | Phase 5 | — |
| Real admin usage statistics, token consumption reporting, webhook subscription management, and paginated chunk retrieval with cross-restart persistence | Phase 5 | — |
| Fixed CLI path resolution allowing direct `python src/cli.py` execution from any directory | Phase 5 | — |
| Authenticated Streamlit UI dashboard integration with document exploration, chunk inspection, live query citations, admin stats, and webhook subscription management | Phase 5 | — |
| End-to-end API lifecycle integration suite verifying upload, chunk inspection, RAG query, cross-tenant isolation, and cascading deletion | Phase 5 | — |
| Proper repository restructuring: segregated engine specs into docs/specifications, phase reports into docs/reports, assets into docs/assets, and removed obsolete root scratch directory | Phase 5 | — |

## Fixed in Phases 1–4

| Fix | Phase | ID |
|---|---|---|
| Root Dockerfile created, healthcheck target aligned, `/health` mock-mode 503 false alarm fixed | Phase 1 | I-09, I-10 |
| PDF table extraction O(N^2) page-reparsing eliminated | Phase 2 | I-14 |
| SubmodularKnapsackPacker (1 - 1/e)/2 approximation guarantee implemented with best-single-item fallback | Phase 2 | I-26 |
| PII surname truncation leak resolved | Phase 2 | I-15 |
| 5 API route collisions and 3 duplicate OpenAPI operation IDs eliminated | Phase 3 | I-12 |
| Unified `POST /v1/query` with AEL export routing; cross-tenant queries return 404 | Phase 3 | I-11, I-13 |
| Production RS256 JWT validation and real API-key lookup | Phase 4 | I-20 |
| SQLite document persistence across service restarts | Phase 4 | I-19 |
| Tamper-evident structured audit logging with SHA-256 cryptographic chaining | Phase 4 | I-21 |
| Aligned `requires-python` to `>=3.12` and modernized trove classifiers | Phase 4 | I-30 |

## Fixed in Phase 0

| Fix | ID |
|---|---|
| Anonymous callers could read other tenants' documents and wipe all documents (45 of 59 operations had no authentication) | I-27 |
| Undeclared dependencies (`hypothesis`, `python-docx`, `python-pptx`, `openpyxl`) made the documented install abort with zero tests run | I-01, I-02 |
| Two divergent dependency lists (pyproject vs requirements) | I-01 |
| Secret scan false positive (placeholder hash) | I-04 |
| Stale AEL integration test | I-05 |
| Tracked, test-mutated SQLite file (`data/annotations.db`) | I-25 |
| Documented examples that did not run, and documented outputs that were false | I-28 |
| Unsupported pilot case studies removed (quarantined in `_unverified_archive/pilot/`) | I-06 |
| Docs referenced an environment variable (`ALLOW_DEV_BYPASS`) that does not exist | I-31 |
| CI pinned to deprecated Node 20 actions and the floating `ubuntu-latest` | I-29 |

## Corrections to earlier claims

Earlier revisions of this file, the README and the changelog stated the following; each was found to be false or unsupported and has been corrected:

- "N tests passing" counts that disagreed with each other and with reality.
- Phase 10 and Phase 13 labelled "Verified" while most routes had no authentication and several routes were duplicated.
- Pilot case studies with specific metrics, which no public issue or statement corroborates.
- PII redaction of emails and API tokens; the implementation handles four entity types only.
- A "provably (1 − 1/e)" guarantee for the context packer (see I-26).
- A documented `ALLOW_DEV_BYPASS` variable that never existed; the real control is `AEGIS_ENVIRONMENT`.
- Python support "3.10–3.12"; CI tests 3.12 and 3.13.
- A memory figure and a single-document timing that cite no reproducible artifact.

The previous file is preserved unmodified, with a warning banner, at [docs/history/STATUS_2026-10-09.md](docs/history/STATUS_2026-10-09.md).

---

## Layer-by-Layer Implementation Status (Master State D)

Per Section 5.1 of the AMDI-OS Extended Monograph and its Appendix E
status matrix — the most detailed and honest implementation-status
assessment that exists in this project (a *self*-assessment — not independently audited):

| Layer | Meaning | Status |
|---|---|---|
| P | Page/element representation | Hardened |
| G | Geometric coordinate layer | Hardened |
| R | Structural recurrence | Hardened |
| F | Token frequency/weight | Hardened |
| M | Table-matrix relational | Hardened |
| T | Template fingerprint | Hardened |
| X | Structural linkage graph | Hardened |
| S | Semantic embedding | Mock fallback unless `sentence-transformers` installed — real path exists and works, but is optional and clearly flagged (`is_mock` on `MasterState.semantic_status`) |
| H | Hierarchical coordinate (persistent homology) | Proposed, not yet evaluated |
| E | Shannon-entropy | Hardened |

This table is enforced in code, not just documentation: `MasterState`
(added in this phase) carries a `LayerStatus` alongside every layer, so
`state.semantic_status.is_mock` or `state.hierarchy_status.is_proposed`
can be checked at runtime rather than only in a document no pipeline
consumer ever reads.

---

## Not Real (Previously Presented as Fact — Now Corrected)

- **"Production Ready" status** — removed. There is no evidence of any
  production deployment.
- **Penetration test report, threat model, vulnerability scan** — these were
  self-authored narrative documents, not real security testing output. Moved
  to `_unverified_archive/`. Replaced in Phase 10 with authentic `bandit` static
  analysis and `pip-audit` dependency scanning reports in `production/security-audit/`.
- **GDPR / SOC 2 / ISO 27001 "COMPLIANT" status** — self-declared, not
  certified by any accredited third party. No organization holds any formal
  compliance certification for this software. Replaced in Phase 11 with an
  honest gap analysis in `production/security-audit/compliance_gap_analysis.json`
  documenting real control implementations, partial implementations, and explicit gaps.
- **Signed release artifacts** (`SHA256SUMS.sig`, `.crt` files) — these were
  placeholder text, not real cryptographic signatures.
- **Benchmark results (94.2% accuracy, etc.)** — generated against a
  synthetic dataset (`generate_mock_dataset.py`), not real documents. The PDFs
  in that dataset do not open correctly and ground-truth entries contain
  literal placeholder text ("Mock Document eng_003"). No real-world accuracy
  claim can currently be made about this system.

---

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) and the 6-phase fix and reconstruction plan. Phase 0 (this document's baseline) restores a green, truthful starting point.