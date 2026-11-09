# AEGIS-DocIntel — UX Acceptance Criteria

## 1. Quality Gates & Verification Standards

Work Package WP-UI-01 requires passing all of the following verification criteria prior to sign-off:

| Criteria ID | Category | Target Requirement | Pass Threshold |
| :--- | :--- | :--- | :---: |
| **AC-01** | Architecture | Navigation is centralized in `web/src/config/navigation.ts` and routes in `web/src/config/routes.ts`. | 100% centralized |
| **AC-02** | Security | Hardcoded tenant labels (e.g. `Tenant: default-tenant`) removed from rendered UI shell. | 0 occurrences |
| **AC-03** | Security | API client contains zero production fallback bearer tokens (`dev-default-tenant`). | 0 occurrences in prod |
| **AC-04** | Navigation | Planned features (`/processing`, `/evidence`, `/analytics`, `/settings`) are marked planned and omitted from active links. | 0 planned links shown |
| **AC-05** | Usability | Active route styling persists accurately for nested sub-routes (`/documents/doc-123`, `/reviews/rev-456`). | 100% active state match |
| **AC-06** | Usability | Unrelated prefix routes (e.g. `/documents-old`) do not trigger false positive active states. | 0 false matches |
| **AC-07** | Accessibility | Shell contains `<nav aria-label="Primary navigation">`, `<main id="main-content">`, and valid `aria-current="page"`. | 100% compliant |
| **AC-08** | Responsiveness | Responsive mobile navigation bar renders on viewports $< 768px$ with horizontal scroll. | No horizontal page bleed |
| **AC-09** | Quality | Unit test suite (`web/tests/unit/navigation.test.ts`) passes with 100% green assertions. | All tests pass |
| **AC-10** | Quality | Playwright navigation suite (`web/tests/e2e/navigation.spec.ts`) passes across headless browser runs. | All scenarios pass |
| **AC-11** | Build | Next.js production build (`npm run build`) compiles with zero TypeScript errors and zero lint violations. | Clean production build |
