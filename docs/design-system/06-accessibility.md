# 06 — Accessibility Specification & Verification (WCAG 2.2 Level AA)

**Document Identifier**: `AEGIS-DOCINTEL-DS-006`  
**Work Package**: `WP-UI-02: Design System`  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. Compliance Standard & Scope

AEGIS-DocIntel formally targets **WCAG 2.2 Level AA** compliance across all workbench interfaces. Document intelligence analysis frequently involves multi-hour review sessions by compliance officers, legal analysts, and operational reviewers; accessibility is therefore an ergonomics and legal mandate, not an optional convenience.

---

## 2. Accessible Landmarks & Page Structure

Every screen must reside within the strict HTML5 landmark hierarchy established in `AppShell`:

```html
<a class="skip-link" href="#main-content">Skip to main content</a>

<header class="sticky top-0 z-40 ...">
  <!-- Brand Identity -->
  <a href="/" aria-label="AEGIS workspace home">...</a>

  <!-- Primary Desktop Navigation -->
  <nav aria-label="Primary navigation">...</nav>

  <!-- Mobile Navigation Bar -->
  <nav aria-label="Mobile navigation">...</nav>
</header>

<main id="main-content" tabIndex="-1" class="mx-auto w-full max-w-7xl ...">
  <!-- Route Content -->
</main>

<footer class="mt-auto ...">
  <!-- Operational Workspace Metadata -->
</footer>
```

### 2.1 Skip Link Behavior
- When the page loads, the skip-link is visually positioned off-screen (`left: -9999px;`).
- Upon receiving keyboard focus (the very first `Tab` keystroke), the skip-link slides down into view at `top: 1rem; left: 1rem;` with high-contrast styling (`background: var(--surface); color: var(--foreground); border: 2px solid var(--primary)`).
- Activating the skip-link transfers browser focus directly to `<main id="main-content">` via `tabIndex={-1}`, bypassing repeated navigation menus.

---

## 3. Keyboard Navigation & Focus Rings

### 3.1 Focus Indicator Contract
The global stylesheet enforces an uncompromised visible focus indicator for all keyboard-focusable elements:
```css
:focus-visible {
  outline: 3px solid var(--primary);
  outline-offset: 2px;
}
```
`outline: none` or `outline: 0` is strictly forbidden unless immediately accompanied by `:focus-visible` ring replacements.

### 3.2 Modal Dialog Focus Trapping
- Opening `<Dialog />` captures keyboard focus and restrains Tab cycling within the modal window.
- Pressing `Escape` triggers `onClose()`.
- Closing the modal restores focus to the invoking trigger button.

---

## 4. Contrast Compliance Matrix

All semantic tokens comply with WCAG 2.2 Level AA:

$$\text{Contrast Ratio} = \frac{L_1 + 0.05}{L_2 + 0.05}$$

- **Body Text**: `16.1 : 1` (exceeds $4.5 : 1$ requirement).
- **Secondary Muted Text**: `4.6 : 1` (exceeds $4.5 : 1$ requirement).
- **Primary Action Buttons**: `4.6 : 1` (exceeds $4.5 : 1$ requirement).
- **Focus Rings**: `4.7 : 1` (exceeds $3.0 : 1$ requirement).
- **Dark Mode Body**: `15.2 : 1` (exceeds $4.5 : 1$ requirement).

---

## 5. Non-Color Status Communication

Under WCAG 2.2 Success Criterion 1.4.1 (Use of Color), color must not be the sole visual means of conveying information or indicating an action:
- **Status Badges**: Always render both a colored circular status indicator *and* a plain-language capitalized text label (`Ready`, `Indexing`, `Failed`, `Approved`, `Rejected`).
- **Alert Banners**: Incorporate distinctive Unicode glyphs (`ℹ️`, `✓`, `⚠`, `⨂`) before the title text.
- **Form Validation**: Combines red border highlighting with `aria-invalid="true"` and an explicit error explanation paragraph.

---

## 6. Motion Sensitivity & Reduced Motion

The global stylesheet respects the user's operating system preferences for reduced motion:
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```
All CSS pulse animations (such as `<Skeleton />`) and transitions collapse immediately to zero-duration when reduced motion is preferred.
