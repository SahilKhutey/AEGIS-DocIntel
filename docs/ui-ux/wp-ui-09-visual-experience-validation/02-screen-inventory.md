# WP-UI-09 — 02: Screen & Visual State Inventory

**Work Package**: WP-UI-09 — Visual, Interaction & End-to-End Experience Validation  
**Document**: 02 — Screen Inventory & Visual State Matrix  
**Status**: Approved & Baseline Verified  

---

## 1. Application Screen Inventory

The AEGIS-DocIntel web application comprises 11 functional views spanning all operational domains:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      AEGIS Application Topology                        │
├────────────────────────────────┬───────────────────────────────────────┤
│ Core Workspace                 │ Intelligence Workspace                │
│ • / (Overview & Quick Actions) │ • /ask (Grounded Question Answering)  │
│ • /documents (Document Library)│ • /compare (Document Comparison Diff) │
│ • /documents/[id] (Inspector)  │                                       │
├────────────────────────────────┼───────────────────────────────────────┤
│ Governance Workspace           │ Advanced & Operational Workspace      │
│ • /reviews (Human Review Queue)│ • /analytics (Metrics & Dashboards)   │
│                                │ • /mathematics (KaTeX & Vectors)      │
│                                │ • /pipelines (Execution DAGs)         │
│                                │ • /monitoring (Telemetry & Alerts)    │
│                                │ • /developer (API Keys & Webhooks)    │
└────────────────────────────────┴───────────────────────────────────────┘
```

---

## 2. Fifteen Standard Visual States

To ensure exhaustive UX resilience, every screen is evaluated against 15 distinct visual and operational states:

| State Code | State Designation | Visual & Behavioral Characteristic |
| :--- | :--- | :--- |
| **ST-01** | **Unauthenticated / Session Expired** | Immediate redirect to login with return URL preserved in state. |
| **ST-02** | **Initial Page Loading (Skeleton)** | Semantic `role="status"` skeleton loader matching target layout; no jarring layout shift (CLS < 0.05). |
| **ST-03** | **Empty State (Zero Records)** | Clean vector illustration or icon, helpful explanatory prompt, and primary CTA button. |
| **ST-04** | **Initial Input / Ready State** | Controls enabled, placeholder hints displayed, default focus positioned appropriately. |
| **ST-05** | **Populated Data State** | Clean tabular or card display, typography hierarchy preserved, data formatted cleanly. |
| **ST-06** | **Active Selection / Row Highlight** | Clear high-contrast selection borders (`outline-2 outline-primary`), badge counters updated. |
| **ST-07** | **Drawer / Modal Open State** | Semi-transparent backdrop (`backdrop-blur-sm`), focus locked inside modal, Esc dismissible. |
| **ST-08** | **Filtered / Sorted View** | Filter tags visible with dismiss buttons, sort direction arrows (`asc`/`desc`), record counters. |
| **ST-09** | **In-Progress Mutation (Busy)** | Disabled trigger button, indeterminate loading spinner, `aria-busy="true"`. |
| **ST-10** | **Optimistic Update State** | Immediate local state reflection with subtle pending indicator pending backend confirmation. |
| **ST-11** | **Success State Notification** | Green success banner (`role="status"`), toast or inline alert with auto-dismiss or close button. |
| **ST-12** | **Form Validation Error** | Red inline message under affected field, high-contrast border, focus pulled to first error. |
| **ST-13** | **Server Error (5xx / Timeout)** | User-friendly message explaining network issue, retry CTA button, technical details expandable. |
| **ST-14** | **Reconnecting / Offline Banner** | Persistent amber banner at top of shell indicating WebSocket reconnect attempt. |
| **ST-15** | **Read-Only / Forbidden (403)** | Action buttons hidden or disabled with tooltip explaining required role/permission. |

---

## 3. Screen-by-Screen State Coverage Matrix

The matrix below documents verified state behavior across all primary application routes:

| Route Path | ST-02 (Skeleton) | ST-03 (Empty) | ST-05 (Data) | ST-07 (Modal/Drawer) | ST-12/13 (Errors) | ST-15 (RBAC Gated) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `/` | Verified | Verified | Verified | N/A | Verified | Verified |
| `/documents` | Verified | Verified | Verified | Upload Modal | Verified | Ingestion Gated |
| `/documents/[id]` | Verified | Verified | Verified | Metadata Drawer | Verified | Edit Gated |
| `/ask` | Verified | Verified | Verified | Citation Drawer | Verified | Query Logged |
| `/compare` | Verified | Verified | Verified | Diff Selector | Verified | Compare Permitted |
| `/reviews` | Verified | Verified | Verified | Decision Modal | Verified | Reviewer Role Only |
| `/analytics` | Verified | Verified | Verified | Export Dialog | Verified | Admin / Analyst |
| `/mathematics` | Verified | Verified | Verified | Matrix Inspector | Verified | Verified |
| `/pipelines` | Verified | Verified | Verified | Stage Log Drawer| Verified | Admin Role Only |
| `/monitoring` | Verified | Verified | Verified | Alert Config | Verified | Admin Role Only |
| `/developer` | Verified | Verified | Verified | Key Creation | Verified | Admin / Dev Only |

---

## 4. Layout & Viewport Specifications

All screens adhere to standard responsive breakpoints governed by the Tailwind CSS configuration:

- **Desktop Widescreen (1920x1080)**: Full 4-column layout, open 256px sidebar, multi-panel split view.
- **Laptop / Standard Desktop (1366x768 / 1280x800)**: 3-column layout, standard sidebar, flexible content pane.
- **Tablet Landscape (1024x768)**: Collapsible sidebar, 2-column or stacked content panels.
- **Tablet Portrait (768x1024)**: Off-canvas hamburger navigation drawer, single column content flow.
- **Mobile Smartphone (390x844 / 320x568)**: Fully stacked card views, sticky bottom actions, touch targets >= 44x44px.
