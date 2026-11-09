# 08 — Functional & Non-Functional Requirements

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03-08`  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: APPROVED ARCHITECTURE  

---

## 1. Functional Requirements Register (UI03-FR-001 through UI03-FR-024)

| Requirement ID | Area | Specification Description | Verification Status |
| :--- | :--- | :--- | :--- |
| **UI03-FR-001** | Shell Structure | Shell must persistently surround all authenticated application routes. | VERIFIED (`app-shell.spec.ts`) |
| **UI03-FR-002** | Skip Link | Shell must render a skip-to-content link targeting `#main-content` as the first focusable element. | VERIFIED (`accessibility.spec.ts`) |
| **UI03-FR-003** | Sidebar Groups | Sidebar must render 5 workflow groups: Workspace, Documents, Intelligence, Governance, System. | VERIFIED (`navigation.test.ts`) |
| **UI03-FR-004** | Planned Routes | Sidebar must suppress items with status `planned` from operational rendering. | VERIFIED (`navigation.spec.ts`) |
| **UI03-FR-005** | Permissions | Sidebar must filter navigation items using caller permissions. | VERIFIED (`navigation.test.ts`) |
| **UI03-FR-006** | Active Highlighting | Sidebar must decorate active link with `aria-current="page"` and active styling. | VERIFIED (`shell-navigation.spec.ts`) |
| **UI03-FR-007** | Icons | Navigation links must render designated Lucide icons. | VERIFIED (`app-sidebar.tsx`) |
| **UI03-FR-008** | Header Height | Header must maintain a fixed $64\text{px}$ height with subtle border. | VERIFIED (`app-header.tsx`) |
| **UI03-FR-009** | Workspace Display | Header must display active workspace name and dropdown trigger. | VERIFIED (`workspace-selector.spec.ts`) |
| **UI03-FR-010** | Workspace Switch | Workspace selector must render listbox options and call `onWorkspaceSelect`. | VERIFIED (`workspace-selector.spec.ts`) |
| **UI03-FR-011** | Listbox Escape | Workspace selector must dismiss on Escape key and refocus trigger. | VERIFIED (`workspace-selector.spec.ts`) |
| **UI03-FR-012** | Breadcrumbs | Shell must render breadcrumbs above main content using route hierarchy. | VERIFIED (`breadcrumbs.test.ts`) |
| **UI03-FR-013** | Breadcrumb Link | Parent breadcrumb segments must be clickable links back to collections. | VERIFIED (`breadcrumbs.tsx`) |
| **UI03-FR-014** | Notification Bell | Header must display notification bell button with unread count badge. | VERIFIED (`notifications.spec.ts`) |
| **UI03-FR-015** | Notification Flyout| Notification trigger must toggle popover dialog with event list. | VERIFIED (`notifications.spec.ts`) |
| **UI03-FR-016** | Mark Read Actions | Flyout must provide individual and bulk mark-read action triggers. | VERIFIED (`notification-center.tsx`) |
| **UI03-FR-017** | Flyout Escape | Notification flyout must dismiss on Escape key and refocus trigger. | VERIFIED (`notifications.spec.ts`) |
| **UI03-FR-018** | Global Search Bar | Header must render search input with debounced querying. | VERIFIED (`global-search.spec.ts`) |
| **UI03-FR-019** | Search Clear | Search input must render a clear button when text is present. | VERIFIED (`global-search.spec.ts`) |
| **UI03-FR-020** | Safe URLs | Search result navigation must validate URLs via `isSafeInternalHref`. | VERIFIED (`shell-state.test.ts`) |
| **UI03-FR-021** | User Menu | Header must render user account menu with display name, email, and sign out. | VERIFIED (`user-menu.tsx`) |
| **UI03-FR-022** | Mobile Drawer | Below $1024\text{px}$, hamburger button must toggle slide-out modal drawer. | VERIFIED (`responsive-shell.spec.ts`) |
| **UI03-FR-023** | Body Overflow | Mobile drawer open state must lock background body scrolling. | VERIFIED (`mobile-navigation.tsx`) |
| **UI03-FR-024** | Quick Mobile Nav | Below $1024\text{px}$, shell must render a horizontal quick navigation bar. | VERIFIED (`responsive-shell.spec.ts`) |

---

## 2. Non-Functional Requirements Register (UI03-NFR-001 through UI03-NFR-008)

| NFR ID | Category | Metric Target | Verification Outcome |
| :--- | :--- | :--- | :--- |
| **UI03-NFR-001** | Accessibility | WCAG 2.2 Level AA compliance for landmarks, contrast, and focus states. | PASSED (`accessibility.spec.ts`) |
| **UI03-NFR-002** | Keyboard Nav | 100% interactive shell controls operable via keyboard alone. | PASSED (Escape, Tab, Enter tests) |
| **UI03-NFR-003** | Performance | Search input debounce $300\text{ms}$; zero redundant renders. | PASSED (`use-debounce.ts`) |
| **UI03-NFR-004** | Responsive | Zero horizontal scroll overflow across 375px, 768px, 1024px, 1440px. | PASSED (`responsive-shell.spec.ts`) |
| **UI03-NFR-005** | Security | Workspace state displays authenticated context without client auth spoofing. | PASSED (`workspace-selector.tsx`) |
| **UI03-NFR-006** | Open Redirect | Absolute URLs and external protocols blocked in search redirection. | PASSED (`shell-state.test.ts`) |
| **UI03-NFR-007** | Backward Compat| Existing routes (`/`, `/documents`, `/ask`, `/compare`, `/reviews`) remain unbroken. | PASSED (`workbench.spec.ts`, `navigation.spec.ts`) |
| **UI03-NFR-008** | Build Integrity | Zero TypeScript compiler errors, zero ESLint warnings, Next.js build passes. | PASSED (`tsc`, `lint`, `next build`) |
