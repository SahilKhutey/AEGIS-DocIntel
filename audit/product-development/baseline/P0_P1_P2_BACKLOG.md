# AEGIS-DocIntel Engineering Sprint Backlog (P0 / P1 / P2)

**Backlog Version:** 1.0.0  
**Phase Reference:** PROT-FINAL-10 (Section 2)  
**Date:** 2026-11-19  
**Status:** Canonical Sprint Prioritization  

---

## 1. Prioritization Framework

Work packages are strictly tiered according to their necessity for establishing a dependable, verifiable document intelligence pipeline:
- **P0 — Core Workflow Restoration (Mandatory for Beta):** Foundational data path must work flawlessly before any advanced features are exposed.
- **P1 — Product Intelligence & Usability (High-Value Features):** Key analytical capabilities included once underlying pipeline stages are certified.
- **P2 — Beta Hardening & Release Rehearsal (Release Blockers):** Non-functional requirements (security, isolation, performance, backups) that must pass before external access is granted.

---

## 2. P0 Backlog: Core Workflow Restoration

| Work Package | ID | Scope & Engineering Tasks | Acceptance Criteria / Completion Evidence | Target Sprint | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline Audit** | PD-01 | Inspect backend, frontend, APIs, storage, workers, tests, and dependencies | Comprehensive baseline reports, component inventory, functionality matrix, signoff | Sprint 0 | **COMPLETED** |
| **File Handling** | PD-02 | Restore upload validation, opaque storage references, file integrity checksums, safe deletions | File lifecycle test suite with 100% pass rate; zero path traversal | Sprint 1 | PENDING (PROT-FINAL-11) |
| **Extraction Engine** | PD-03 | Hardening PDF (PyMuPDF), DOCX, TXT loaders with ground-truth fixtures and character recall metrics | Character recall $\ge 98\%$ on clean text PDF/DOCX fixtures | Sprint 2 | PENDING (PROT-FINAL-11) |
| **Document Parsing** | PD-04 | Layout analysis, heading hierarchy, table cell extraction, Kahn DAG reading order | Kahn topological sort determinism; table cell accuracy $\ge 95\%$ | Sprint 2 | PENDING (PROT-FINAL-11) |
| **Processing Orchestration**| PD-05 | State machine lifecycle unification (`UPLOADED` $\to$ `READY`), durable retries, lease locking | 100% of jobs reach terminal or documented retry state; zero stuck jobs | Sprint 3 | PENDING (PROT-FINAL-11) |
| **Intelligence Pipeline** | PD-06 | Multi-modal chunking, hybrid dense/sparse retrieval, evidence ranking, citation coordinate binding | Grounded answer evaluation suite with Recall@5 $\ge 0.85$ | Sprint 4 | SCHEDULED |
| **Context Optimization** | PD-07 | Submodular knapsack token packing, token budget enforcement, rejected evidence tracking | Never exceeds context budget; $(1-1/e)/2$ approximation bound | Sprint 4 | SCHEDULED |
| **Frontend Integration** | PD-08 | Wire Next.js UI to live backend REST/SSE APIs; verify end-to-end document upload and inspection | End-to-end browser workflow completed without developer intervention | Sprint 5 | SCHEDULED |

---

## 3. P1 Backlog: Product Intelligence & Usability

| Work Package | ID | Scope & Engineering Tasks | Acceptance Criteria | Target Sprint | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Source-Grounded Answers** | PD-09 | Page, section, and bounding-box level coordinate citations with visual highlight binding | $\ge 98\%$ citations resolve to exact source locations | Sprint 5 | SCHEDULED |
| **Structured Extraction** | PD-10 | Extract custom user-defined schemas, key-value pairs, and tabular summaries to JSON | Schema-conforming structured JSON outputs with confidence scores | Sprint 6 | SCHEDULED |
| **Document Summarization** | PD-11 | Document-level executive summaries and section-level hierarchical digests | Summaries grounded in document text; zero ungrounded claims | Sprint 6 | SCHEDULED |
| **Cross-Document Analysis** | PD-12 | Semantic comparison across documents; identify conflicting facts and version diffs | Conflict detection test suite passing with high precision | Sprint 6 | SCHEDULED |
| **Workspace Management** | PD-13 | Multi-document workspace organization, document tagging, semantic collection search | Fast workspace search ($p95 < 200\text{ms}$) with tenant isolation | Sprint 6 | SCHEDULED |
| **Error Recovery & Feedback**| PD-14 | User-facing failure explanations, retry triggers, and diagnostic reference lookups | Sanitized error codes; zero stack traces exposed to clients | Sprint 6 | SCHEDULED |
| **Usage Visibility** | PD-15 | Real-time token accounting, quota meters, job progress bars, and cost transparency | Token estimator aligns within $\pm 5\%$ of provider accounting | Sprint 6 | SCHEDULED |

---

## 4. P2 Backlog: Beta Hardening & Release Gates

| Category | Focus Area | Scope & Mitigation | Gate Reference |
| :--- | :--- | :--- | :--- |
| **Security & Isolation** | Multi-Tenancy | Verify 100% fail-closed cross-tenant document isolation and API guards | Gate D |
| **Input Hardening** | Parser Resilience | Test zip bombs, malformed XML, PDF buffer overflows, and corrupted headers | Gate D |
| **Performance** | Concurrency & Latency | Benchmark $p50/p95$ ingestion latency and concurrent query throughput | Gate A / Gate B |
| **Observability** | Telemetry & Logs | Prometheus metrics, OpenTelemetry spans, sanitized audit log ledgers | Gate D |
| **Disaster Recovery** | Backups & Deletion | Verify cascading document deletion and SQLite point-in-time restore | Gate D |
| **Deployment** | Docker & Caddy | Rehearse complete standalone deployment via Docker Compose with TLS | Gate E |
