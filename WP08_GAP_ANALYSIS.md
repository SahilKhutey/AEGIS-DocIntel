# AEGIS-DocIntel — WP-08: Gap Analysis

> **Work Package**: WP-08 — Integration  
> **Status**: **GAPS IDENTIFIED & REMEDIATION ROADMAP SPECIFIED**  
> **Date**: 2026-11-04  
> **Target Branch**: `wp-08-integration`  

---

## 1. Executive Summary

This Gap Analysis identifies the specific missing links between isolated subsystem tests and a fully verified, integrated, and deployable product. While WP-01 through WP-07 established verified baselines for audit, data acquisition, extraction, intelligence, and security, WP-08 bridges these components across live runtime boundaries.

---

## 2. Work Item Gap Inventory

### 2.1 WP-08.01 — Frontend CI
| Item / Requirement | Current State | Identified Gap | Remediation Action |
| :--- | :--- | :--- | :--- |
| **Lint & Formatting** | ESLint 9 present | 2 React Hook `useEffect` dependency warnings in `documents/[documentId]` and `reviews/[reviewId]`. | Remediate hook dependencies using `useCallback` to achieve 0 warnings and 0 errors. |
| **Automated Reports** | GitHub workflow runs inline | No machine-readable JSON build or CI reports produced. | Implement automated frontend CI benchmark generator outputting `FRONTEND_CI_TEST_REPORT.json` and `FRONTEND_BUILD_REPORT.json`. |
| **A11y & Security** | Manual inspection | Automated accessibility checks and dependency vulnerability audits are not formalized in CI. | Add automated accessibility audit rules and npm audit scanning. |
| **Negative CI Scenarios** | Untested | Scenarios `FE-CI-001` through `FE-CI-010` (type errors, lint failures, broken builds) lack automated regression tests. | Build an automated validation test script verifying that deliberate type/lint/build faults are caught. |

---

### 2.2 WP-08.02 — API Contract Tests
| Item / Requirement | Current State | Identified Gap | Remediation Action |
| :--- | :--- | :--- | :--- |
| **Endpoint Inventory** | Code spread across routers | No central, versioned `API_ENDPOINT_INVENTORY.csv`. | Compile comprehensive endpoint inventory documenting methods, paths, auth schemes, schemas, and tenant scoping. |
| **Contract Source of Truth** | `openapi.json` at root | Not automatically validated against frontend Zod schemas in `web/src/lib/schemas.ts`. | Build bidirectional contract test suite verifying that FastAPI response schemas strictly match frontend expectations. |
| **Async Polling & Idempotency** | Implemented in backend | Integration tests for polling transitions (`202 Accepted` -> `pending` -> `ready` / `failed`) and repeated submissions are needed. | Implement deterministic contract test suite covering `API-001` through `API-015`. |
| **Anti-IDOR HTTP 404** | Implemented in WP-07 | API contract verification must assert that cross-tenant lookups never return HTTP 403 or expose document existence. | Include negative cross-tenant scenarios in API contract test suite. |

---

### 2.3 WP-08.03 — Browser E2E
| Item / Requirement | Current State | Identified Gap | Remediation Action |
| :--- | :--- | :--- | :--- |
| **User Journey Coverage** | 4 smoke tests in `workbench.spec.ts` | Missing end-to-end tests for upload modal, search, QA asking, citation inspection, fact review, conflict comparison, report download, cascading deletion, and session expiry. | Implement Playwright test suite covering all 18 core scenarios (`E2E-001` through `E2E-018`). |
| **Failure & Recovery** | Happy path only | No automated verification of network drops, API unavailable errors, or timeout handling in the browser. | Add negative browser scenarios and failure trace captures. |
| **E2E Evidence Generation** | Terminal stdout | Missing standardized `BROWSER_E2E_TEST_REPORT.json` and `BROWSER_FAILURE_ANALYSIS.md`. | Build automated runner generating structured execution reports and trace artifacts. |

---

