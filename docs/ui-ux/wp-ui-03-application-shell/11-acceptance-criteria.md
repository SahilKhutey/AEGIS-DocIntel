# 11 — Acceptance Criteria & Release Gates

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03-11`  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: APPROVED ARCHITECTURE  

---

## 1. Release Gates Matrix (AS-01 through AS-17)

Every release gate represents a binary, automated requirement that must pass before WP-UI-03 is accepted for production integration.

| Gate ID | Criteria Description | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| **AS-01** | Skip-link is the first focusable element in DOM and receives focus on initial Tab press. | Automated Playwright (`accessibility.spec.ts`) | **PASSED** |
| **AS-02** | Desktop sidebar renders all 5 workflow groups with valid group labels. | Automated Playwright (`shell-navigation.spec.ts`) | **PASSED** |
| **AS-03** | Planned routes (`status: "planned"`) are completely omitted from operational navigation. | Automated Playwright (`navigation.spec.ts`) | **PASSED** |
| **AS-04** | Active route is decorated with `aria-current="page"` and distinct visual indicator. | Automated Playwright (`shell-navigation.spec.ts`) | **PASSED** |
| **AS-05** | Workspace selector listbox toggles on click and closes on Escape key press. | Automated Playwright (`workspace-selector.spec.ts`) | **PASSED** |
| **AS-06** | Selecting a workspace fires the `onWorkspaceSelect` callback. | Automated Vitest (`shell-state.test.ts`) | **PASSED** |
| **AS-07** | Breadcrumbs accurately mirror the route hierarchy and parent segments are clickable. | Automated Vitest & Playwright (`breadcrumbs.test.ts`) | **PASSED** |
| **AS-08** | Notification bell displays unread count badge. | Automated Playwright (`notifications.spec.ts`) | **PASSED** |
| **AS-09** | Notification flyout opens, lists items, and closes on Escape key press. | Automated Playwright (`notifications.spec.ts`) | **PASSED** |
| **AS-10** | Global search input debounces queries by 300ms and provides clear trigger. | Automated Playwright (`global-search.spec.ts`) | **PASSED** |
| **AS-11** | External URLs and invalid schemes are blocked from search redirection. | Automated Vitest (`shell-state.test.ts`) | **PASSED** |
| **AS-12** | Mobile navigation drawer opens via hamburger trigger and closes via Escape. | Automated Playwright (`responsive-shell.spec.ts`) | **PASSED** |
| **AS-13** | Body overflow is locked when mobile navigation drawer is active. | Automated Vitest & Code Inspection (`mobile-navigation.tsx`) | **PASSED** |
| **AS-14** | Shell displays zero horizontal scroll overflow across 375px, 768px, 1024px, 1440px. | Automated Playwright (`responsive-shell.spec.ts`) | **PASSED** |
| **AS-15** | Existing application pages (`/`, `/documents`, `/ask`, `/compare`, `/reviews`) load and operate without regression. | Automated Playwright (`workbench.spec.ts`, `user-journeys.spec.ts`) | **PASSED** |
| **AS-16** | TypeScript compiler check (`tsc --noEmit`) passes with 0 errors. | Command execution | **PASSED** |
| **AS-17** | ESLint static analysis passes with 0 warnings and 0 errors. | Command execution | **PASSED** |

---

## 2. Release Decision

All 17 acceptance release gates (AS-01 through AS-17) are fully verified and passing. WP-UI-03 meets the full Definition of Done and is approved for deployment.
