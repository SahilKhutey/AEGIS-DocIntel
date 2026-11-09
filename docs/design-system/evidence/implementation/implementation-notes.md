# Implementation Notes — Work Package WP-UI-02

## 1. Technical Baseline & Decisions

- **Framework**: Next.js 16.4.3 App Router, React 19.3.0, TypeScript 5, Tailwind CSS 4.
- **Tailwind CSS 4 Architecture**:
  - `@import "tailwindcss";` placed at the very top of `web/src/app/globals.css`.
  - Semantic token stylesheets imported immediately after: `tokens.css`, `themes.css`, and `typography.css`.
  - Avoided duplicating base color rules or generating conflicting inline classes.
- **Component Primitives**:
  - All primitives implemented with standard React 19 + TypeScript attributes under `web/src/components/ui/`.
  - Primitives use `className={cn(...)}` for class composition.
  - Zero heavy external runtime component dependencies installed.
- **Accessibility & Focus Indicators**:
  - Accessible skip link implemented at the top of `AppShell`: `<a className="skip-link" href="#main-content">Skip to main content</a>`.
  - Main landmark receives `tabIndex={-1}` and `id="main-content"` for immediate keyboard routing.
  - Global `:focus-visible` ring provides 3px solid `--primary` outline with 2px offset.
