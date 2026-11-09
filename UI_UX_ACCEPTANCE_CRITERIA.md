# AEGIS-DocIntel — UI/UX Acceptance Criteria & Verification Matrix
**Document Identifier**: `AEGIS-DOCINTEL-UX-ACC-001`  
**Work Package**: `WP-UI-01: Product UX Architecture`  
**Version**: `2.0.0`  
**Classification**: Formal Quality Assurance & Verification Contract  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. Purpose & Verification Authority

This document defines the strict, measurable acceptance criteria that must be satisfied before Work Package `WP-UI-01` (and subsequent UI work packages `WP-UI-02` through `WP-UI-08`) can receive release certification. Every acceptance criterion is verifiable through automated CI test suites (Vitest, Playwright, Axe-core), static security scanners, or formal visual regression audits.

---

## 2. Acceptance Criteria by Dimension

### Dimension 1: Architecture & Modular Structure (AC-ARC)

| ID | Criterion Statement | Verification Method | Pass Threshold |
| :--- | :--- | :--- | :---: |
| **AC-ARC-001** | Modular Feature Organization: All frontend code must reside in self-contained feature folders under `web/src/features/` (`documents`, `processing`, `intelligence`, `evidence`, `compare`, `governance`, `advanced`, `analytics`) with clear boundary interfaces. | Static filesystem audit | 100% compliant |
| **AC-ARC-002** | Zero Backend Engine Reimplementation: The frontend must act strictly as a presentation and interaction layer over backend REST/WS contracts; no intelligence or mathematical engines may be reimplemented in client JavaScript. | Code review & static analysis | Zero duplicated logic |
| **AC-ARC-003** | Server-State Decoupling: Server data fetching, caching, and optimistic mutations must use TanStack Query; UI components must not execute raw fetch calls directly in `useEffect`. | ESLint / AST check | Zero unmanaged fetch calls |

---

### Dimension 2: Design Tokens & System Compliance (AC-DSN)

| ID | Criterion Statement | Verification Method | Pass Threshold |
| :--- | :--- | :--- | :---: |
| **AC-DSN-001** | Tokenized Color Palette: All UI components must consume standardized semantic color tokens (`--primary`, `--background`, `--surface`, `--evidence-highlight`, `--conflict-warning`, `--success-approved`). | Tailwind config inspection | Zero arbitrary raw hex codes in markup |
| **AC-DSN-002** | Typography & Spacing Scales: Font sizes, line heights, and padding/margin units must strictly adhere to the enterprise design scale defined in `WP-UI-02`. | Visual regression test | 100% token usage |
| **AC-DSN-003** | Dark/Light Palette Readiness: All components must support dynamic theming via CSS variables with identical information hierarchy in dark mode. | Playwright theme toggle suite | Pass in both themes |

---

### Dimension 3: Navigation & Discoverability (AC-NAV)

| ID | Criterion Statement | Verification Method | Pass Threshold |
| :--- | :--- | :--- | :---: |
| **AC-NAV-001** | 100% Feature Route Discoverability: Every implemented capability defined in `UI_ROUTE_AND_PAGE_REGISTER.csv` must be reachable via the primary sidebar or command palette without typing manual URLs. | Automated crawler crawl test | 0 unreachable routes |
| **AC-NAV-002** | Universal Command Palette (`Ctrl+K`): Pressing `Ctrl+K` must instantly open the modal palette with fuzzy-search matching documents, routes, review items, and quick actions within < 50ms. | Playwright E2E keyboard test | Latency < 50ms, 100% matches |
| **AC-NAV-003** | Stateful Deep Linking: Navigating to deep URLs with query parameters (e.g. `?citation=ev-42`, `?status=pending`) must accurately restore active tabs, filters, and inspector states on fresh reload. | Browser refresh test | 100% state restoration |
| **AC-NAV-004** | Navigable Breadcrumb Trails: All child routes deeper than root must render breadcrumb trails enabling single-click navigation back to parent collections. | Vitest / E2E assertion | 100% breadcrumb coverage |

