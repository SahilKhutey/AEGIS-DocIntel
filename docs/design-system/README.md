# WP-UI-02 — Design System & Visual Foundation

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-02`  
**Classification**: Engineering & UX Architecture Specification  
**Work Package**: `WP-UI-02: Design System`  
**Target Standard**: `WCAG 2.2 Level AA`  
**Status**: ACTIVE IMPLEMENTATION  
**Version**: `2.0.0`  

---

## 1. Overview & Purpose

Work Package `WP-UI-02` establishes the unified visual language, design token architecture, reusable component library, accessibility guidelines, and responsive standards for the **AEGIS-DocIntel** Document Intelligence Workbench.

Following the foundational product architecture delivered in `WP-UI-01`, this package ensures that every current and future screen in AEGIS:
1. Adheres to deterministic, centralized design tokens (colors, typography, spacing, radius, elevation).
2. Uses robust, accessible, and independently tested component primitives.
3. Complies with WCAG 2.2 Level AA accessibility standards (visible keyboard focus, programmatically associated labels, semantic HTML landmarks, non-color-only status indicators).
4. Maintains responsive integrity across mobile (375px+), tablet (768px), desktop (1024px+), and wide workspaces (1440px+) without horizontal scroll degradation.
5. Extends the existing Next.js 16 / React 19 application in `web/` cleanly without disrupting established backend API contracts or route behavior.

---

## 2. Document Inventory

The design system specification is organized into 10 structured specifications:

| Document | Title | Scope & Purpose |
| :--- | :--- | :--- |
| [`01-design-principles.md`](./01-design-principles.md) | Design Principles & Philosophy | Core UX tenets: Information Density without Clutter, Provenance Hierarchy, Sovereign Human Governance. |
| [`02-color-system.md`](./02-color-system.md) | Semantic Color Architecture | Light and dark theme palettes, semantic roles, contrast audit ratios, and CSS variables. |
| [`03-typography.md`](./03-typography.md) | Typography System | Font families, modular type scale, line heights, font roles, and monospace rules. |
| [`04-spacing-layout.md`](./04-spacing-layout.md) | Spacing & Layout System | 4px base spacing scale, container widths, grid rules, elevation levels, and geometry radiuses. |
| [`05-component-library.md`](./05-component-library.md) | Shared Component Library | APIs, variant matrices, keyboard behaviors, and usage guidelines for all UI primitives. |
| [`06-accessibility.md`](./06-accessibility.md) | Accessibility & Compliance (WCAG 2.2 AA) | Keyboard navigation, skip link, ARIA landmarks, live regions, and contrast verification. |
| [`07-responsive-design.md`](./07-responsive-design.md) | Responsive Design & Breakpoints | Mobile, tablet, desktop, and wide desktop layout policies and non-overflow rules. |
| [`08-functional-requirements.md`](./08-functional-requirements.md) | Requirements & Traceability | Traceable functional (UI02-FR-001–020) and non-functional requirements (UI02-NFR-001–007). |
| [`09-acceptance-criteria.md`](./09-acceptance-criteria.md) | Acceptance Criteria & Release Gates | Formal definition of done and release criteria (Gates DS-01 through DS-12). |
| [`10-test-plan.md`](./10-test-plan.md) | Verification & Test Plan | Unit, component contract, Playwright browser, responsive, and accessibility test suites. |

---

## 3. Repository Architecture

```
web/
├── src/
│   ├── app/
│   │   └── globals.css             # Unified global stylesheet importing tokens, themes & typography
│   ├── styles/
│   │   ├── tokens.css              # Base semantic CSS variables (4px grid, colors, typography)
│   │   ├── themes.css              # Theme overrides ([data-theme="dark"])
│   │   └── typography.css          # Global typography, heading styles, and code block styling
│   ├── config/
│   │   ├── breakpoints.ts          # Centralized viewport breakpoint constants
│   │   └── design-system.ts        # Design system metadata and token manifest
│   ├── components/
│   │   ├── app-shell.tsx           # Application shell with accessible skip-link and landmarks
│   │   └── ui/                     # Shared UI component primitives
│   │       ├── button.tsx          # Button: primary, secondary, outline, ghost, danger
│   │       ├── badge.tsx           # Badge: default, success, warning, danger, info
│   │       ├── card.tsx            # Card: default, interactive, selected
│   │       ├── input.tsx           # Accessible text input with aria-invalid
│   │       ├── textarea.tsx        # Accessible textarea with aria-invalid
│   │       ├── select.tsx          # Accessible select dropdown
│   │       ├── checkbox.tsx        # Accessible checkbox with label association
│   │       ├── dialog.tsx          # Accessible modal dialog with focus management
│   │       ├── tooltip.tsx         # Accessible keyboard/hover tooltip primitive
│   │       ├── table.tsx           # Responsive structured data table primitives
│   │       ├── skeleton.tsx        # Loading skeleton placeholders (text, card, table)
│   │       ├── alert.tsx           # Accessible status/alert callout
│   │       └── index.ts            # Barrel export
│   └── lib/
│       └── cn.ts                   # Class name merger utility
└── tests/
    ├── unit/
    │   ├── design-tokens.test.ts   # Design token presence verification
    │   ├── button.test.tsx         # Button variant, loading, and disabled test suite
    │   ├── input.test.tsx          # Input accessibility and invalid state test suite
    │   └── component-contracts.test.tsx # Component contract verification suite
    └── e2e/
        ├── responsive.spec.ts      # Multi-viewport responsive verification (Playwright)
        ├── accessibility.spec.ts   # Keyboard navigation and landmark audit (Playwright)
        └── design-system.spec.ts   # Browser design system token and layout verification
```

---

## 4. Execution & Verification Summary

To execute the test suites and verify the design system:

```bash
# Run Vitest unit & component test suites
cd web
npx vitest run

# Run TypeScript typecheck
npx tsc --noEmit

# Run ESLint static analysis
npx eslint .

# Build Next.js production bundle
npm run build

# Run Playwright E2E browser test suites
npx playwright test
```
