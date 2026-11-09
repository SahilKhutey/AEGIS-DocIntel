# WP-UI-08: Baseline & Runtime Environment

## 1. Baseline Verification

The integration activities of WP-UI-08 began from the stable HEAD of WP-UI-07:

- **Baseline Commit**: `c1ff775b1d3ef37faea37e8c617c60ee1f67f0bf`
- **Prior Work Packages Committed**:
  - `4d86023`: WP-UI-01 Product UX Architecture
  - `60be08d`: WP-UI-02 Design System
  - `b61c4fa`: WP-UI-03 Application Shell
  - `2b39e9b`: WP-UI-04 Core Workspace
  - `c1ff775`: WP-UI-05, WP-UI-06, WP-UI-07 Intelligence, Governance, and Advanced Interfaces
- **Pre-existing Test Baseline**: 42 test suites, 194 passed tests (100%), 0 failures.

---

## 2. Environment & Dependency Matrix

| Component | Verified Version | Purpose |
| :--- | :--- | :--- |
| **Node.js** | `v24.18.0` | JavaScript runtime environment |
| **npm** | `11.16.0` | Package manager |
| **Next.js** | `16.4.3` | React framework with Turbopack and Partial Prerendering |
| **React** | `19.2.4` | Component UI library |
| **TypeScript** | `5.9.3` | Type system and static analysis |
| **Vitest** | `5.0.5` | Unit and integration testing runner |
| **Playwright** | `1.58.2` | End-to-end browser testing automation |
| **@axe-core/playwright** | `4.11.1` | Automated WCAG 2.2 AA accessibility auditor |
| **Zod** | `3.25.76` | Runtime contract validation schemas |
| **Tailwind CSS** | `4.1.18` | Utility-first CSS token framework |
| **Lucide React** | `1.16.0` | Accessible icon library |

---

## 3. Public Environment Variable Contract

Environment variables are validated at runtime through `web/src/lib/validation/environment.ts` using `PublicEnvironmentSchema`. This prevents misconfiguration while ensuring private secrets are never exposed on client bundles.

| Variable Name | Required | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_API_BASE_URL` | No | `http://127.0.0.1:8000` | Base URL of FastAPI gateway |
| `NEXT_PUBLIC_AEGIS_DEV_TOKEN`| No | `dev-default-tenant` | Development authentication bypass token |
| `NEXT_PUBLIC_WS_BASE_URL` | No | `ws://127.0.0.1:8000/v1/ws`| WebSocket streaming telemetry endpoint |
| `NEXT_PUBLIC_ENVIRONMENT` | No | `development` | Deployment tier: `development`, `staging`, `production` |