---

### Dimension 4: End-to-End Workflow Completeness (AC-WRK)

| ID | Workflow | Criterion Statement | Verification Method |
| :--- | :--- | :--- | :--- |
| **AC-WRK-001** | **Ingestion** | Drag-and-dropping a 50MB PDF must calculate SHA-256 fingerprint, attach idempotency key, initiate multipart upload, and display real-time stage progress (OCR -> Layout -> Graph -> Ready) without UI freeze. | Playwright E2E upload test |
| **AC-WRK-002** | **Grounded QA** | Submitting a question in "Ask AEGIS" must stream tokenized answers via SSE, display sub-query decomposition, and render interactive citation badges linking to verifiable evidence. | Playwright streaming test |
| **AC-WRK-003** | **Evidence Canvas** | Clicking any citation badge must open the Evidence Studio, navigate to the target PDF page, and draw a highlighted vector bounding box matching backend element coordinates. | Canvas bounding box inspection |
| **AC-WRK-004** | **Contradictions** | Comparing two conflicting documents must generate a side-by-side contradiction matrix highlighting mismatched terms with one-click escalation to the review queue. | E2E compare & escalate test |
| **AC-WRK-005** | **Governance** | A reviewer must be able to claim a review item, review source evidence, submit a sovereign 4-way decision (Approve/Correct/Reject/Request Evidence) with mandatory rationale, and record an immutable audit event. | E2E review decision test |
| **AC-WRK-006** | **Self-Healing** | A failed background job in `/processing` must display the exact backend error code and provide a working `Retry Job` action that resets attempts and reschedules worker execution. | E2E job retry simulation |

---

### Dimension 5: Backend Integration & Contract Fidelity (AC-INT)

| ID | Criterion Statement | Verification Method | Pass Threshold |
| :--- | :--- | :--- | :---: |
| **AC-INT-001** | Zero Mocked Production Data: All live views must source data exclusively from verified backend FastAPI endpoints; zero mock fixtures may be shipped in production builds. | Static code scan for mock flags | Zero production mocks |
| **AC-INT-002** | Strict Zod Contract Validation: 100% of API responses must be parsed through strict Zod schemas; malformed payloads must trigger typed `ApiError` instances rather than silent UI crashes. | Unit test schema parsing | 100% schema coverage |
| **AC-INT-003** | Request ID Provenance: Every failed API request must capture the backend `X-Request-ID` and display it in the error recovery banner for support tracing. | Error state component test | 100% request ID capture |

---

### Dimension 6: Security, Multi-Tenancy & Zero Dev-Token Leakage (AC-SEC)

| ID | Criterion Statement | Verification Method | Pass Threshold |
| :--- | :--- | :--- | :---: |
| **AC-SEC-001** | Zero Dev-Mode Token Fallback: The API client must NOT contain any fallback bearer tokens (such as `dev-default-tenant`). Production builds must reject missing auth configurations. | CI regex security scanner | PASS (0 occurrences) |
| **AC-SEC-002** | Authenticated Tenant Scoping: The UI shell must display the verified tenant ID from claims; all API calls must inject the active tenant context header (`X-Tenant-ID`). | Network request inspection | 100% tenant header injection |
| **AC-SEC-003** | DOM XSS Sanitization: All raw document chunks, markdown explanations, and user rationales must be sanitized via DOMPurify before rendering into the DOM. | Automated XSS payload fuzzing | Zero XSS execution |
| **AC-SEC-004** | RBAC Mutation Gating: Action buttons requiring elevated permissions (e.g., Delete Document, Reschedule Job, Submit Review) must be disabled or hidden for unauthorized roles. | Role permission matrix test | 100% authorization gate |

---

### Dimension 7: Accessibility & Inclusivity (AC-A11Y)

