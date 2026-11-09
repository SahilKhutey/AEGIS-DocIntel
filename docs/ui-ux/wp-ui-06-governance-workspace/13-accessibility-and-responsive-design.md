# 13 — Accessibility and Responsive Design

## 1. Accessibility Standards (WCAG 2.2 AA)

The Governance Workspace incorporates accessibility primitives established in WP-UI-02:

1. **Semantic HTML & Roles**:
   - `role="tablist"` and `role="tab"` with `aria-selected` for review queue and detail view tab bars.
   - Standard table structures with `<th scope="col">` for keyboard and screen reader accessibility.
   - `role="alert"` for stale version warnings and `role="status"` for success notifications.
   - `aria-busy="true"` on loading indicators.

2. **Color Contrast & Indicators**:
   - Status badges include both text labels and colored dots (e.g. green for approved, purple for corrected, rose for rejected).
   - Priority badges use high-contrast text combinations (`text-rose-700 bg-rose-50 border-rose-200`) ensuring ≥ 4.5:1 contrast ratios.

3. **Keyboard Navigation**:
   - All interactive controls (tabs, filter dropdowns, buttons, textareas, checkboxes) are accessible via standard Tab and Enter/Space controls.
   - Focus rings conform to Tailwind `focus:ring-1 focus:ring-blue-500` standards without focus trapping.

---

## 2. Responsive Breakpoint Behavior

- **Mobile (<640px)**:
  - Metric banners wrap into a 2x2 grid.
  - Review queue tables scroll horizontally with smooth momentum scrolling.
  - Verification and conflict panels stack comparative source passages vertically.
  - Decision buttons render in a 2x2 grid for thumb accessibility.
- **Tablet (640px - 1024px)**:
  - Metrics banner expands to 4 columns.
  - Side-by-side claim comparison aligns smoothly with moderate padding.
- **Desktop (≥1024px)**:
  - Full side-by-side comparative layout for conflict resolution and fact citation review.
