# AEGIS-DocIntel — UI/UX Requirements Specification
**Document Identifier**: `AEGIS-DOCINTEL-UX-REQ-001`  
**Work Package**: `WP-UI-01: Product UX Architecture`  
**Version**: `2.0.0`  
**Classification**: Formal Engineering Specification  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. Scope & Purpose

This specification defines the exhaustive functional and non-functional requirements for the frontend user interface and user experience of **AEGIS-DocIntel (AEGIS Workbench 2.0)**. It serves as the binding contract for engineering implementation, component design, automated testing, and release auditing.

---

## 2. Functional Requirements (FR)

### Module 1: Application Shell, Navigation & Authentication Session (FR-SHL)

| Requirement ID | Title | Description | Priority | Target Persona |
| :--- | :--- | :--- | :---: | :--- |
| **FR-SHL-001** | Persistent Dual-Tier Navigation | The shell must provide a persistent, collapsible left sidebar for primary workspaces and a responsive top header for workspace context and profile controls. | P0 | All |
| **FR-SHL-002** | Authenticated Multi-Tenant Switcher | The UI must display the active tenant identifier extracted from the verified session claims and provide a dropdown switcher for users with multi-tenant access. | P0 | Admin, Analyst |
| **FR-SHL-003** | Secure Session & Zero Dev Tokens | The application must authenticate using standard JWT Bearer tokens or API keys stored in secure memory/HTTP-only cookies. Hardcoded development tokens are strictly forbidden in production builds. | P0 | All |
| **FR-SHL-004** | Role-Based Navigation Filtering | Navigation items and operational buttons must automatically reflect the active user's RBAC role, hiding or disabling actions exceeding user permissions. | P0 | All |
| **FR-SHL-005** | Global Command Palette (`Ctrl+K`) | A modal command palette must be accessible via keyboard shortcut (`Ctrl+K` or `Cmd+K`) enabling instant fuzzy-search navigation across documents, review items, and commands. | P1 | Knowledge Eng, Analyst |
| **FR-SHL-006** | Real-Time System Health Indicator | The top header must display a live status pill (Operational, Degraded, Critical) driven by periodic polling or WebSocket alerts from `/health` and `/readiness`. | P1 | System Admin |
| **FR-SHL-007** | Global Notification Center | An in-app notification drawer must aggregate asynchronous job completions, pipeline failure alerts, review assignments, and system advisories. | P1 | All |
| **FR-SHL-008** | Dynamic Breadcrumbs | Every deep route (e.g., `/documents/[documentId]`, `/reviews/[reviewId]`) must render navigable breadcrumb trails with document title or item ID truncations. | P1 | All |

---

### Module 2: Document Ingestion, Batch Upload & Library Management (FR-DOC)

| Requirement ID | Title | Description | Priority | Target Persona |
| :--- | :--- | :--- | :---: | :--- |
| **FR-DOC-001** | Multi-Format Drag-and-Drop Ingestion | The upload modal must support drag-and-drop ingestion of PDF, DOCX, XLSX, scanned TIFF/PNG, and audio formats with client-side file size and MIME-type validation. | P0 | Knowledge Eng, Analyst |
| **FR-DOC-002** | Pre-Flight Virus & PII Scan Options | The upload dialog must offer optional pre-ingestion toggles for automated PII entity scanning/redaction (`/v1/advanced/compliance/pii-scan`) and anomaly checks. | P1 | Compliance Officer |
| **FR-DOC-003** | Batch Ingestion via S3 Manifest | Support batch document registration via S3 manifest JSON payloads with immediate job dispatch (`/v1/documents/batch`). | P1 | System Admin |
| **FR-DOC-004** | Idempotent Upload Handling | Every upload request must generate a client-side UUID idempotency key to prevent duplicate document submissions during network blips. | P0 | All |
| **FR-DOC-005** | Document Library Filter & Search | The document library table must support real-time full-text search, status filtering (`pending`, `indexing`, `ready`, `failed`, `reindexing`), date range filters, and pagination. | P0 | All |
| **FR-DOC-006** | Document Deletion & Lifecycle Management | Authorized users must be able to delete documents (`DELETE /v1/documents/{doc_id}`) with double-confirmation dialog and cascade preview (chunks, embeddings, facts). | P0 | Tenant Admin |
| **FR-DOC-007** | Reindexing Trigger | Provide an action to trigger reindexing (`POST /v1/documents/{doc_id}/reindex`) with parameter overrides for chunking strategy and embedding models. | P1 | Knowledge Eng |
| **FR-DOC-008** | Document Chunk & Layout Inspector | Dedicated view (`/documents/[documentId]`) showing paginated text chunks, token counts, section hierarchies, and layout element coordinates (`/v1/documents/{doc_id}/elements`). | P0 | Knowledge Eng, Analyst |