| ID | Criterion Statement | Verification Method | Pass Threshold |
| :--- | :--- | :--- | :---: |
| **AC-A11Y-001** | WCAG 2.1 AA Compliance: All pages must achieve a 100% zero-violation score on automated Axe-core accessibility audits. | `@axe-core/playwright` CI scan | 0 critical/serious violations |
| **AC-A11Y-002** | Complete Keyboard Operability: Review queues, document tables, modals, and QA inputs must be operable using keyboard only (`Tab`, `Enter`, `Space`, `Esc`, `J`/`K`). | Headless keyboard traversal | 100% interactive controls |
| **AC-A11Y-003** | Contrast Ratios: Normal text must have at least 4.5:1 contrast; large text and graphical controls must have at least 3:1 contrast against backgrounds. | Axe contrast checker | 100% passing elements |

---

### Dimension 8: Responsive Layouts & Breakpoints (AC-RSP)

| ID | Viewport | Resolution | Acceptance Requirement |
| :--- | :--- | :--- | :--- |
| **AC-RSP-001** | **Desktop** | `>= 1280px` | Full 3-pane layout (Sidebar 260px, Central Workspace, Contextual Inspector 420px) without horizontal scrolling. |
| **AC-RSP-002** | **Laptop** | `1024px - 1279px` | Collapsed icon sidebar (68px); Contextual Inspector operates as slide-over overlay. |
| **AC-RSP-003** | **Tablet** | `768px - 1023px` | Off-canvas drawer sidebar; stacked central workspace; inspector opens as responsive bottom sheet. |
| **AC-RSP-004** | **Mobile** | `< 768px` | Off-canvas hamburger menu + sticky bottom action bar; data tables convert to touch-friendly card layouts. |

---

### Dimension 9: Automated Test Coverage Baseline (AC-TST)

| ID | Test Suite | Scope | Target Threshold |
| :--- | :--- | :--- | :---: |
| **AC-TST-001** | Vitest Unit & Component Tests | Schemas, API client, error handling, review decisions, badge status, and evidence panels. | `>= 85%` branch coverage |
| **AC-TST-002** | Playwright Browser E2E Tests | End-to-end user journeys for Ingestion, Ask AEGIS, Compare, and Governance Review workflows. | 100% passing scenarios |
| **AC-TST-003** | TypeScript Static Compilation | Complete project compilation via `tsc --noEmit` with `strict: true`. | Zero type errors |
| **AC-TST-004** | ESLint Code Quality Gate | Zero-tolerance linting enforcing React hook invariants and import hygiene. | Zero warnings, zero errors |

---

### Dimension 10: Performance & Resilience (AC-PRF)

| ID | Metric | Target Specification | Verification Method |
| :--- | :--- | :--- | :---: |
| **AC-PRF-001** | Largest Contentful Paint (LCP) | `< 1.5 seconds` on desktop under standard broadband. | Lighthouse audit in CI |
| **AC-PRF-002** | Interaction to Next Paint (INP) | `< 100 milliseconds` for all button clicks and table filters. | Chrome Web Vitals trace |
| **AC-PRF-003** | Streaming Token Render Latency | First streaming token visible in UI within `< 200 milliseconds` of backend dispatch. | Network streaming benchmark |
| **AC-PRF-004** | React Error Boundaries | Component errors must render a local recovery box with "Try Again" without unmounting the application shell. | Fault injection test |
| **AC-PRF-005** | Stream Auto-Reconnection | Dropped SSE connections must reconnect automatically with exponential backoff up to 5 attempts. | Disconnect simulation test |

---

## 3. Work Package Sign-Off Protocol

Release certification for any UI work package requires formal verification:
1. Automated CI run passing all 10 quality gates.
2. Signed-off traceability report confirming every requirement has a passing test ID.
3. Verification report archived in `artifacts/ui_verification/` with SHA-256 integrity hash.