### 2.4 WP-08.04 — Complete Document-to-Report Workflow
| Item / Requirement | Current State | Identified Gap | Remediation Action |
| :--- | :--- | :--- | :--- |
| **Corpus Binding** | WP-04 corpus exists | Golden test documents are not yet bound into an end-to-end pipeline specification. | Create `WP08_END_TO_END_TEST_CORPUS.md` and `WP08_WORKFLOW_SPECIFICATION.md`. |
| **Intermediate Assertions** | Subsystems tested in isolation | Pipeline is tested piecemeal (WP-05 separately from WP-06). A single continuous run validating upload -> extraction -> layout -> reading order -> tables -> provenance -> indexing -> retrieval -> QA -> citations -> facts -> conflicts -> report -> export is missing. | Implement unified end-to-end workflow runner covering scenarios `WF-001` through `WF-010`. |
| **Run Manifests** | Evaluation manifest in WP-03 | Missing immutable workflow run manifest schema (`WP08_WORKFLOW_RUN_MANIFEST.schema.json`) recording dataset version, commit SHA, and stage timings. | Create manifest schema and generate execution manifests. |
| **Performance Metrics** | Isolated benchmarks | Missing end-to-end latency and stage timing metrics for the full pipeline. | Measure stage durations and compile `DOCUMENT_TO_REPORT_PERFORMANCE.json`. |

---

### 2.5 WP-08.05 — Deployment Configuration
| Item / Requirement | Current State | Identified Gap | Remediation Action |
| :--- | :--- | :--- | :--- |
| **Deployment Register** | Docker Compose present | Missing formal `WP08_DEPLOYMENT_ARCHITECTURE.md`, `DEPLOYMENT_ENVIRONMENT_MATRIX.csv`, and `ENVIRONMENT_VARIABLE_REGISTER.md`. | Document multi-tier architecture, environment separation, and configuration variable classifications. |
| **Health & Readiness** | Basic `/health` endpoint | No distinct liveness, readiness, and dependency health checks for DB, Redis, and MinIO S3. | Validate health probe structure and error behavior without exposing infrastructure secrets. |
| **Staging & Rollback Drills** | Static compose file | No automated verification of clean staging deployment, smoke testing, and database rollback procedures. | Execute clean-environment staging deployment verification and test rollback failure handling. |

---

### 2.6 Central Audit Integration
| Item / Requirement | Current State | Identified Gap | Remediation Action |
| :--- | :--- | :--- | :--- |
| **Audit Suite** | 8 suites currently registered | Central audit runner needs an `IntegrationAuditSuite` verifying all 5 integration gates. | Update and register `IntegrationAuditSuite` in `aegis/audit/runner/engine.py` and `configs/audit/default.yaml` to achieve 9/9 passing suites with 0 findings. |

---

## 3. Remediation Execution Plan

1. **Phase 1: Frontend Quality & CI (WP-08.01)**
   - Fix React hook warnings in `web/`.
   - Update `.github/workflows/frontend-ci.yml`.
   - Implement frontend CI benchmark runner and publish reports.
2. **Phase 2: API Contract Verification (WP-08.02)**
   - Generate `API_ENDPOINT_INVENTORY.csv`.
   - Implement `tests/integration/api_contract/` test suite (`API-001`..`015`).
   - Generate compatibility and schema reports.
3. **Phase 3: Browser E2E Suite (WP-08.03)**
   - Expand `web/tests/e2e/` for all 18 user journeys.
   - Run Playwright E2E and generate `BROWSER_E2E_TEST_REPORT.json`.
4. **Phase 4: Document-to-Report Workflow (WP-08.04)**
   - Define corpus bindings and workflow specifications (`WF-001`..`010`).
   - Implement end-to-end workflow runner and generate `DOCUMENT_TO_REPORT_TEST_REPORT.json`.
5. **Phase 5: Deployment Configuration & Staging (WP-08.05)**
   - Document deployment architecture, environment matrix, and variable registers.
   - Run staging deployment validation, health probes, and rollback drills.
6. **Phase 6: Central Audit & Release Acceptance**
   - Register `IntegrationAuditSuite` in `aegis.audit`.
   - Execute full repository audit (`python -m aegis.audit run --all`).
   - Author `WP08_FINAL_AUDIT.md` and user acceptance artifact.
