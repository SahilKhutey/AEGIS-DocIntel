# 08 — Functional & Non-Functional Requirements Specification

**Document Identifier**: `AEGIS-DOCINTEL-DS-008`  
**Work Package**: `WP-UI-02: Design System`  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. Traceability Matrix — Functional Requirements

| ID | Requirement Statement | Priority | Implementation Artifact | Verification Test |
| :--- | :--- | :---: | :--- | :--- |
| **UI02-FR-001** | Centralized semantic color tokens | P0 | `web/src/styles/tokens.css` | `tests/unit/design-tokens.test.ts` |
| **UI02-FR-002** | Light and dark theme tokens | P1 | `web/src/styles/themes.css` | `tests/e2e/design-system.spec.ts` |
| **UI02-FR-003** | Typography scale and font roles | P0 | `web/src/styles/typography.css` | `03-typography.md` & CSS audit |
| **UI02-FR-004** | Spacing, radius, elevation and sizing tokens | P0 | `web/src/styles/tokens.css` | `tests/unit/design-tokens.test.ts` |
| **UI02-FR-005** | Responsive breakpoints and layout rules | P0 | `web/src/config/breakpoints.ts` | `tests/e2e/responsive.spec.ts` |
| **UI02-FR-006** | Reusable button variants and states | P0 | `web/src/components/ui/button.tsx` | `tests/unit/button.test.tsx` |
| **UI02-FR-007** | Reusable cards, badges and status indicators | P0 | `badge.tsx`, `card.tsx` | `tests/unit/component-contracts.test.tsx` |
| **UI02-FR-008** | Accessible form controls (input, textarea, select, checkbox) | P0 | `input.tsx`, `textarea.tsx`, `select.tsx`, `checkbox.tsx` | `tests/unit/input.test.tsx`, `component-contracts.test.tsx` |
| **UI02-FR-009** | Dialog, tooltip and alert patterns | P1 | `dialog.tsx`, `tooltip.tsx`, `alert.tsx` | `tests/unit/component-contracts.test.tsx` |
| **UI02-FR-010** | Table, skeleton and empty-state patterns | P0 | `table.tsx`, `skeleton.tsx` | `tests/unit/component-contracts.test.tsx` |
| **UI02-FR-011** | Enforce visible keyboard focus (`:focus-visible`) | P0 | `web/src/app/globals.css` | `tests/e2e/accessibility.spec.ts` |
| **UI02-FR-012** | Meet defined text and non-text contrast requirements | P0 | `web/src/styles/tokens.css` | `02-color-system.md` contrast audit |
| **UI02-FR-013** | Respect reduced-motion preferences | P1 | `web/src/app/globals.css` | CSS media query inspection |
| **UI02-FR-014** | Support mobile, tablet and desktop layouts | P0 | `AppShell`, `breakpoints.ts` | `tests/e2e/responsive.spec.ts` |
| **UI02-FR-015** | Document component variants and usage rules | P0 | `05-component-library.md` | Manual architecture review |
| **UI02-FR-016** | Test design tokens and component contracts | P0 | `tests/unit/` | Vitest automated suite (68 tests) |
| **UI02-FR-017** | Test keyboard and screen-reader semantics | P0 | `tests/e2e/accessibility.spec.ts` | Playwright accessibility suite |
| **UI02-FR-018** | Test responsive layouts on critical routes | P0 | `tests/e2e/responsive.spec.ts` | Playwright responsive suite (3 viewports) |
| **UI02-FR-019** | Prevent unauthorized one-off styling patterns in shared code | P1 | `tokens.css`, `cn.ts` | Static code review & token tests |
| **UI02-FR-020** | Preserve existing application functionality during migration | P0 | `web/src/app/*` routes | Playwright E2E suite (`workbench.spec.ts`) |

---

## 2. Non-Functional Requirements (NFR)

- **UI02-NFR-001 (Modularity)**: Components must be reusable, self-contained, and independently testable without circular dependencies.
- **UI02-NFR-002 (Centralization)**: All visual design tokens must be centrally maintained in `tokens.css`, `themes.css`, and `typography.css`.
- **UI02-NFR-003 (Zero Runtime Overhead)**: The design system must not introduce heavy external UI runtime dependencies (e.g., bulky CSS-in-JS libraries).
- **UI02-NFR-004 (Zero Viewport Overflow)**: Responsive layouts must never cause horizontal scrolling at the document root level across all supported viewports ($375\text{px} \le W \le 1440\text{px}$).
- **UI02-NFR-005 (Accessibility Semantics)**: All interactive components must expose appropriate HTML tags, accessible names, ARIA states, and keyboard triggers.
- **UI02-NFR-006 (Dark Theme Legibility)**: Dark theme activation via `[data-theme="dark"]` must maintain contrast ratios $\ge 4.5:1$ for body text and $\ge 3.0:1$ for UI controls.
- **UI02-NFR-007 (Contract Preservation)**: The design system integration must preserve existing FastAPI backend endpoints, Zod validation schemas, and route behavior.
