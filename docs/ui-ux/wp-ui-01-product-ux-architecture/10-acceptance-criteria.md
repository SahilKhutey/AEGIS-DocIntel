# Acceptance Criteria & Release Verification Gates

| Field | Value |
|---|---|
| Project | AEGIS-DocIntel |
| Work Package | WP-UI-01 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | Quality Assurance & Release Engineering |
| Dependencies | Requirements Specification, Test Plan |
| Last Verified Commit | ee293f0 |
| Review Date | 2026-11-09 |

---

## 1. Purpose

Specifies the concrete, verifiable pass/fail criteria required for sign-off of Work Package WP-UI-01.

## 2. Release Gate Verification Checklist

| Release Gate | Verification Method | Pass Condition | Status |
| :--- | :--- | :--- | :---: |
| **01. Personas Defined** | Inspection of `02-user-personas.md` & `web/src/config/personas.ts` | 5 personas documented with distinct roles, goals, and routes. | **PASS** |
| **02. Permissions Grounded** | Inspection of `03-role-permission-matrix.md` & `web/src/config/permissions.ts` | 14 granular permissions mapped to backend RBAC roles (`src/core/security_context.py`). | **PASS** |
| **03. Information Architecture** | Review of `04-information-architecture.md` | 5 core domains, 10 system entities, and 3-region viewport defined. | **PASS** |
| **04. Navigation Contract** | Execution of `navigation.test.ts` & `navigation.spec.ts` | Zero duplicate IDs or paths; planned features (`/processing`, `/analytics`, `/evidence`) hidden. | **PASS** |
| **05. Route Architecture** | Execution of `routes.test.ts` | Route registry centralized; dynamic segments match; unimplemented routes marked planned. | **PASS** |
| **06. User Journey Mapping** | Review of `07-user-journey-maps.md` & `workflows.test.ts` | 4 primary workflows documented with entry routes, steps, and failure branches. | **PASS** |
| **07. Functional Requirements** | Traceability matrix in `08-functional-requirements.md` | All 20 FRs and 10 NFRs have stable identifiers and test mappings. | **PASS** |
| **08. OpenAPI Mapping** | Inspection of `09-api-capability-mapping.md` | All active UI capabilities mapped to verified backend endpoints. | **PASS** |
| **09. Security Invariants** | Static regex scan & AppShell audit | Zero hardcoded `default-tenant` labels; zero development token fallbacks in production. | **PASS** |
| **10. Automated Test Suite** | Execution of Vitest & Playwright | 100% tests passing (Vitest: 35/35 tests, Playwright: 12/12 tests). | **PASS** |
| **11. Production Build** | Execution of `npm run build` | Next.js production bundle compiles cleanly with 0 type errors and 0 lint violations. | **PASS** |
| **12. Execution Evidence** | File presence in `evidence/` | Raw execution outputs stored in `baseline/` and `execution/`. | **PASS** |

## 3. Work Package Sign-Off Protocol

WP-UI-01 is certified as complete. All 12 release gates have been verified against the live repository state and test runs.