---

### Module 3: Pipeline Monitoring & Background Job Execution (FR-JOB)

| Requirement ID | Title | Description | Priority | Target Persona |
| :--- | :--- | :--- | :---: | :--- |
| **FR-JOB-001** | Real-Time Pipeline Progress Timeline | Visual stage tracker for active document processing: Ingestion -> Parsing -> OCR -> Layout -> Graphs -> Embeddings -> Ready. | P0 | Knowledge Eng, Analyst |
| **FR-JOB-002** | Background Job Dashboard | Dedicated dashboard (`/processing`) listing all active, queued, failed, and completed background jobs (`GET /v1/jobs`) with live SSE progress updates. | P0 | System Admin, Analyst |
| **FR-JOB-003** | Job Retry & Rescheduling | Authorized users can manually reschedule failed or cancelled background jobs (`POST /v1/jobs/{job_id}/retry`) with fresh attempt counters. | P0 | System Admin |
| **FR-JOB-004** | Active Job Cancellation | Support cancelling pending or running background jobs (`POST /v1/jobs/{job_id}/cancel`) with cancellation rationale recording. | P0 | System Admin |
| **FR-JOB-005** | Audit Event & Attempt History Inspector | Inspect the detailed execution attempts, worker lease owners, error codes, and audit logs for any job (`GET /v1/jobs/{job_id}/events`). | P1 | System Admin |
| **FR-JOB-006** | Dead-Letter Queue (DLQ) Diagnostic Viewer | Surface poison messages and repeated job failures with stack traces, root cause diagnostics, and payload inspection. | P1 | System Admin |

---

### Module 4: "Ask AEGIS", Query Decomposition & Grounded Intelligence (FR-INT)

| Requirement ID | Title | Description | Priority | Target Persona |
| :--- | :--- | :--- | :---: | :--- |
| **FR-INT-001** | Tri-Pane Grounded QA Console | Flagship interface featuring: Left (Document/Collection Selector), Center (Query Formulation & Streaming Answer), Right (Contextual Evidence Inspector). | P0 | Analyst, Researcher |
| **FR-INT-002** | Real-Time Token & Answer Streaming | Stream generated responses in real-time via Server-Sent Events (SSE) or WebSocket streaming with instant citation badges. | P0 | Analyst, Researcher |
| **FR-INT-003** | Sub-Query Decomposition Viewer | Visual breakout displaying how complex multi-hop queries were decomposed into atomic retrieval sub-queries (`POST /v1/advanced/query/decompose`). | P1 | Knowledge Eng |
| **FR-INT-004** | Grounded Citation Highlighting | Citations in generated answers must be clickable numbered badges (`[1]`, `[2]`) that immediately illuminate the exact source chunk in the evidence panel. | P0 | All |
| **FR-INT-005** | Insufficient Evidence & Warning States | Explicit warning callouts when retrieved context does not meet confidence thresholds, alerting the user to missing facts rather than hallucinating. | P0 | All |
| **FR-INT-006** | Hybrid Retrieval Parameter Tuning | Drawer allowing advanced users to adjust hybrid search weighting (dense vector vs sparse BM25, reranker threshold, top-k). | P2 | Knowledge Eng |
| **FR-INT-007** | Query History & Saved Inquiries | Persist past queries per user session with pinned answers and exportable markdown summaries. | P1 | Analyst |

