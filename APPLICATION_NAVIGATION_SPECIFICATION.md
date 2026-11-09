# AEGIS-DocIntel — Application Navigation Specification
**Document Identifier**: `AEGIS-DOCINTEL-UX-NAV-001`  
**Work Package**: `WP-UI-01: Product UX Architecture`  
**Version**: `2.0.0`  
**Classification**: Formal Engineering Specification  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. Executive Summary

This specification defines the complete navigation model, routing hierarchy, URL contracts, command palette specification, and responsive behavior for **AEGIS Workbench 2.0**. It upgrades the initial four-link navigation into a comprehensive, multi-tiered enterprise navigation architecture.

---

## 2. Navigation Architecture & Route Tree

The application is organized into ten distinct functional navigation groups:

```
/ (Workspace Root)
│
├── /overview ............................. Operational Command Center & Dashboard
│
├── /documents ............................ Document Library & Collection Explorer
│   ├── /documents/upload ................. Drag-and-drop & S3 manifest ingestion modal
│   └── /documents/[documentId] ........... Document Inspector (Overview, Chunks, Elements, Facts, Raw PDF)
│
├── /processing ........................... Pipeline Monitor & Background Jobs
│   ├── /processing/jobs .................. Active/Queued/Completed Jobs List
│   ├── /processing/jobs/[jobId] .......... Job Detail, Attempt History & Worker Leasing
│   └── /processing/dlq ................... Dead-Letter Queue & Poison Message Diagnostics
│
├── /ask .................................. "Ask AEGIS" Tri-Pane Grounded QA & Reasoning
│   └── /ask/history ...................... Past Inquiries, Pinned Answers & Saved Contexts
│
├── /retrieval ............................ Hybrid Search & Evidence Explorer
│   └── /retrieval/context-builder ........ Structured Context Package Assembler
│
├── /compare .............................. Cross-Document Comparison & Contradictions
│   ├── /compare/matrix ................... Pairwise Assertion Matrix
│   ├── /compare/conflicts ................ Cross-Document Contradiction Detector
│   └── /compare/diff ..................... Document Version Visual Clause Diff
│
├── /reviews .............................. Human Governance Review Queue
│   ├── /reviews/[reviewId] ............... Individual Review Workbench (Sovereign 4-Way Decision)
│   ├── /reviews/metrics .................. Governance & Quality Metrics Dashboard
│   └── /reviews/approved ................. Verified Facts & Approved Assertion Catalog
│
├── /advanced ............................. Advanced Mathematical Engines
│   ├── /advanced/topology ................ Topological Percolation Resilience Gauge
│   ├── /advanced/ising ................... Ising Annealing Objective Optimizer
│   └── /advanced/matrix-norm ............. Matrix & Quantity Normalization Sandbox
│
├── /analytics ............................ System Observability & Cost Telemetry
│   ├── /analytics/tokens ................. Token Economy & RAG Cost Savings
│   └── /analytics/latency ................ API Latency & Pipeline SLA Telemetry
│
├── /developer ............................ Integration Hub & Developer Tools
│   ├── /developer/api-explorer ........... Interactive Swagger/OpenAPI Console
│   ├── /developer/webhooks ............... Webhook Subscriptions & Dispatch Logs
│   └── /developer/sdks ................... SDK Code Samples & Export Formats
│
└── /admin ................................ Administration & Security Settings
    ├── /admin/tenants .................... Multi-Tenant Isolation & Quotas
    ├── /admin/users ...................... User Directory & RBAC Roles
    ├── /admin/keys ....................... Scoped API Key Management
    └── /admin/audit ...................... System-Wide Audit Log Stream
```

---

## 3. Deep-Linking & URL Query Parameter Contracts

All primary workspaces support stateful deep-linking via standard URL query parameters. This ensures workflows can be bookmarked, shared between team members, or linked directly from notifications:

### 3.1 Document Workspace (`/documents`)
* `GET /documents?status={pending|indexing|ready|failed}&search={query}&page={n}&limit={size}&sort={field:asc|desc}`
* `GET /documents/{documentId}?tab={overview|chunks|elements|facts|viewer}&page_num={n}&chunk_id={id}`

