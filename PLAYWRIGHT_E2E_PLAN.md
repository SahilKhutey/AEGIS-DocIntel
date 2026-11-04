# AEGIS-DocIntel — WP-08.03: Playwright Browser E2E Plan

> **Work Package**: WP-08 — Integration (Work Item WP-08.03)  
> **Status**: **ACTIVE PLAN**  
> **Date**: 2026-11-04  
> **Test Framework**: Playwright 1.64.1 (`web/playwright.config.ts`)  
> **Target Application**: Next.js 16 Web Workbench (`web/src/app`)  

---

## 1. Objectives & Testing Principles

Browser End-to-End (E2E) testing validates that human operators and automated agents can navigate the AEGIS-DocIntel web workbench, authenticate, upload documents, track extraction progress, query intelligence with citations, inspect contradictions, export reports, and purge documents safely.

### Core User Experience Invariants
1. **Accurate Evidence Presentation**: Citations displayed in the browser must visually match the source document page, chunk text, and bounding box coordinates.
2. **Conflict Visibility**: Cross-document differences and contradictions must be explicitly highlighted in the comparison view rather than suppressed.
3. **Graceful Error Recovery**: Network timeouts, missing documents, or unanswerable queries must display clear, non-cryptic error banners and abstention notices without application crashes.
4. **Session & Security Boundaries**: Expired tokens or unauthorized role actions must immediately redirect to safe authentication boundaries without state corruption.

---

## 2. Core User Journey Scenarios Matrix

| Scenario ID | Journey / Capability | User Action | Expected Browser UI State |
| :--- | :--- | :--- | :--- |
| **E2E-001** | Valid Login | Submit valid tenant credentials | Navigates to `/documents` dashboard with active session banner |
| **E2E-002** | Invalid Login | Submit invalid password/token | Displays accessible error alert: "Invalid credentials" |
| **E2E-003** | Dashboard Navigation | Navigate header & sidebar | Header links, metrics summary, and workspace shell render |
| **E2E-004** | Valid PDF Upload | Select PDF in upload modal | Modal shows upload progress -> document registered with `pending` badge |
| **E2E-005** | Unsupported File Upload | Attempt uploading `.exe` / `.bmp` | Rejection banner displays supported formats (`PDF`, `DOCX`, `PPTX`) |
| **E2E-006** | Progress Telemetry | Poll status during indexing | Status badge transitions dynamically `pending` -> `indexing` -> `ready` |
| **E2E-007** | Extracted Document Viewer | Click document title | Document viewer renders metadata, text chunks, and page navigator |
| **E2E-008** | Document Full-Text Search | Input query in search box | Matching text blocks highlight with relevance scores |
| **E2E-009** | Question Answering | Submit question on `/ask` | Generated grounded answer displays with citation pills |
| **E2E-010** | Citation Inspection | Click citation badge | Evidence drawer opens highlighting exact quote and source page |
| **E2E-011** | Extracted Facts | Open Facts tab on document view | Structured entity triples render with temporal/spatial attributes |
| **E2E-012** | Cross-Document Conflicts | Select 2 docs on `/compare` | Contradiction cards display differing values, metrics, and timestamps |
| **E2E-013** | Report Generation | Click "Generate Report" | Summary and findings table synthesize into exportable view |
| **E2E-014** | Report Download | Click "Download Markdown/HTML" | Browser initiates file download matching structured report schema |
| **E2E-015** | Document Deletion | Click "Delete Document" | Confirmation prompt completes; document removed from listing |
| **E2E-016** | Logout Session | Click "Sign Out" | Session cleared; redirected to login/landing page |
| **E2E-017** | Restricted Access Guard | Non-admin visits admin route | Access denied notice renders; forbidden action buttons disabled |
| **E2E-018** | Expired Session Recovery | Action with expired token | Safe modal asks user to re-authenticate; preserves form draft |

---

## 3. Evidence Artifacts
- [`artifacts/integration/browser_e2e/BROWSER_E2E_TEST_REPORT.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/artifacts/integration/browser_e2e/BROWSER_E2E_TEST_REPORT.json)
- [`artifacts/integration/browser_e2e/BROWSER_FAILURE_ANALYSIS.md`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/artifacts/integration/browser_e2e/BROWSER_FAILURE_ANALYSIS.md)
