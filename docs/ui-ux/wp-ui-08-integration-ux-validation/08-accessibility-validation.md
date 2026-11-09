# WP-UI-08: Accessibility (a11y) Certification

## 1. Compliance Standard

AEGIS-DocIntel is certified to meet **WCAG 2.2 Level AA** standards. Automated accessibility testing is executed via `@axe-core/playwright` across all 10 core workspace views (`web/tests/accessibility/accessibility.a11y.spec.ts`).

---

## 2. Automated Axe-Core Audit Results

| Route | Viewport | Target Elements Scanned | Violations (Critical) | Violations (Serious) | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/` | 1280x800 | Overview, stats, shell header, sidebar | 0 | 0 | **PASS** |
| `/documents` | 1280x800 | Library table, search, status filters | 0 | 0 | **PASS** |
| `/ask` | 1280x800 | Question composer, chat history, citations | 0 | 0 | **PASS** |
| `/compare` | 1280x800 | Document selector, comparison matrix | 0 | 0 | **PASS** |
| `/reviews` | 1280x800 | Review queue, priority badges, actions | 0 | 0 | **PASS** |
| `/analytics` | 1280x800 | KPI cards, time range, charts, export | 0 | 0 | **PASS** |
| `/mathematics` | 1280x800 | Vector viewer, matrix cells, LaTeX formulas | 0 | 0 | **PASS** |
| `/pipelines` | 1280x800 | Pipeline runs, DAG graph, status indicators | 0 | 0 | **PASS** |
| `/monitoring` | 1280x800 | Telemetry health cards, latency SLAs | 0 | 0 | **PASS** |
| `/developer` | 1280x800 | API explorer, webhook manager, credentials | 0 | 0 | **PASS** |

---

## 3. Notable Remediations Implemented During WP-UI-08

1. **WCAG 2.5.3: Label in Name**:
   - *Problem*: In `app-sidebar.tsx`, the home brand link `<a aria-label="AEGIS home">` failed because its visible text was `"AEGIS DocIntel"`.
   - *Fix*: Removed artificial `aria-label` override, allowing the accessible name to calculate naturally from the visible brand text (using `sr-only` for collapsed mode).
2. **WCAG 2.2 SC 2.5.8: Target Size Minimum (24x24px)**:
   - *Problem*: Small time-range buttons and compact table triggers in analytics and mathematics fell below the 24x24px threshold.
   - *Fix*: Enforced `min-height: 28px; min-width: 28px;` globally in `globals.css` and dedicated component wrappers.
3. **Definition List ARIA Structure (`definition-list`)**:
   - *Problem*: In `ProvenanceViewer.tsx`, a `<span className="...">` was a direct child of a `<div>` inside a `<dl>`, violating definition list markup rules.
   - *Fix*: Encapsulated all secondary descriptions directly within `<dd>` elements, ensuring strictly permitted `<dt>` and `<dd>` tag structures.
4. **Combobox ARIA Attributes on Global Search**:
   - *Problem*: Input with `aria-expanded` and `aria-controls` triggered `aria-allowed-attr` violation on a standard textbox.
   - *Fix*: Added `role="combobox"` and `aria-autocomplete="list"` to provide full WAI-ARIA combobox semantics.
