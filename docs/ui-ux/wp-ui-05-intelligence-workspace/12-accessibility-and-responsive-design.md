# 12 — Accessibility & Responsive Design

## 1. Accessibility Compliance (WCAG 2.2 AA)
The Intelligence Workspace conforms to WCAG 2.2 Level AA accessibility standards:
1. **Interactive Controls & Keyboard Navigation**:
   - Every button and interactive control has an accessible name (e.g., `aria-label="Ask AEGIS a question"`, `aria-label="Visual graph view"`, `aria-label="Accessible table view"`).
   - Skip link jumps directly to `#main-content`.
   - Focus rings use high-visibility blue outlines (`focus-visible:ring-2 focus-visible:ring-blue-500`).
2. **Accessible Knowledge Graph Alternative**:
   - Visual SVG graphs can be difficult or impossible for screen readers or keyboard-only users.
   - We implemented a seamless view switcher providing an **Accessible Structured Table View** with standard `<table>`, `<thead>`, `<tbody>`, and semantic cells containing node labels, types, IDs, and relationships.
3. **Contrast Ratios**:
   - Text contrast meets or exceeds 4.5:1 for body copy and 3:1 for large headings across both light and dark themes.
4. **Color Independence**:
   - Never relies solely on color to communicate state: status badges include text labels ("Verified Grounded", "Safe Abstention", "Conflict").

## 2. Responsive Breakpoint Strategy
- **Mobile (< 640px)**:
  - Linear single-column flow.
  - Horizontal scrolling pill bars for document selection.
  - Bottom-stacked evidence list on `/ask`.
- **Tablet (640px - 1024px)**:
  - 2-column comparison grids.
  - Collapsible panels.
- **Desktop (>= 1024px)**:
  - 3-column grounded workspace on `/ask` (Scope & History, Query Composer, Evidence Panel).
  - 4-column canvas + inspector on `/intelligence/knowledge`.
