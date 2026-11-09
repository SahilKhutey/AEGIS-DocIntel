# 13 — Accessibility and Responsive Design

## 1. WCAG 2.2 AA Conformance
All WP-UI-07 interfaces satisfy WCAG 2.2 AA accessibility requirements:
1. **Semantic Landmarking**:
   - Containers use `role="region"` with descriptive `aria-label` tags (e.g. `aria-label="Total Documents metric"`).
   - Time range presets grouped via `role="group"` with `aria-pressed` states on active buttons.
2. **Keyboard Navigability**:
   - Interactive elements (tabs, matrix cells, pipeline stage nodes) are focusable via `Tab` and activated via `Enter` or `Space`.
   - Data tables provide accessible sorting buttons with `aria-label="Sort by {header}"` and dynamic chevrons.
3. **Color Contrast & State Redundancy**:
   - Metrics and status indicators (succeeded, running, failed) do not rely solely on color. Every indicator includes semantic text, icons, and contrast ratios $\ge 4.5:1$ against backgrounds.

## 2. Responsive Breakpoint Matrix
- **Mobile (< 640px)**: Single-column metric stacking, horizontal scroll wrappers on matrix grids and pipeline DAGs.
- **Tablet (640px - 1024px)**: 2-column KPI grids, condensed parameter tables.
- **Desktop (1024px - 1280px)**: 3-column layouts, side-by-side code snippets and JSON response viewers.
- **Widescreen (>= 1280px)**: 6-column KPI overview grid, full-width DAG stage workflows.
