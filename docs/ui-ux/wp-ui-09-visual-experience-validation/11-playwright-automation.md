# WP-UI-09 — 11: Playwright Test Automation Architecture

**Work Package**: WP-UI-09 — Visual, Interaction & End-to-End Experience Validation  
**Document**: 11 — Test Automation Architecture, Fixtures & Configuration  
**Status**: Approved & Baseline Verified  

---

## 1. Test Directory Structure

The automated Playwright test suite is organized into modular directories under `web/tests/`:

```
web/tests/
├── accessibility/                 # WCAG 2.2 AA automated scans (axe-core)
│   └── accessibility.spec.ts     # 16 tests covering all 10 routes & keyboard
├── e2e/                           # End-to-end multi-step workflow journeys
│   ├── authentication/           # WF-AUTH session, login, and tenant switching
│   ├── comparison/               # WF-CMP pairwise document diffing
│   ├── documents/                # WF-DOC ingestion, library, and inspector
│   ├── governance/               # WF-GOV review queue, verification, audit
│   ├── intelligence/             # WF-ASK grounded querying & citation drawer
│   ├── navigation/               # NAV-001..015 routes, breadcrumbs, history
│   └── operations/               # WF-OPS pipeline DAG, metrics, telemetry
├── fixtures/                      # Reusable Playwright fixtures & mock backends
│   ├── auth-fixture.ts           # Pre-authenticated user sessions & tokens
│   ├── mock-backend.ts           # API contract response fixtures
│   └── test-data.ts              # Canonical document payloads & citations
├── integration/                   # Frontend-backend contract verification
│   └── backend-features.spec.ts  # API-FE header injection & Zod contracts
├── interaction/                   # Granular component behavior
│   └── buttons-forms.spec.ts     # BTN, INP, DLG, TBL, NTF test specifications
├── responsive/                    # Viewport matrix & overflow audits
│   └── viewport.spec.ts          # 67 tests across 320px to 1920px viewports
└── visual/                        # Visual regression baseline screenshots
    └── visual-regression.spec.ts # 29 visual snapshot scenarios
```

---

## 2. Configuration (`web/playwright.config.ts`)

The test suite is managed via `playwright.config.ts` supporting targeted project isolation:

```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: "**/*.spec.ts",
  timeout: 30000,
  expect: { timeout: 5000 },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "e2e", testDir: "./tests/e2e" },
    { name: "navigation", testDir: "./tests/e2e/navigation" },
    { name: "interaction", testDir: "./tests/interaction" },
    { name: "integration", testDir: "./tests/integration" },
    { name: "visual", testDir: "./tests/visual" },
    { name: "accessibility", testDir: "./tests/accessibility" },
    { name: "responsive", testDir: "./tests/responsive" },
  ],
});
```

---

## 3. Reusable Test Fixtures

### Pre-Authenticated Test User Fixture (`fixtures/auth-fixture.ts`)
```typescript
import { test as base } from "@playwright/test";

export const test = base.extend({
  authenticatedPage: async ({ page }, use) => {
    // Inject development bypass token and default workspace context
    await page.goto("http://127.0.0.1:3000/");
    await page.evaluate(() => {
      localStorage.setItem("aegis_auth_token", "test-bearer-token-analyst");
      localStorage.setItem("aegis_active_workspace", "ws-default");
      localStorage.setItem("aegis_active_tenant", "tenant-enterprise-01");
    });
    await page.reload();
    await use(page);
  },
});
```

---

## 4. Execution Commands

```bash
# Run entire automated suite across all projects (196 tests)
npx playwright test

# Run specific project slices
npx playwright test --project=navigation
npx playwright test --project=interaction
npx playwright test --project=accessibility
npx playwright test --project=responsive
npx playwright test --project=e2e
npx playwright test --project=visual

# Run with interactive Playwright UI for local debugging
npx playwright test --ui
```
