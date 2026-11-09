# WP-UI-03 — Application Shell & Workspace Identity

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03`  
**Classification**: Engineering & UX Architecture Specification  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: ACTIVE IMPLEMENTATION  
**Version**: `2.0.0`  

---

## 1. Executive Summary & Purpose

Work Package `WP-UI-03` establishes the persistent application frame surrounding every AEGIS workspace screen. It bridges the foundational user journeys, route architecture, and role permissions established in `WP-UI-01` with the semantic design tokens, responsive standards, and reusable component primitives delivered in `WP-UI-02`.

The application shell provides the user's primary operating context:
1. **Sidebar Navigation**: Workflow-grouped access to Overview, Documents, Intelligence, Governance, and System areas.
2. **Application Header**: Compact operational header featuring workspace identity selector, global search, notification center, and user account menu.
3. **Breadcrumbs**: Hierarchical, route-derived location tracking across active and nested dynamic routes.
4. **Responsive Shell**: Seamless transition from persistent desktop sidebar ($\ge 1024\text{px}$) to collapsible mobile drawer ($< 1024\text{px}$) with zero horizontal root overflow.
5. **Security & Tenant Isolation**: Server-authoritative workspace context preventing unauthorized resource disclosure.

---

## 2. Document Inventory

The WP-UI-03 architecture is documented across 12 governing specifications:

| Document | Title | Scope & Purpose |
| :--- | :--- | :--- |
| [`01-shell-architecture.md`](./01-shell-architecture.md) | Shell Architecture & State Ownership | Component tree, layout composition, and state persistence rules. |
| [`02-sidebar-navigation.md`](./02-sidebar-navigation.md) | Sidebar Navigation & Routing | Workflow grouping, permission filtering, and active route highlighting. |
| [`03-header-workspace-selector.md`](./03-header-workspace-selector.md) | Header & Workspace Selector | Workspace identity, switching lifecycle, and cache invalidation. |
| [`04-breadcrumbs.md`](./04-breadcrumbs.md) | Breadcrumbs Hierarchy | Route-derived breadcrumb mapping and dynamic resource naming. |
| [`05-notification-center.md`](./05-notification-center.md) | Notification Center | Notification categories, lifecycle, unread counts, and API boundary. |
| [`06-global-search.md`](./06-global-search.md) | Global Search Interface | Search scope, debounce, cancellation, and internal route security. |
| [`07-responsive-layout.md`](./07-responsive-layout.md) | Responsive Shell Standards | Mobile drawer, tablet adaptations, and desktop layout contracts. |
| [`08-functional-requirements.md`](./08-functional-requirements.md) | Requirements & Traceability | Traceable functional (UI03-FR-001–024) and non-functional requirements. |
| [`09-api-integration.md`](./09-api-integration.md) | Backend API Contract Verification | OpenAPI capability mapping, verified endpoints, and blocked feature registers. |
| [`10-accessibility.md`](./10-accessibility.md) | Accessibility Standards (WCAG 2.2 AA) | Focus traps, skip link, landmarks, and keyboard shortcuts. |
| [`11-acceptance-criteria.md`](./11-acceptance-criteria.md) | Acceptance Criteria & Release Gates | Definition of Done, Release Gates AS-01 through AS-17. |
| [`12-test-plan.md`](./12-test-plan.md) | Automated Verification Plan | Unit, component contract, and Playwright browser E2E test suites. |

---

## 3. Repository Architecture

```
web/
├── src/
│   ├── components/
│   │   ├── shell/
│   │   │   ├── app-shell.tsx            # Persistent workbench layout container
│   │   │   ├── app-sidebar.tsx          # Workflow-grouped desktop sidebar navigation
│   │   │   ├── app-header.tsx           # Global header with selector, search & notifications
│   │   │   ├── mobile-navigation.tsx    # Slide-out modal drawer with focus containment
│   │   │   ├── workspace-selector.tsx   # Workspace switcher listbox
│   │   │   ├── breadcrumbs.tsx          # Route-derived hierarchical breadcrumbs
│   │   │   ├── notification-center.tsx  # Unread badge, notification list & read actions
│   │   │   ├── global-search.tsx        # Debounced search bar with category results
│   │   │   ├── user-menu.tsx            # Account options & sign out
│   │   │   ├── shell-skeleton.tsx       # Loading shell placeholder
│   │   │   └── navigation-access.ts     # Pure permission filter for shell items
│   │   └── app-shell.tsx                # Re-export preserving backward compatibility
│   ├── config/
│   │   ├── shell.ts                     # Shell navigation definitions & icons
│   │   └── navigation.ts                # Canonical route & group definitions
│   ├── features/
│   │   ├── workspaces/                  # Workspace schemas, types & API services
│   │   ├── notifications/               # Notification schemas, types & API services
│   │   └── search/                      # Search schemas, types & API services
│   ├── hooks/
│   │   ├── use-debounce.ts              # Query debounce hook
│   │   └── use-mobile-navigation.ts     # Mobile drawer state hook
│   └── lib/
│       └── shell/
│           ├── breadcrumbs.ts           # Route to breadcrumbs mapper
│           └── route-utils.ts           # Route active checks and safe URL validator
└── tests/
    ├── unit/
    │   ├── breadcrumbs.test.ts          # Breadcrumb mapping verification
    │   ├── navigation.test.ts           # Navigation permission filtering
    │   └── shell-state.test.ts          # Workspace selector and notification state
    └── e2e/
        ├── shell-navigation.spec.ts     # Desktop navigation & breadcrumb verification
        ├── workspace-selector.spec.ts   # Workspace listbox & keyboard escape
        ├── notifications.spec.ts        # Notification panel & unread badges
        ├── global-search.spec.ts        # Search input typing & clear behavior
        └── responsive-shell.spec.ts     # Mobile drawer & zero-overflow across viewports
```