---

### Module 5: Interactive Evidence Studio & Bounding Box Viewer (FR-EVD)

| Requirement ID | Title | Description | Priority | Target Persona |
| :--- | :--- | :--- | :---: | :--- |
| **FR-EVD-001** | Side-by-Side Synchronized PDF/Image Viewer | Visual canvas rendering the raw document page with highlighted vector bounding boxes matching active citation coordinates. | P0 | Compliance, Analyst |
| **FR-EVD-002** | Deep Evidence Inspection | Display exact chunk text, page index, section path hierarchy, token count, and cosine similarity/relevance score for any selected evidence item. | P0 | All |
| **FR-EVD-003** | Annotation & Note Creation | Allow users to highlight passages, attach notes, and submit corrections directly on the document canvas (`POST /v1/annotations/`). | P1 | Reviewer, Analyst |
| **FR-EVD-004** | Multi-Document Evidence Tabs | When an answer cites multiple documents, the evidence panel provides tabs to switch seamlessly between source artifacts. | P0 | Analyst |

---

### Module 6: Document Comparison, Fact Extraction & Contradiction Matrix (FR-CMP)

| Requirement ID | Title | Description | Priority | Target Persona |
| :--- | :--- | :--- | :---: | :--- |
| **FR-CMP-001** | Pairwise Document Comparison Console | Select two documents (or two versions of the same document) to trigger deep structural and factual comparison (`POST /v1/intelligence/compare`). | P0 | Legal Reviewer, Analyst |
| **FR-CMP-002** | Structured Fact Extraction Grid | Extract and display typed facts (Subject, Attribute, Value, Unit, Confidence, Evidence Quote) per document (`POST /v1/documents/{id}/extract-facts`). | P0 | Analyst, Reviewer |
| **FR-CMP-003** | Cross-Document Contradiction Matrix | Visual matrix highlighting conflicting facts between documents (e.g., conflicting interest rates, mismatched liability terms, differing dates). | P0 | Legal, Compliance |
| **FR-CMP-004** | Visual Document Version Diff | Side-by-side visual diff of document revisions highlighting added, modified, and deleted clauses (`POST /v1/advanced/versioning/diff`). | P1 | Legal, Compliance |
| **FR-CMP-005** | Escalate Conflict to Governance | One-click escalation allowing an analyst to push a detected conflict directly into the human review queue. | P0 | Analyst |

---

### Module 7: Human Governance Review Queue & Immutable Audit (FR-GOV)

| Requirement ID | Title | Description | Priority | Target Persona |
| :--- | :--- | :--- | :---: | :--- |
| **FR-GOV-001** | Unified Review Queue | Prioritized list of candidate facts and conflicts awaiting human evaluation (`GET /v1/reviews`), filterable by status, candidate type, and assignee. | P0 | Reviewer, Compliance |
| **FR-GOV-002** | Review Claim & Lock Mechanism | Reviewers can claim a review item (`POST /v1/reviews/{id}/claim`) to prevent concurrent race conditions; unclaiming releases the lock after timeout. | P0 | Reviewer |
| **FR-GOV-003** | 4-Way Decision Action Framework | Reviewers can record one of four sovereign decisions: **Approve**, **Correct**, **Reject**, or **Request Evidence** (`POST /v1/reviews/{id}/decisions`). | P0 | Reviewer |
| **FR-GOV-004** | Structured Correction Workflow | When "Correct" is selected, the UI provides fields to input corrected value, corrected data type, units, and mandatory explanation rationale. | P0 | Reviewer |
| **FR-GOV-005** | Immutable Audit Event Stream | Render a chronological, tamper-evident audit history of all state transitions, actor IDs, timestamps, and revision IDs (`GET /v1/reviews/{id}/history`). | P0 | Compliance Auditor |
| **FR-GOV-006** | Administrative Reopen Capability | Authorized governance administrators can reopen finalized reviews with audit logging (`POST /v1/reviews/{id}/reopen`). | P1 | Tenant Admin |
| **FR-GOV-007** | Governance Metrics Dashboard | Display approval rates, correction frequencies, rejection ratios, and reviewer turnaround times (`GET /v1/reviews/metrics`). | P1 | Governance Lead |

