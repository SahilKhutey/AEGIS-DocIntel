# Route Register & Page Responsibility Specification

| Field | Value |
|---|---|
| Project | AEGIS-DocIntel |
| Work Package | WP-UI-01 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | Product Engineering |
| Dependencies | `web/src/config/routes.ts`, `web/src/lib/route-matching.ts` |
| Last Verified Commit | ee293f0 |
| Review Date | 2026-11-09 |

---

## 1. Purpose

Maintains the authoritative registry of application routes, required permissions, implementation status, and page responsibilities across the AEGIS frontend.

## 2. Route Inventory

| Route ID | Path Pattern | Page Title | Required Permission | Initial Status | Auth Required |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `overview` | `/` | Workspace Overview | `workspace.read` | **Active** | Yes |
| `documents` | `/documents` | Document Library | `documents.read` | **Active** | Yes |
| `document-detail` | `/documents/[documentId]`| Document Inspection | `documents.read` | **Active** | Yes |
| `ask` | `/ask` | Ask AEGIS | `intelligence.query` | **Active** | Yes |
| `compare` | `/compare` | Document Comparison | `documents.compare` | **Active** | Yes |
| `reviews` | `/reviews` | Review Queue | `governance.read` | **Active** | Yes |
| `review-detail` | `/reviews/[reviewId]` | Review Details | `governance.review` | **Active** | Yes |
| `evidence` | `/evidence` | Evidence Explorer | `evidence.read` | **Planned** | Yes |
| `processing` | `/processing` | Processing Monitor | `processing.read` | **Planned** | Yes |
| `analytics` | `/analytics` | System Analytics | `workspace.read` | **Planned** | Yes |
| `settings` | `/settings` | Workspace Settings | `workspace.settings.manage` | **Planned** | Yes |
| `integrations` | `/integrations` | External Integrations| `integrations.manage` | **Planned** | Yes |

## 3. Dynamic Route Matching

The routing layer uses [`web/src/lib/route-matching.ts`](file:///c:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/ui_ux_development_strategy/web/src/lib/route-matching.ts) to match static paths and single-segment dynamic patterns (`[documentId]`, `[reviewId]`):

- Dynamic segment pattern: `^/documents/[^/]+/?$` accurately matches `/documents/doc-123`.
- Incomplete segment: `/documents/` evaluates to `false` and does not falsely match `document-detail`.
- Unrelated prefix: `/documents-old` evaluates to `false`.
- Longest-prefix match ordering guarantees specific routes take precedence over root routes.
