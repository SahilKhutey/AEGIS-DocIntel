# WP-UI-08: Playwright Test Architecture

## 1. Project Organization

Playwright is configured across three dedicated projects in `web/playwright.config.ts`:

```text
web/tests/
├── e2e/                     Functional & integration browser journeys (87 tests)
│   ├── e2e-user-journeys.spec.ts         3 critical end-to-end user workflows
│   ├── isolation-and-security.spec.ts    Workspace selector & boundary controls
│   ├── document-library.spec.ts          Document ingestion & status filters
│   ├── governance/                       Review queue, decisions, audit history
│   └── advanced/                         Analytics, math, pipelines, monitoring, developer
├── accessibility/           axe-core automated WCAG 2.2 AA audits (12 tests)
│   └── accessibility.a11y.spec.ts
└── responsive/              Multi-viewport layout stability audits (60 tests)
    └── routes.responsive.spec.ts
```

---

## 2. WebServer Orchestration

Playwright automatically spawns and lifecycle-manages the Next.js production server:

```typescript
webServer: {
  command: "npm run start -- -p 3000",
  url: "http://127.0.0.1:3000",
  reuseExistingServer: true,
  timeout: 30000,
}
```

This guarantees that browser tests execute against real production Turbopack builds rather than development bundles, catching subtle build-time tree-shaking and CSS bundling anomalies.

---

## 3. Mock Strategy & CORS Compliance

When testing end-to-end flows without a live FastAPI cluster, Playwright intercepts requests via `page.route()`. Because browser fetches execute cross-origin (port 3000 to port 8000), mocked handlers must strictly handle preflight `OPTIONS` requests:

```typescript
const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "*",
};

async function handleCorsMock(route: Route, jsonBody: unknown, status = 200) {
  if (route.request().method() === "OPTIONS") {
    await route.fulfill({ status: 204, headers: CORS_HEADERS });
    return;
  }
  await route.fulfill({
    status,
    headers: CORS_HEADERS,
    contentType: "application/json",
    body: JSON.stringify(jsonBody),
  });
}
```
