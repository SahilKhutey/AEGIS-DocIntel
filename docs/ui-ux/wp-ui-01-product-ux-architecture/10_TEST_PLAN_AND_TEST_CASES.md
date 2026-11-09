# AEGIS-DocIntel — Test Plan & Test Cases

## 1. Test Strategy & Scope

Testing for WP-UI-01 validates architectural invariants, route integrity, navigation logic, and accessibility landmarks across unit and browser test layers.

## 2. Test Case Register

| Test ID | Test Scenario | Verification Layer | Priority | Expected Outcome |
| :--- | :--- | :--- | :---: | :--- |
| **UI01-T001** | Navigation groups exist | Unit (`navigation.test.ts`) | P0 | All 5 navigation groups defined (`workspace`, `documents`, `intelligence`, `governance`, `system`). |
| **UI01-T002** | Duplicate navigation IDs | Unit (`navigation.test.ts`) | P0 | All navigation group IDs are unique. |
| **UI01-T003** | Duplicate routes | Unit (`navigation.test.ts`) | P0 | All navigation item `href` paths are unique. |
| **UI01-T004** | Nested route selection | Unit (`navigation.test.ts`) | P0 | Navigating to `/documents/doc-123` retains `/documents` active state. |
| **UI01-T005** | Planned navigation exclusion | Unit / E2E | P0 | Items with `status: "planned"` (`/processing`, `/analytics`, `/evidence`) are not marked active or rendered as working links. |
| **UI01-T006** | Unknown route resolution | Unit (`navigation.test.ts`) | P1 | `getActiveNavigationItem("/unknown")` returns `undefined`. |
| **UI01-T007** | Mobile navigation visibility | E2E (`navigation.spec.ts`) | P1 | On viewport 390x844, `<nav aria-label="Mobile navigation">` is visible. |
| **UI01-T008** | Accessible navigation landmarks | E2E (`navigation.spec.ts`) | P0 | `<nav aria-label="Primary navigation">` is attached in the DOM. |
| **UI01-T009** | Main content landmark | E2E (`navigation.spec.ts`) | P1 | `<main id="main-content">` is visible. |
| **UI01-T010** | Tenant identity removal | Static / E2E | P0 | Zero hardcoded `default-tenant` labels rendered in the shell. |
| **UI01-T011** | Route authorization | API Integration | P0 | Backend rejects unauthorized requests with 401/403. |
| **UI01-T012** | Production build sanity | Build (`npm run build`) | P0 | Next.js build compiles without type or lint errors. |

## 3. Test Execution Commands

```powershell
# Run Vitest Unit Tests
cd web
npx vitest run

# Run ESLint Static Analysis
npx eslint .

# Run TypeScript Typecheck
npx tsc --noEmit

# Run Playwright Browser Tests
npx playwright test

# Run Next.js Production Build
npm run build
```
