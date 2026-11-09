# Test Plan & Quality Assurance Strategy

| Field | Value |
|---|---|
| Project | AEGIS-DocIntel |
| Work Package | WP-UI-01 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | QA Engineering |
| Dependencies | Vitest, Playwright, Next.js, TypeScript |
| Last Verified Commit | ee293f0 |
| Review Date | 2026-11-09 |

---

## 1. Test Strategy Overview

Quality assurance for WP-UI-01 validates architectural invariants, role permissions, route matching, user journeys, accessibility, and build integrity across unit, integration, and end-to-end browser layers.

## 2. Test Suites Inventory

```
web/tests/
├── unit/
│   ├── permissions.test.ts ............. Validates role defaults, hasPermission, and permission checks (7 tests)
│   ├── navigation.test.ts .............. Validates group IDs, paths, active state, and planned hiding (10 tests)
│   ├── routes.test.ts .................. Validates route matching, regex patterns, and planned status (7 tests)
│   └── workflows.test.ts ............... Validates workflow IDs, step IDs, failure states, and routes (6 tests)
└── e2e/
    ├── navigation.spec.ts .............. Validates shell rendering, navigation clicks, landmarks, mobile (7 tests)
    └── user-journeys.spec.ts ........... Validates user entry points (workspace, analyst, reviewer, planned) (5 tests)
```

## 3. Test Cases & Execution Commands

### Unit Tests (Vitest)
```powershell
cd web
npx vitest run
# Expected: 6 test suites passed, 35 tests passed
```

### Static Analysis & Typechecking
```powershell
cd web
npx eslint .
npx tsc --noEmit
# Expected: 0 warnings, 0 errors
```

### Browser E2E Tests (Playwright)
```powershell
cd web
# Start production server and run Playwright
$server = Start-Process node -ArgumentList "./node_modules/next/dist/bin/next", "start" -PassThru
Start-Sleep -Seconds 5
npx playwright test tests/e2e/navigation.spec.ts tests/e2e/user-journeys.spec.ts
Stop-Process -Id $server.Id -Force
# Expected: 12 passing browser tests across 2 workers
```

### Production Build Verification
```powershell
cd web
npm run build
# Expected: Clean production build with all 10 static and partial prerenders generated
```

## 4. Evidence Traceability

All execution outputs are archived in:
- `docs/ui-ux/wp-ui-01-product-ux-architecture/evidence/execution/unit-test-results.txt`
- `docs/ui-ux/wp-ui-01-product-ux-architecture/evidence/execution/e2e-test-results.txt`
- `docs/ui-ux/wp-ui-01-product-ux-architecture/evidence/execution/lint-results.txt`
- `docs/ui-ux/wp-ui-01-product-ux-architecture/evidence/execution/typecheck-results.txt`
- `docs/ui-ux/wp-ui-01-product-ux-architecture/evidence/execution/build-results.txt`