---

### Module 8: Advanced Mathematical & Knowledge Representation (FR-MTH)

| Requirement ID | Title | Description | Priority | Target Persona |
| :--- | :--- | :--- | :---: | :--- |
| **FR-MTH-001** | Knowledge Graph Visualizer | Interactive node-link graph visualizer displaying extracted entities, relationships, confidence weights, and document provenance links. | P1 | Knowledge Eng, Researcher |
| **FR-MTH-002** | Topological Percolation Resilience Gauge | Visual gauge displaying network resilience and information percolation thresholds (`GET /v1/advanced/topology/percolation-check`). | P2 | Knowledge Eng |
| **FR-MTH-003** | Ising Annealing Objective Optimizer | Visual interface to configure objective functions and run Ising spin optimization for multi-constraint document extraction. | P2 | Researcher |
| **FR-MTH-004** | Matrix & Unit Normalization Sandbox | Interactive table cell inspector converting raw textual values into standardized SI units or canonical financial dimensions. | P1 | Knowledge Eng |

---

### Module 9: System Observability, Telemetry & Token Economy (FR-OBS)

| Requirement ID | Title | Description | Priority | Target Persona |
| :--- | :--- | :--- | :---: | :--- |
| **FR-OBS-001** | Operational Dashboard (Command Center) | Operational overview displaying live throughput, active documents, running jobs, pending reviews, and worker latencies. | P0 | All |
| **FR-OBS-002** | Token Consumption & Cost Breakdown | Charts detailing prompt tokens, completion tokens, cached tokens, and estimated cost savings achieved via RAG (`GET /v1/admin/token-usage`). | P1 | Tenant Admin |
| **FR-OBS-003** | Request Latency & P99 Telemetry | Real-time charts showing P50, P90, and P99 API response latencies and document indexing durations. | P1 | System Admin |

---

### Module 10: Administration, Security & Integration Hub (FR-ADM)

| Requirement ID | Title | Description | Priority | Target Persona |
| :--- | :--- | :--- | :---: | :--- |
| **FR-ADM-001** | Webhook Subscription Management | Create, test, list, and delete outbound webhook endpoints for ingestion and governance events (`/v1/webhooks/subscriptions`). | P1 | Integration Eng |
| **FR-ADM-002** | API Key Provisioning & Scopes | Generate and revoke tenant-scoped API keys with role restrictions and usage limits. | P0 | Tenant Admin |
| **FR-ADM-003** | PII Detection & Redaction Rules | Configure automated PII detection sensitivity thresholds and redaction replacement patterns. | P1 | Compliance Officer |

---

## 3. Non-Functional Requirements (NFR)

### 3.1 Performance & Latency (NFR-PERF)

| ID | Metric | Target Specification | Verification Method |
| :--- | :--- | :--- | :--- |
| **NFR-PERF-001** | Largest Contentful Paint (LCP) | < 1.5 seconds on desktop under standard broadband (10 Mbps). | Lighthouse / Playwright performance run |
| **NFR-PERF-002** | First Input Delay (FID) / INP | Interaction to Next Paint < 100 milliseconds for all clicks and inputs. | Chrome Web Vitals in E2E tests |
| **NFR-PERF-003** | Streaming Token Render Latency | First streaming token rendered in UI within 200ms of backend dispatch. | Network trace & streaming component test |
| **NFR-PERF-004** | Client Bundle Size Budget | Total initial JS bundle < 250 KB gzipped; dynamic code-splitting for heavy graph visualizers. | Next.js build bundle analyzer |
| **NFR-PERF-005** | Large Document List Virtualization | Smooth 60 FPS scrolling for libraries containing > 5,000 documents via DOM windowing/virtualization. | TanStack Virtual test harness |

