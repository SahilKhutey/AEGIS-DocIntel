# 07 — Responsive Design & Breakpoint Specification

**Document Identifier**: `AEGIS-DOCINTEL-DS-007`  
**Work Package**: `WP-UI-02: Design System`  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. Responsive Philosophy & Task Preservation

In high-assurance document analysis, responsive design must **preserve analytical context**, not arbitrarily remove features. When an analyst switches from a 32-inch 4K monitor to an iPad or mobile device during an emergency compliance review:
1. Critical data fields (confidence score, citation quotes, bounding coordinates) must **never be silently omitted**.
2. Document comparison interfaces must transition into tabbed or stacked selectors rather than hiding the second document.
3. Tables must prioritize key identity columns and provide smooth horizontal touch scrolling for extensive metadata.
4. The page-level viewport must never suffer unintentional horizontal overflow ($W_{\text{document}} \le W_{\text{viewport}}$).

---

## 2. Breakpoint Architecture

AEGIS-DocIntel standardizes on four responsive tiers configured in `web/src/config/breakpoints.ts`:

```typescript
export const BREAKPOINTS = {
  mobile: 640,
  tablet: 768,
  desktop: 1024,
  wide: 1280,
} as const;
```

| Tier Name | Viewport Range | Primary Behavior & Form Factor |
| :--- | :---: | :--- |
| **Mobile** | `320px – 639px` | Single-column linear layout. Top sticky mobile navigation bar. Stacked evidence panels. Full-width dialog sheets. |
| **Tablet** | `640px – 1023px` | Two-column adaptive grid. Collapsible navigation drawer. Split document view where practical. |
| **Desktop** | `1024px – 1279px` | Persistent desktop sidebar/header navigation. Full multi-column data tables. Simultaneous document and evidence panels. |
| **Wide Desktop** | `1280px+` | Expanded canvas up to 1440px max-width. Side-by-side cross-document comparison and deep topological graph views. |

---

## 3. Responsive Rules by Component & Screen

| Component / Route | Mobile (375px) | Tablet (768px) | Desktop (1024px+) |
| :--- | :--- | :--- | :--- |
| **AppShell Navigation** | Compact horizontal scroll tab bar (`overflow-x-auto`) | Collapsible grouped links | Full horizontal group tabs with role badges |
| **Dashboard (`/`)** | Single column stacked summary cards | 2-column grid | 3-to-4 column responsive grid |
| **Documents (`/documents`)** | Compact card list with status pills | Scrollable table with prioritized columns | Full multi-column inventory table with filter toolbar |
| **Document Detail (`/documents/[id]`)** | Stacked document metadata $\to$ chunks $\to$ facts | Split layout (chunks left, metadata right) | Multi-panel workspace with synchronized highlight pane |
| **Ask AEGIS (`/ask`)** | Question input stacked above response & evidence cards | 2-column split (query & answer top, evidence bottom) | Side-by-side workspace with synchronized source highlights |
| **Compare (`/compare`)** | Stacked document selection with document toggle tab | Split comparison panes with synchronous scroll lock | Full side-by-side comparison matrix with conflict highlight |
| **Review Queue (`/reviews`)** | Compact status cards with inline action buttons | Adaptive table | Full governance table with metrics summary header |
| **Dialogs (`<Dialog />`)** | Full-width bottom sheet or inset card ($92\text{vw}$) | Centered modal bounded at $512\text{px}$ (`max-w-lg`) | Centered modal bounded at $512\text{px}$ (`max-w-lg`) |

---

## 4. Viewport Verification & Zero-Overflow Contract

Every page template and component layout is automatedly tested via Playwright across three target viewports:
- Mobile: $375 \times 812\text{px}$ (iPhone mini/standard)
- Tablet: $768 \times 1024\text{px}$ (iPad portrait)
- Desktop: $1440 \times 900\text{px}$ (Standard workstation)

The test verifies:
$$\text{scrollWidth} \le \text{clientWidth}$$
Ensuring zero unintended horizontal scrollbars appear at the page level.
