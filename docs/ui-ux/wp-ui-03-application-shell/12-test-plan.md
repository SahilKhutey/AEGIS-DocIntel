# 12 — Automated Verification Plan & Test Strategy

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03-12`  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: APPROVED ARCHITECTURE  

---

## 1. Test Architecture & Coverage

The WP-UI-03 test suite employs a two-tier verification architecture:
1. **Unit & Fast Pure Logic Tests (Vitest)**: Fast execution testing state machines, permission evaluation, breadcrumb path mappers, and safe URL sanitizers.
2. **Browser End-to-End Tests (Playwright)**: Full browser verification testing rendering, layout, keyboard interactions, focus trapping, and responsiveness.

```
                           +----------------------------------------+
                           |           WP-UI-03 Test Suite          |
                           +-------------------+--------------------+
                                               |
                     +-------------------------+-------------------------+
                     |                                                   |
        +------------v-------------+                        +------------v-------------+
        |   Vitest Unit & Contract |                        | Playwright Browser E2E   |
        |   12 Suites / 80 Tests   |                        | 11 Suites / 36 Tests     |
        +--------------------------+                        +--------------------------+
        | - breadcrumbs.test.ts    |                        | - shell-navigation.spec  |
        | - navigation.test.ts     |                        | - workspace-selector.spec|
        | - shell-state.test.ts    |                        | - notifications.spec.ts  |
        | - permissions.test.ts    |                        | - global-search.spec.ts  |
        | - component-contracts    |                        | - responsive-shell.spec  |
        | - design-tokens.test.ts  |                        | - accessibility.spec.ts  |
        +--------------------------+                        +--------------------------+
```

---

## 2. Test Execution Commands

```bash
# Execute fast unit tests
npm --prefix web test

# Execute TypeScript compiler validation
npx --prefix web tsc -p web/tsconfig.json --noEmit

# Execute ESLint static analysis
npm --prefix web run lint

# Execute Next.js production build
npm --prefix web run build

# Execute Playwright E2E browser test suite
npm --prefix web run test:e2e
```

---

## 3. Test Suites Inventory & Purpose

### 3.1 Unit Test Suites
- `web/tests/unit/breadcrumbs.test.ts`: Validates root path, single level, nested resources, and unknown route breadcrumb generation.
- `web/tests/unit/navigation.test.ts`: Validates that planned items are filtered out and permission filtering works across all 5 groups.
- `web/tests/unit/shell-state.test.ts`: Validates drawer open/close, workspace lookup, notification count formatting, and open redirect URL prevention.

### 3.2 E2E Test Suites
- `web/tests/e2e/shell-navigation.spec.ts`: Tests sidebar navigation to documents, active link `aria-current="page"`, and breadcrumbs visibility.
- `web/tests/e2e/workspace-selector.spec.ts`: Tests workspace dropdown toggle, listbox options, and Escape key dismissal.
- `web/tests/e2e/notifications.spec.ts`: Tests notification bell button, badge, panel toggle, and Escape key dismissal.
- `web/tests/e2e/global-search.spec.ts`: Tests search input typing, debounced response, and clear button.
- `web/tests/e2e/responsive-shell.spec.ts`: Tests mobile drawer toggle, desktop sidebar visibility, and zero horizontal scroll overflow across viewports.
- `web/tests/e2e/accessibility.spec.ts`: Tests skip link keyboard accessibility, main landmark, and button accessible names.
- `web/tests/e2e/workbench.spec.ts`: Verifies non-regression of documents, ask, compare, and reviews pages.