### 3.2 "Ask AEGIS" Workspace (`/ask`)
* `GET /ask?doc_id={id}&collection={tag}&q={query_string}&citation={evidence_id}&mode={stream|sync}`
  * When `citation` is present, the UI automatically opens the Contextual Evidence Inspector and scrolls the PDF canvas to the target bounding box.

### 3.3 Document Comparison Workspace (`/compare`)
* `GET /compare?doc_a={id}&doc_b={id}&show_conflicts_only={true|false}&subject={filter}`
* `GET /compare/diff?base_id={id}&target_id={id}&view={split|unified}`

### 3.4 Governance Review Queue (`/reviews`)
* `GET /reviews?status={pending|in_review|approved|corrected|rejected|needs_evidence}&candidate_type={fact|conflict}&assigned_to={actor_id}&sort={priority:desc}`
* `GET /reviews/{reviewId}?mode={decision|history|evidence}`

### 3.5 Processing Pipeline & Jobs (`/processing`)
* `GET /processing?status={queued|running|retry_wait|succeeded|failed|cancelled}&type={ingest|index|extract}&doc_id={id}`

---

## 4. UI Shell Navigation Components

### 4.1 Primary Sidebar Specification

```
┌──────────────────────────────────────┐
│ [A] AEGIS DocIntel          [ < ]    │
├──────────────────────────────────────┤
│ WORKSPACE                            │
│ 📊 Overview                          │
│                                      │
│ PIPELINES                            │
│ 📄 Documents                 (142)   │
│ ⚙️ Processing & Jobs           (2)🔴 │
│                                      │
│ INTELLIGENCE & GOVERNANCE            │
│ 💬 Ask AEGIS                         │
│ 🔍 Retrieval & Evidence              │
│ ⚖️ Compare & Conflicts        (5)⚠️ │
│ 🛡️ Review Queue              (18)⚡ │
│                                      │
│ ADVANCED & ANALYTICS                 │
│ 📐 Advanced Math & Topology          │
│ 📈 Analytics & Token Economy         │
│                                      │
│ SYSTEM                               │
│ 🔌 Developer & Webhooks              │
│ ⚙️ Administration                    │
├──────────────────────────────────────┤
│ 👤 Marcus Vance                      │
│    Role: Compliance Reviewer         │
│    [ Sign Out ]                      │
└──────────────────────────────────────┘
```

#### States & Micro-Interactions:
* **Expanded State (Default desktop >= 1280px)**: 260px wide, displays icons, labels, and real-time counter badges.
* **Collapsed State (Toggleable via `Ctrl+B` or `<` button)**: 68px wide, displays only icons with floating hover tooltips.
* **Real-Time Badge Counters**:
  * Review Queue: Displays count of unassigned `pending` items (e.g. `18`).
  * Processing Jobs: Displays red dot indicator if any job is currently in `failed` state.
  * Compare: Displays warning triangle if new cross-document conflicts are detected.
* **Keyboard Navigation**: Sidebar links support standard tab order and arrow-key traversal.

### 4.2 Top Header Context Bar

The top header is 56px high, pinned to `sticky top-0 z-40`:
1. **Tenant Switcher Dropdown**:
   * Shows active organization: e.g. `Acme BioPharma (tenant-01)`.
   * Clicking opens search-enabled dropdown listing all authorized tenants.
   * Selecting a different tenant triggers immediate state reset and cache refresh.
2. **Global Command Palette (`Ctrl+K` / `Cmd+K`)**:
   * Centered search bar: *"Search documents, reviews, jobs, or run a command... (Ctrl+K)"*.
3. **System Health Indicator**:
   * Small animated pulse dot + text badge:
     * Green (`Operational`): All endpoints healthy, latencies < 200ms.
     * Amber (`Degraded`): Worker queue backing up or circuit breaker open.
     * Red (`Critical`): Backend unreachable or primary database offline.
