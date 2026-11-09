# WP-UI-08: Permissions & Tenant Isolation

## 1. Backend RBAC Authority & Canonical Roles

The frontend maps strictly to the authoritative roles defined in the FastAPI security context (`src/api/auth.py` and `src/core/security_context.py`):

| Canonical Role | System Responsibilities | Mapped Permissions Count |
| :--- | :--- | :--- |
| `viewer` | Read-only inspection of documents, queries, and pipelines | 6 permissions |
| `editor` | Ingests documents, triggers pipeline reprocessing | 11 permissions |
| `reviewer` | Claims review items, submits fact & conflict decisions | 14 permissions |
| `review_admin` | Reopens closed reviews, inspects system audit history | 18 permissions |
| `tenant_admin` | Manages tenant users, credentials, and webhooks | 22 permissions |
| `platform_admin` | System health monitoring, cluster SLAs | 23 permissions |
| `admin` | Full sovereign administrative clearance | 23 permissions |

---

## 2. Route Access Rules (`web/src/lib/auth/route-guard.ts`)

Access to workspace routes is guarded by declarative rule definitions:

```typescript
export const ROUTE_ACCESS_RULES: Record<string, readonly string[]> = {
  "/": ["workspace.read"],
  "/documents": ["documents.read"],
  "/documents/upload": ["documents.upload"],
  "/ask": ["intelligence.query"],
  "/compare": ["documents.compare"],
  "/reviews": ["governance.read"],
  "/analytics": ["analytics.read"],
  "/mathematics": ["mathematics.read"],
  "/pipelines": ["processing.read"],
  "/monitoring": ["monitoring.read"],
  "/developer": ["developer.read"],
};
```

---

## 3. UI Protection Components

1. **`PermissionGate`** (`web/src/components/integration/PermissionGate.tsx`):
   Selectively renders child UI components only if the session contains the required permission, falling back to an optional placeholder or null.
2. **`AccessDenied`** (`web/src/components/integration/AccessDenied.tsx`):
   Renders an accessible (`role="alert"`) view explaining which exact permission was missing, preventing unauthorized interaction without breaking application flow.
3. **Workspace Isolation Boundary**:
   Switching workspaces updates `X-Workspace-ID` globally across the `RequestContext`. The `RealtimeManager` immediately drops and re-establishes streaming subscriptions for the new workspace boundary to prevent cross-workspace data bleed.
