# 01 — Shell Architecture & State Ownership

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03-01`  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: APPROVED ARCHITECTURE  

---

## 1. Architectural Role & Boundary

The AEGIS Application Shell is the persistent, sovereign frame enclosing every interactive screen within the workbench. It guarantees workspace contextual continuity, secure identity presentation, and uniform navigation access across document intelligence workflows.

```
+-----------------------------------------------------------------------------------------------+
| AppShell (Root Layout)                                                                        |
| +-------------------------------------------------------------------------------------------+ |
| | Skip to main content (Skip Link)                                                          | |
| +-------------------------------------------------------------------------------------------+ |
| | Suspense Boundary (Fallback: ShellSkeleton)                                               | |
| | +---------------------+-----------------------------------------------------------------+ | |
| | | AppSidebar          | AppHeader                                                       | | |
| | | (Desktop >=1024px)  | +------------------+------------------+-----------+-----------+ | | |
| | |                     | | WorkspaceSelector| GlobalSearch     | NotifCtr  | UserMenu  | | | |
| | | - Logo / Branding   | +------------------+------------------+-----------+-----------+ | | |
| | | - Workspace Group   | Quick Mobile Navigation Bar (<1024px)                           | | |
| | | - Documents Group   +-----------------------------------------------------------------+ | |
| | | - Intelligence Grp  | Main Content Area (<main id="main-content">)                    | | |
| | | - Governance Group  | +-------------------------------------------------------------+ | | |
| | | - System Group      | | Breadcrumbs (<nav aria-label="Breadcrumb">)                 | | | |
| | |                     | +-------------------------------------------------------------+ | | |
| | |                     | | {children} (Page View: /documents, /ask, /compare, /reviews)| | | |
| | |                     | +-------------------------------------------------------------+ | | |
| | |                     | Footer                                                          | | |
| | +---------------------+-----------------------------------------------------------------+ | |
| +-------------------------------------------------------------------------------------------+ |
| | MobileNavigation (Modal Drawer, role="dialog", <1024px)                                     | |
| +-------------------------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------------------------+
```

---

## 2. Component Hierarchy & Composition

1. **`AppShell` (`web/src/components/shell/app-shell.tsx`)**:
   - Outermost container providing standard CSS theme variables (`var(--background)`, `var(--foreground)`).
   - Renders the `.skip-link` immediately into the root DOM before any dynamic suspension.
   - Houses the `<Suspense fallback={<ShellSkeleton />}>` boundary required for Next.js App Router dynamic routes (`usePathname()`).
   - Delegates operational layout to `AppShellInner`.

2. **`AppSidebar` (`web/src/components/shell/app-sidebar.tsx`)**:
   - Persistent desktop navigation sidebar (`<aside>` container with `<nav aria-label="Primary navigation">`).
   - Renders workflow groupings: Workspace, Documents, Intelligence, Governance, and System.
   - Enforces permission-based visibility using pure function `getVisibleNavigation()`.
   - Distinguishes active routes with `aria-current="page"` and high-contrast visual indicators.

3. **`AppHeader` (`web/src/components/shell/app-header.tsx`)**:
   - Fixed-height ($64\text{px}$) header with subtle border and elevation.
   - Hosts mobile menu hamburger toggle button, workspace identity dropdown, debounced global search, notification center, and user account menu.

4. **`Breadcrumbs` (`web/src/components/shell/breadcrumbs.tsx`)**:
   - Accessible navigation landmark (`<nav aria-label="Breadcrumb">`).
   - Maps pathname segments dynamically to human-readable names and clickable internal links.

5. **`MobileNavigation` (`web/src/components/shell/mobile-navigation.tsx`)**:
   - Slide-out accessible modal drawer (`role="dialog"`, `aria-modal="true"`, `aria-label="Mobile navigation"`).
   - Manages body overflow locking, keyboard Escape dismissal, and backdrop click dismissal.

---

## 3. State Ownership & Persistence

| State Item | Owner | Persistence Mechanism | Security Authority |
| :--- | :--- | :--- | :--- |
| **Active Workspace** | `AppShell` | Client state (`useState`), props callback `onWorkspaceSelect` | Server session (`X-Tenant-ID` / JWT claims). Client state is display-only. |
| **Mobile Drawer Open** | `AppShell` | Client boolean (`useState`) | Pure UI state. |
| **Search Query** | `GlobalSearch` | Local state with $300\text{ms}$ debounce | Pure UI state; API queries filtered by user permissions. |
| **Notifications Panel** | `NotificationCenter` | Local popover state (`useState`) | Server-backed review and job state. |
| **User Menu Open** | `UserMenu` | Local popover state (`useState`) | Pure UI state. |
| **Granted Permissions** | `AccessContext` / Shell Props | Client memoization | FastAPI backend RBAC contract. |

---

## 4. Architectural Rules

1. **Zero Fake Success**: Client components must never mock successful mutations or invent synthetic records when an endpoint is missing. Unsupported operations are marked with structured fallback states.
2. **Tenant Isolation**: Selecting a workspace in the UI does NOT alter server authorization boundaries. All document, intelligence, and review operations require server-side token validation.
3. **No Root Overflow**: The application shell guarantees zero horizontal layout shift and zero horizontal overflow across 375px, 768px, 1024px, and 1440px viewports.
4. **Single `<main>` Landmark**: The document hierarchy maintains exactly one `<main id="main-content">` landmark. Skeletons and subcomponents use `<div>` or explicit section landmarks.