---

### 3.2 Accessibility & Usability (NFR-A11Y)

| ID | Standard | Specification | Verification Method |
| :--- | :--- | :--- | :--- |
| **NFR-A11Y-001** | WCAG 2.1 AA Compliance | All interactive components, colors, and typography must pass WCAG 2.1 AA contrast and navigation standards. | Axe Core automated CI scan |
| **NFR-A11Y-002** | Full Keyboard Navigability | Every user workflow (upload, search, review, compare) must be fully operable without mouse interaction. | Playwright keyboard traversal suite |
| **NFR-A11Y-003** | ARIA Semantics & Live Regions | Streaming answers, progress bars, and modal state transitions must use proper `aria-live`, `aria-busy`, and roles. | Screen reader audit (NVDA/VoiceOver) |
| **NFR-A11Y-004** | High Contrast & Dark Theme | Design tokens must support seamless switching between standard daylight, high contrast, and dark theme palettes. | Visual regression tests |

---

### 3.3 Security, Data Protection & Privacy (NFR-SEC)

| ID | Requirement | Specification | Verification Method |
| :--- | :--- | :--- | :--- |
| **NFR-SEC-001** | Zero Dev-Mode Token Leakage | Production frontend bundles must contain zero fallback tokens (e.g. `dev-default-tenant`). Builds must fail if detected. | CI static security regex scanner |
| **NFR-SEC-002** | XSS Prevention & Sanitization | All raw document text, chunks, and LLM generated markdown must be strictly sanitized via DOMPurify before render. | Security penetration test suite |
| **NFR-SEC-003** | CSRF & Frame-Options Defense | All mutation requests must include anti-CSRF headers; UI shell must set `X-Frame-Options: DENY`. | HTTP header verification |
| **NFR-SEC-004** | Tenant Isolation Enforcement | UI must strictly prevent crossing tenant boundaries; all API calls must automatically inject active tenant headers. | Multi-tenant integration tests |
| **NFR-SEC-005** | Client-Side PII Masking | PII entities flagged by backend must be masked by default in the UI until explicitly revealed by authorized roles. | Role permission test suite |

---

### 3.4 Reliability, Fault Tolerance & Error Handling (NFR-REL)

| ID | Metric | Specification | Verification Method |
| :--- | :--- | :--- | :--- |
| **NFR-REL-001** | Graceful Error Boundaries | React Error Boundaries must isolate failing widgets (e.g., PDF viewer crash) without crashing the primary shell. | Vitest error boundary test |
| **NFR-REL-002** | Automatic SSE/WS Reconnection | Real-time streams must implement exponential backoff reconnection with heartbeat monitoring. | Network disconnect simulation test |
| **NFR-REL-003** | Standardized API Error Recovery | All HTTP 4xx/5xx responses must render actionable user messages displaying request IDs and retry actions. | Error state component test |
| **NFR-REL-004** | Offline State Awareness | The UI must detect network disconnections, display an offline banner, and queue mutations safely. | Browser offline mode test |

---

## 4. Requirements Traceability Matrix Summary

Every functional requirement (FR-SHL, FR-DOC, FR-JOB, FR-INT, FR-EVD, FR-CMP, FR-GOV, FR-MTH, FR-OBS, FR-ADM) is mapped directly to corresponding user personas, application routes, backend endpoints, and automated Playwright/Vitest test suites in `REQUIREMENTS_TRACEABILITY.csv` and `UI_API_INTEGRATION_MATRIX.csv`.
