# AEGIS-DocIntel — Route & Page Register

## 1. Route Registry Architecture

The frontend route register is centralized in [`web/src/config/routes.ts`](file:///c:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/ui_ux_development_strategy/web/src/config/routes.ts). Every route declares its capability, implementation status, and authentication requirements.

## 2. Comprehensive Route Inventory

| Route Path | Page Title | Required Capability | Implementation Status | Auth Required | Backend Target |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `/` | Workspace Overview | `workspace.read` | **Active** (Redesign) | Yes | `/v1/stats`, `/v1/admin/stats` |
| `/documents` | Document Library | `documents.read` | **Active** | Yes | `/v1/documents`, `/v1/documents/upload` |
| `/documents/[documentId]` | Document Inspection | `documents.read` | **Active** | Yes | `/v1/documents/{id}`, `/v1/documents/{id}/chunks` |
| `/ask` | Ask AEGIS | `intelligence.query` | **Active** | Yes | `/v1/answers`, `/v1/query` |
| `/compare` | Document Comparison | `documents.compare` | **Active** | Yes | `/v1/intelligence/compare`, `/v1/intelligence/conflicts` |
| `/reviews` | Review Queue | `governance.read` | **Active** | Yes | `/v1/reviews`, `/v1/reviews/metrics` |
| `/reviews/[reviewId]` | Review Details & Decision | `governance.review` | **Active** | Yes | `/v1/reviews/{id}`, `/v1/reviews/{id}/decisions` |
| `/processing` | Processing Monitor | `processing.read` | **Planned** | Yes | `/v1/jobs`, `/v1/jobs/{id}/events` |
| `/evidence` | Evidence Explorer | `evidence.read` | **Planned** | Yes | `/v1/documents/{id}/elements`, `/v1/annotations/` |
| `/analytics` | System Analytics | `analytics.read` | **Planned** | Yes | `/v1/admin/token-usage`, `/metrics` |
| `/settings` | Workspace Settings | `settings.read` | **Planned** | Yes | `/v1/admin/tenants`, `/v1/webhooks/subscriptions` |

## 3. Route Ownership & Security Boundary

1. **Client-Side Intent Only**: The frontend route registry expresses user navigation intent. It is **not** an authorization firewall.
2. **Backend Enforcement**: Every protected API route must enforce authentication, tenant isolation (`X-Tenant-ID`), and role validation on the server side (`src/api/auth.py`).
3. **Fail-Closed Redirection**: Unauthorized API responses (HTTP 401/403) automatically trigger route redirection or accessible permission denial notices.
