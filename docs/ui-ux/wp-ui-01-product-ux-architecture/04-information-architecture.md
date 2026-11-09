# Information Architecture & Product Domain Structure

| Field | Value |
|---|---|
| Project | AEGIS-DocIntel |
| Work Package | WP-UI-01 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | Product Engineering |
| Dependencies | Existing web application, AppShell, Navigation Configuration |
| Last Verified Commit | ee293f0 |
| Review Date | 2026-11-09 |

---

## 1. Purpose

Specifies the information architecture of AEGIS Workbench 2.0, organizing the application into five primary product domains while establishing the 3-region viewport layout and state management boundaries.

## 2. Product Domains & Hierarchy

```
AEGIS Workbench
│
├── [Domain 1: Workspace]
│   └── Overview (/) ..................... Operational Command Center & Telemetry
│
├── [Domain 2: Documents]
│   ├── Document Library (/documents) .... Ingest, search & manage source documents
│   └── Inspection (/documents/[id]) ..... Chunks, layout elements & metadata
│
├── [Domain 3: Intelligence]
│   ├── Ask AEGIS (/ask) ................. Tri-pane grounded QA & citation streaming
│   ├── Compare (/compare) ............... Pairwise assertion & contradiction matrix
│   └── Evidence (/evidence) ............. [Planned] Cross-document evidence search
│
├── [Domain 4: Governance]
│   ├── Review Queue (/reviews) .......... Human-in-the-loop candidate triage
│   └── Details (/reviews/[reviewId]) .... Sovereign decision workbench & audit trail
│
└── [Domain 5: System]
    ├── Processing (/processing) ......... [Planned] Background pipeline job monitor
    ├── Analytics (/analytics) ........... [Planned] Telemetry, token economy & metrics
    ├── Settings (/settings) ............. [Planned] Tenant, quota & preferences
    └── Integrations (/integrations) ..... [Planned] Webhooks & API developer hub
```

## 3. Viewport Layout Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│ HEADER: Brand · Tenant Context · Search (Ctrl+K) · Health · Profile    │
├──────────────┬──────────────────────────────────────────┬──────────────┤
│ PRIMARY NAV  │ CENTRAL WORKSPACE                        │ CONTEXTUAL   │
│              │                                          │ INSPECTOR    │
│ • Workspace  │ • Operational Dashboard Overview         │              │
│ • Documents  │ • Document Library & Ingestion Studio    │ • PDF Canvas │
│ • Ask AEGIS  │ • Tri-Pane Grounded QA Console           │ • Bounding   │
│ • Compare    │ • Document Comparison & Conflict Matrix  │   Boxes      │
│ • Reviews    │ • Governance Review Queue & Decision Hub │ • Audit Trail│
│              │                                          │ • Metadata   │
├──────────────┴──────────────────────────────────────────┴──────────────┤
│ FOOTER: System Status · Active Session · API Version                  │
└────────────────────────────────────────────────────────────────────────┘
```

## 4. State Architecture Tiers

1. **Server State (TanStack Query)**: Centralized caching, automatic background invalidation, and optimistic mutations for all REST API resources, tagged by active tenant ID (`['tenant', tenantId, resource]`).
2. **Session State (AccessContext / Auth)**: Authenticated user claims, verified active tenant, role boundaries, and theme preferences.
3. **Local Workspace State**: Ephemeral view states, modal open/close flags, active citation selections, and PDF zoom levels.
