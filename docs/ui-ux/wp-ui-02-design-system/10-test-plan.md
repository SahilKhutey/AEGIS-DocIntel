# 10 — Verification & Automated Test Plan

**Document Identifier**: `AEGIS-DOCINTEL-DS-010`  
**Work Package**: `WP-UI-02: Design System`  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. Test Architecture & Verification Matrix

The AEGIS-DocIntel Design System verification suite consists of multiple testing layers designed to catch regressions in design tokens, component contracts, accessibility compliance, and multi-viewport layouts.

| Test ID | Test Category | Target Component / Area | Verification Framework | Pass Threshold |
| :--- | :--- | :--- | :--- | :---: |
| **UI02-T01** | Token Verification | `tokens.css` semantic variables | Vitest (`design-tokens.test.ts`) | 12/12 tokens |
| **UI02-T02** | Component Contract | Button variants, sizes, and styles | Vitest (`button.test.tsx`) | 100% pass |
| **UI02-T03** | Component State | Button loading state and `aria-busy` | Vitest (`button.test.tsx`) | 100% pass |
| **UI02-T04** | Component Behavior | Button disabled click interception | Vitest (`button.test.tsx`) | 100% pass |
| **UI02-T05** | Form Semantics | Input accessible labeling | Vitest (`input.test.tsx`) | 100% pass |
| **UI02-T06** | Validation State | Input `aria-invalid` exposure | Vitest (`input.test.tsx`) | 100% pass |
| **UI02-T07** | Control Disabling | Input disabled interaction | Vitest (`input.test.tsx`) | 100% pass |
| **UI02-T08** | Badge Contracts | Badge variant styling (success, danger, info) | Vitest (`component-contracts.test.tsx`) | 100% pass |
| **UI02-T09** | Card Contracts | Card surface and interactive hover elevation | Vitest (`component-contracts.test.tsx`) | 100% pass |
| **UI02-T10** | Form Primitives | Textarea, Select, Checkbox contract behavior | Vitest (`component-contracts.test.tsx`) | 100% pass |
| **UI02-T11** | Dialog Semantics | Dialog open/close, Escape key listener | Vitest (`component-contracts.test.tsx`) | 100% pass |
| **UI02-T12** | Tooltip Semantics | Tooltip hover/focus triggering & `role="tooltip"` | Vitest (`component-contracts.test.tsx`) | 100% pass |
| **UI02-T13** | Table Semantics | Structured responsive table rendering | Vitest (`component-contracts.test.tsx`) | 100% pass |
| **UI02-T14** | Skeleton Attributes | Skeleton loading placeholders with `aria-busy` | Vitest (`component-contracts.test.tsx`) | 100% pass |
| **UI02-T15** | Alert Semantics | Alert banners with `role="alert"` / `role="status"` | Vitest (`component-contracts.test.tsx`) | 100% pass |
| **UI02-T16** | Token Exposure | `:root` custom properties in browser DOM | Playwright (`design-system.spec.ts`) | 100% pass |
| **UI02-T17** | Keyboard Focus | Skip-link visibility and focus via Tab key | Playwright (`accessibility.spec.ts`) | 100% pass |
| **UI02-T18** | Landmark Audit | Presence of accessible `<main>` landmark | Playwright (`accessibility.spec.ts`) | 100% pass |
| **UI02-T19** | Accessible Names | Primary buttons have non-empty accessible names | Playwright (`accessibility.spec.ts`) | 100% pass |
| **UI02-T20** | Responsive Mobile | iPhone viewport (375x812) zero horizontal overflow | Playwright (`responsive.spec.ts`) | 100% pass |
| **UI02-T21** | Responsive Tablet | iPad portrait (768x1024) zero horizontal overflow | Playwright (`responsive.spec.ts`) | 100% pass |
| **UI02-T22** | Responsive Desktop | Workstation (1440x900) zero horizontal overflow | Playwright (`responsive.spec.ts`) | 100% pass |
| **UI02-T23** | Route Regression | Document, Ask, Compare, Reviews page journeys | Playwright (`workbench.spec.ts`) | 100% pass |

---

## 2. Test Execution Commands

```bash
# Execute full Vitest unit & contract suite
cd web
npx vitest run

# Execute full Playwright browser suite
npx playwright test

# Execute static typecheck
npx tsc --noEmit

# Execute linter
npx eslint .

# Execute full Next.js production build
npm run build
```
