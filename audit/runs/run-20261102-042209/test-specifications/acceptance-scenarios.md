# AEGIS-DocIntel — Acceptance Scenarios Specification
**Document Status:** Approved Acceptance Specification  
**Classification:** Alpha / Experimental (Release Candidate v1.0.0-mvp)  
**Scope:** End-to-End Product Verification & Governance  

---

## Overview

This specification establishes the mandatory end-to-end acceptance scenarios required to validate that AEGIS-DocIntel operates reliably across document ingestion, layout geometry analysis, context budget assembly, grounded answer generation, structured intelligence, human review governance, background job resilience, and UI workbench operations.

---

## Acceptance Scenarios Matrix

| Scenario ID | Category | Scenario Title | Preconditions | Inputs / Triggers | Expected Behavior | Release Gate | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **SCEN-001** | Ingestion & Q&A | Multi-Format Document Ingestion to Grounded Q&A | Authenticated tenant session; empty document repository. | Upload PDF (`sample.pdf`), poll until `status="ready"`, post natural language question. | Response contains evidence-grounded answer with verified page citations and character offsets. Zero hallucinated references. | Gate 2 | **PASS** |
| **SCEN-002** | Layout & Table | Two-Column Layout & Table Reconstruction | Standard two-column PDF with embedded multi-column financial table. | `POST /v1/documents/upload` | Elements extracted with Kendall's tau $\ge 0.80$; table cells reconstructed with F1 $\ge 0.90$. Headers and cells properly associated. | Gate 2 | **PASS** |
| **SCEN-003** | Context Packing | Submodular Knapsack Context Assembly | Candidate chunk pool totaling 8,000 tokens; hard budget limit 2,048 tokens. | `ContextBuilder.build_context(..., budget=2048)` | Selected context strictly $\le 2048$ tokens. Submodular knapsack ratio $\ge 0.316$ verified against greedy optimum. | Gate 2 | **PASS** |
| **SCEN-004** | Grounding & Safety | Unanswerable Query Safe Abstention | Document containing legal definitions; question asking about unrelated medical treatment. | `POST /v1/query` with ungrounded question. | System returns `status="abstained"` and abstention rationale. No fabricated or unverified claims. | Gate 2 | **PASS** |
| **SCEN-005** | Intelligence | Cross-Document Contradiction Detection | Two vendor master agreements uploaded with differing payment terms ($50k net 30 vs $75k net 60). | `POST /v1/intelligence/conflicts` | System identifies conflicting terms, preserves both source spans, and generates typed `ConflictReportModel`. Neither value silently overwritten. | Gate 2 | **PASS** |
| **SCEN-006** | Governance | Human-in-the-Loop Review Claim & Decision | Pending review item generated from extracted fact candidate. | Reviewer claims item (`POST /v1/reviews/{id}/claim`), submits approved decision with rationale. | Status transitions `pending -> in_review -> approved`. Stale version submissions rejected with HTTP 409 Conflict. | Gate 3 | **PASS** |
| **SCEN-007** | Audit Integrity | Append-Only Audit Trail Verification | Review decision submitted. | Attacker attempts `UPDATE` or `DELETE` on audit trail table or endpoint. | All direct modifications rejected. Audit log maintains cryptographic append-only event sequence with timestamp and actor ID. | Gate 3 | **PASS** |
| **SCEN-008** | Operations | Worker Crash Lease Recovery | Long-running extraction job queued; worker process terminated mid-execution. | Worker killed via `SIGKILL` while holding lease. Recovery scanner invoked. | Lease heartbeat expires; job returned to `queued` status and processed by recovery worker. Dead-letter queue on max retries. | Gate 4 | **PASS** |
| **SCEN-009** | Security | Multi-Tenant IDOR Defense & Isolation | Tenant A uploads sensitive NDA; Tenant B attempts retrieval using Tenant A document ID. | `GET /v1/documents/{doc_id_A}` with Tenant B JWT. | Request denied with HTTP 404 Not Found (non-disclosing). Zero cross-tenant data or metadata leakage in SQLite/FAISS. | Gate 3 | **PASS** |
| **SCEN-010** | Workbench SPA | Web Workbench End-to-End User Journey | Browser client accessing `http://localhost:8000/`. | User loads documents, navigates chunks, queries Q&A, and executes review approvals. | Standalone HTML5 SPA functions without external CDNs. All API requests authenticated via local tenant context switcher. | Gate 4 | **PASS** |

---

## Scenario Verification Evidence References

- **SCEN-001:** [`tests/test_mvp_e2e_integration.py::test_end_to_end_ingestion_and_retrieval`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/tests/test_mvp_e2e_integration.py)
- **SCEN-002:** [`tests/test_extraction_fidelity.py`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/tests/test_extraction_fidelity.py) & [`tests/test_table_extraction_regression.py`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/tests/test_table_extraction_regression.py)
- **SCEN-003:** [`tests/test_benchmark_proof.py::test_submodular_packer_approximation_bound_proof`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/tests/test_benchmark_proof.py)
- **SCEN-004:** [`tests/test_mvp3_abstention.py::test_abstention_on_unanswerable_queries`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/tests/test_mvp3_abstention.py)
- **SCEN-005:** [`tests/test_mvp5_conflicts.py::test_detect_date_and_amount_conflicts`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/tests/test_mvp5_conflicts.py)
- **SCEN-006:** [`tests/test_mvp6_review_service.py::test_approve_decision`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/tests/test_mvp6_review_service.py)
- **SCEN-007:** [`tests/test_mvp6_review_audit.py::test_audit_event_immutability`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/tests/test_mvp6_review_audit.py)
- **SCEN-008:** [`tests/test_mvp8_job_recovery.py::test_worker_crash_recovery`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/tests/test_mvp8_job_recovery.py)
- **SCEN-009:** [`tests/security/test_tenant_route_isolation.py::test_http_api_cross_tenant_lifecycle_idor_defense`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/tests/security/test_tenant_route_isolation.py)
- **SCEN-010:** [`src/ui/workbench.py`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/src/ui/workbench.py) & [`tests/test_auth_guard.py::test_workbench_spa_public_accessibility`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/tests/test_auth_guard.py)