4. **Asynchronous Notification Center**:
   * Bell icon with unread count badge. Clicking opens a flyout slide-over listing background job completions, DLQ alerts, and assigned reviews.
5. **User Profile & RBAC Indicator**:
   * Avatar with user initials, full name, role pill (`Reviewer`, `Admin`), and dropdown containing Account Settings and Logout.

---

## 5. Global Command Palette (`Ctrl+K`) Specification

The Command Palette is the universal rapid-navigation accelerator for power users:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 🔍 Type a command or search...                                 [ESC]   │
├────────────────────────────────────────────────────────────────────────┤
│ RECENT DOCUMENTS                                                       │
│ 📄 Pfizer-Trial-Protocol-v4.pdf              Documents > Clinical      │
│ 📄 Credit-Agreement-Merger-2026.docx         Documents > Financial     │
│                                                                        │
│ PENDING REVIEWS                                                        │
│ 🛡️ REV-4089: Interest Rate Conflict (7.25% vs 8.00%)     Priority High │
│ 🛡️ REV-4091: Termination Clause Discrepancy             Priority Med  │
│                                                                        │
│ QUICK ACTIONS                                                          │
│ ⬆️ Upload New Document                                     (Cmd + U)   │
│ 💬 New "Ask AEGIS" Question                               (Cmd + J)   │
│ ⚖️ Compare Two Documents                                  (Cmd + D)   │
│ ⚙️ Open Pipeline Monitor                                  (Cmd + P)   │
│                                                                        │
│ NAVIGATION                                                             │
│ 📊 Go to Operational Overview                                          │
│ 📈 Go to Token Economy Analytics                                       │
│ 🔌 Go to Developer Webhook Settings                                    │
└────────────────────────────────────────────────────────────────────────┘
```

* **Keyboard Activation**: `Ctrl+K` (Windows/Linux) or `Cmd+K` (macOS).
* **Fuzzy Matching**: Matches document filenames, review candidate subjects, route titles, and command triggers.
* **Arrow Navigation**: `Up`/`Down` arrows to navigate; `Enter` to execute/navigate; `Esc` to close.

---

## 6. Responsive Breakpoints & Viewport Adaptations

AEGIS Workbench 2.0 is designed for responsive accessibility across three viewport tiers:

| Breakpoint Tier | Width Range | Sidebar Behavior | Header Behavior | Workspace Adaptation |
| :--- | :--- | :--- | :--- | :--- |
| **Desktop / Ultra-Wide** | `>= 1280px` | Persistent Expanded (260px) or Collapsed (68px). | Full header with tenant, search, health, notifications. | Full 3-pane layout (Sidebar + Focus + Contextual Inspector). |
| **Laptop / Compact Desktop** | `1024px - 1279px`| Auto-collapsed to 68px icon sidebar. | Search bar collapses to search icon button. | Contextual Inspector defaults to collapsible overlay drawer. |
| **Tablet** | `768px - 1023px` | Hidden off-canvas; opens as slide-over drawer via hamburger icon. | Minimal header: Hamburger + Logo + Health Dot + Notifications. | Single column focus workspace; Inspector opens as bottom sheet. |
| **Mobile** | `< 768px` | Hidden off-canvas slide-over. | Minimal header + sticky bottom navigation bar with 4 primary icons. | Stacked views; complex data grids switch to mobile card view. |

---

## 7. Navigation State Guards & Unsaved Changes Protection

1. **Unsaved Review Decision Guard**:
   * If a reviewer enters a custom correction value or rationale in `/reviews/[reviewId]` and attempts to navigate away, the router intercepts the transition with an accessible dialog:
     *"You have unsaved review decision changes. Discard changes or stay on page?"*
2. **Active Upload Interceptor**:
   * If an active chunked file upload is in transit, navigating away triggers a browser warning to prevent corrupted or aborted document ingestion.
3. **Role-Based Redirection Guard**:
   * Attempting to navigate directly to an unauthorized route (e.g. an `analyst` attempting to load `/admin/keys`) automatically redirects to `/` with an accessible toast notification:
     *"Access Restricted: Your active role (Analyst) does not have permission to access Administration."*
