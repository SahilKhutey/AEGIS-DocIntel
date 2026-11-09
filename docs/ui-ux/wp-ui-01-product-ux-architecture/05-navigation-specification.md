# Navigation Specification & Access Control

| Field | Value |
|---|---|
| Project | AEGIS-DocIntel |
| Work Package | WP-UI-01 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | Product Engineering |
| Dependencies | `web/src/config/navigation.ts`, `web/src/features/access/navigation-access.ts` |
| Last Verified Commit | ee293f0 |
| Review Date | 2026-11-09 |

---

## 1. Purpose

Governs product navigation, item visibility, permission filtering, and active-state determination across desktop and mobile application shells.

## 2. Navigation Contract

Navigation is declared in [`web/src/config/navigation.ts`](file:///c:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/ui_ux_development_strategy/web/src/config/navigation.ts):

```typescript
export type NavigationItem = {
  id: string;
  label: string;
  href: string;
  description: string;
  requiredPermissions: Permission[];
  status: "active" | "planned";
  match: "exact" | "prefix";
};
```

## 3. Registered Navigation Items & Permissions

| ID | Label | Destination | Required Permissions | Initial Status | Match Mode |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `overview` | Overview | `/` | `["workspace.read"]` | **Active** | exact |
| `document-library` | Document Library | `/documents` | `["documents.read"]` | **Active** | prefix |
| `ask` | Ask AEGIS | `/ask` | `["intelligence.query"]` | **Active** | prefix |
| `compare` | Compare Documents | `/compare` | `["documents.compare"]` | **Active** | prefix |
| `evidence` | Evidence Explorer | `/evidence` | `["evidence.read"]` | **Planned** | prefix |
| `reviews` | Review Queue | `/reviews` | `["governance.read"]` | **Active** | prefix |
| `processing` | Processing Jobs | `/processing` | `["processing.read"]` | **Planned** | prefix |
| `analytics` | Analytics | `/analytics` | `["workspace.read"]` | **Planned** | prefix |
| `settings` | Settings | `/settings` | `["workspace.settings.manage"]` | **Planned** | prefix |
| `integrations` | Integrations | `/integrations` | `["integrations.manage"]` | **Planned** | prefix |

## 4. Visibility & Active State Rules

1. **Feature Gating**: Navigation items marked with `status: "planned"` are strictly omitted from rendered active links via `getVisibleNavigation`.
2. **Permission Gating**: An item is rendered only if the caller's active permissions contain all `requiredPermissions`.
3. **Route Matching Logic**:
   - `exact`: `pathname === item.href`
   - `prefix`: `pathname === item.href || pathname.startsWith(item.href + "/")`
4. **False Positive Prevention**: Prefix matching requires a trailing `/`, preventing unrelated paths like `/documents-old` from activating `/documents`.
