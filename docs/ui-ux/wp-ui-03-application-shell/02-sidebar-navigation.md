# 02 — Sidebar Navigation & Routing

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03-02`  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: APPROVED ARCHITECTURE  

---

## 1. Overview & Navigation Model

The AEGIS desktop sidebar delivers direct, workflow-oriented navigation tailored for analysts, reviewers, and compliance officers. It organizes operational capabilities into five logical groups:

```
+----------------------------------------+
| [Shield] AEGIS DocIntel                |
+----------------------------------------+
| WORKSPACE                              |
|   [LayoutDashboard] Overview           |
+----------------------------------------+
| DOCUMENTS                              |
|   [Files]           Document Library   |
|   [Workflow]        Processing (Pln)   |
+----------------------------------------+
| INTELLIGENCE                           |
|   [MessageSquare]   Ask AEGIS          |
|   [GitCompare]      Compare Documents  |
|   [FileSearch]      Evidence (Pln)     |
+----------------------------------------+
| GOVERNANCE                             |
|   [ClipboardCheck]  Review Queue       |
|   [BarChart3]       Analytics (Pln)    |
+----------------------------------------+
| SYSTEM                                 |
|   [Plug]            Integrations (Pln) |
|   [Settings]        Settings (Pln)     |
+----------------------------------------+
```

---

## 2. Navigation Registry & Permissions Matrix

Each navigation item is defined in `web/src/config/shell.ts` and evaluated using pure filter `getVisibleNavigation()`:

| Group | Item ID | Label | Route | Icon | Required Permissions | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Workspace** | `overview` | Overview | `/` | `layout-dashboard` | `workspace.read` | `active` |
| **Documents** | `documents-list` | Document Library | `/documents` | `files` | `documents.read` | `active` |
| **Documents** | `processing` | Processing | `/processing` | `workflow` | `processing.read` | `planned` |
| **Intelligence**| `ask` | Ask AEGIS | `/ask` | `message-square` | `intelligence.query` | `active` |
| **Intelligence**| `compare` | Compare Documents | `/compare` | `git-compare` | `documents.compare` | `active` |
| **Intelligence**| `evidence` | Evidence Explorer | `/evidence` | `file-search` | `evidence.read` | `planned` |
| **Governance** | `reviews` | Review Queue | `/reviews` | `clipboard-check` | `governance.read` | `active` |
| **Governance** | `analytics` | Analytics | `/analytics` | `chart-no-axes-combined` | `workspace.read` | `planned` |
| **System** | `integrations` | Integrations | `/settings/integrations` | `plug` | `integrations.manage` | `planned` |
| **System** | `settings` | Settings | `/settings` | `settings` | `workspace.settings.manage` | `planned` |

---

## 3. Pure Permission Filtering Logic

The function `getVisibleNavigation(permissions: readonly string[])` in `web/src/components/shell/navigation-access.ts` enforces the following contracts:
1. **Planned Route Suppression**: Items with `status: "planned"` are automatically excluded from the rendered navigation list.
2. **Permission Conjunction**: An active item is visible if and only if **all** of its `requiredPermissions` are present in the caller's granted set.
3. **Empty Group Pruning**: Any group whose visible items array is empty is completely omitted from the rendered DOM.
4. **Immutability**: Input permission collections are treated as read-only.

---

## 4. Active Route Highlighting & Accessibility

- **Link Highlighting**: Evaluated using pathname prefix matching (`pathname === href || pathname.startsWith(href + '/')`), with `/` strictly requiring exact match.
- **ARIA Standards**:
  - Main container: `<aside>` containing `<nav aria-label="Primary navigation">`.
  - Group headings: `<section aria-label="...">` with semantic `<h2 className="uppercase">`.
  - Active links: decorated with `aria-current="page"`.
  - Interactive item focus: high-contrast focus rings (`outline: 3px solid var(--primary)`).
