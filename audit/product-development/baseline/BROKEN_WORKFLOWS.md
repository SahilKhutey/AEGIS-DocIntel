# AEGIS-DocIntel Broken Workflows & Technical Debt Register

**Document Version:** 1.0.0  
**Phase Reference:** PROT-FINAL-10 (Work Package PD-01)  
**Date:** 2026-11-19  
**Status:** COMPLETE  

---

## 1. Overview

This document catalogs known workflow limitations, brittle dependencies, partial implementations, and areas of architectural tension uncovered during the **PD-01 Baseline Audit**. These items represent the primary engineering targets for **PROT-FINAL-11 (Core Document Processing Engine Restoration)** and subsequent sprints.

---

## 2. Identified Workflow Gaps and Technical Debt

### Issue BW-001: Fragmented Document Lifecycle State Tracking
- **Severity:** HIGH (Architectural)
- **Subsystem:** Ingestion / Operations / Storage
- **Observed Behavior:**
  - `RealDocumentService` in `src/services/container.py` historically managed a 4-state lifecycle (`processing`, `ready`, `failed`, `deleting`).
  - `JobService` in `src/operations/job_service.py` managed a separate 6-state lifecycle (`queued`, `running`, `retry_wait`, `succeeded`, `failed`, `cancelled`).
  - There was no unified state machine mapping intermediate processing stages (`VALIDATING`, `ACCEPTED`, `EXTRACTING`, `PARSING`, `NORMALIZING`, `INDEXING`) to observable document records.
- **Impact:** If a document extraction or parsing step fails internally, the user sees a generic `failed` state without stage attribution or diagnostic reference.
- **Remediation Strategy:** Unify state management using `src/models/document_lifecycle.py` and enforce atomic state transitions across `DocumentService` and `JobService`.

---

### Issue BW-002: Insecure / Ambiguous Storage References
- **Severity:** MEDIUM (Security Hardening)
- **Subsystem:** Processing Contracts
- **Observed Behavior:**
  - Historical payloads in some early pipelines passed local filesystem paths directly in job requests (`payload={"file_path": "/tmp/upload.pdf"}`).
  - If unvalidated, client-supplied filesystem paths introduce path traversal risks (`../../etc/shadow`).
- **Impact:** Potential unauthorized file access in multi-tenant environments.
- **Remediation Strategy:** Mandate opaque storage identifiers (`DocumentSource.storage_reference`) via `src/models/processing_contract.py`, rejecting absolute or relative disk paths.

---

### Issue BW-003: External Dependency on Host Tesseract OCR Binary
- **Severity:** MEDIUM (Environment Sensitivity)
- **Subsystem:** Ingestion (`src/ingestion/ocr_engine.py`)
- **Observed Behavior:**
  - Scanned PDF and image extraction relies on PyTesseract invoking the host `tesseract` CLI.
  - In environments where `tesseract` is not installed or not in `$PATH` (e.g. standard developer workstations without OCR packages), OCR jobs log a warning and return empty text blocks.
- **Impact:** Evaluators running scanned PDFs on systems without Tesseract experience 0% text recall.
- **Remediation Strategy:** Package a standalone bundled OCR engine or provide clear containerized deployment documentation where Tesseract is pre-baked.

---

### Issue BW-004: Live External LLM Provider Unverified in Air-Gapped CI
- **Severity:** LOW (Operational)
- **Subsystem:** Intelligence (`src/engines/llm/llm_interface.py`)
- **Observed Behavior:**
  - Automated CI test suites execute against the deterministic `MockProvider`.
  - Live external API calls (e.g. OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet) require real external API keys and outbound internet egress.
- **Impact:** Provider schema drift or network timeout changes might remain undetected during purely offline CI test runs.
- **Remediation Strategy:** Implement an optional integration test suite executed during staging deployment rehearsals with sandbox egress permissions.

---

### Issue BW-005: Headless Frontend Mock Parity vs Live Backend Staging
- **Severity:** LOW (Verification)
- **Subsystem:** Frontend (`web/`)
- **Observed Behavior:**
  - Frontend Vitest and Playwright tests execute against MSW (Mock Service Worker) mocks.
  - While unit test coverage is comprehensive (100% of critical components), end-to-end user journeys through the live Caddy reverse proxy to the backend container require interactive manual verification.
- **Impact:** Potential CORS, cookie domain, or header mismatch during first-time evaluator local deployment.
- **Remediation Strategy:** Execute live Docker Compose staging rehearsals in Sprint 5 / Sprint 7.
