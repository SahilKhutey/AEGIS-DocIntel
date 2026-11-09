# 05 — Shared Component Library Specification

**Document Identifier**: `AEGIS-DOCINTEL-DS-005`  
**Work Package**: `WP-UI-02: Design System`  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. Component Architecture & Principles

The AEGIS component library (`web/src/components/ui/`) is a collection of accessible, composable UI primitives.

All primitives adhere to these core rules:
1. **Zero External Runtime Heavyweight Dependencies**: Implemented natively on top of React 19 and standard Web APIs.
2. **Accessible by Default**: Every component exposes appropriate ARIA roles, states, and keyboard event handlers.
3. **Deterministic Token Styling**: Stylings utilize semantic tokens (`var(--surface)`, `var(--primary)`, `var(--border)`).
4. **Independent Unit Test Coverage**: Every component is tested for contract compliance under `web/tests/unit/`.

---

## 2. Component Register & Specifications

### 2.1 Button (`web/src/components/ui/button.tsx`)

#### Purpose
Primary action trigger used across all AEGIS screens for submitting forms, opening dialogs, and confirming actions.

#### Variants
- `primary`: Solid blue (`var(--primary)`). High-priority primary actions (e.g., "Ask Question", "Approve Fact").
- `secondary`: Subtle surface (`var(--surface-muted)`). Secondary actions (e.g., "Cancel", "Reset Filters").
- `outline`: Border outline on transparent background. Alternative secondary actions.
- `ghost`: Transparent background, hover highlight. Auxiliary utility triggers (e.g., modal close buttons).
- `danger`: Solid crimson (`var(--danger)`). Irreversible actions (e.g., "Reject Fact", "Delete Document").

#### Sizes
- `sm`: `min-h-9 px-3 text-sm` — Compact table row actions and header buttons.
- `md`: `min-h-10 px-4 text-sm` — Standard form buttons and modal footers.
- `lg`: `min-h-12 px-6 text-base` — Prominent call-to-action triggers on dashboards.

#### States
- `Default`, `Hover`, `Focus-visible` (3px ring), `Active`, `Disabled` (`disabled:opacity-50 disabled:cursor-not-allowed`).
- `Loading`: Displays `"Loading…"` text, sets `disabled={true}`, and applies `aria-busy="true"`.

---

### 2.2 Badge (`web/src/components/ui/badge.tsx`)

#### Purpose
Compact visual indicators for categorizing documents, entities, chunk types, and workflow status.

#### Variants
- `default`: Neutral slate (`bg-[var(--surface-muted)] text-[var(--foreground)]`).
- `success`: Emerald tint (`bg-green-100 text-green-900`). Verified citations, indexed status.
- `warning`: Amber tint (`bg-amber-100 text-amber-950`). Pending reviews, extraction warnings.
- `danger`: Red tint (`bg-red-100 text-red-900`). Extraction failures, rejected items.
- `info`: Sky tint (`bg-sky-100 text-sky-950`). Informational metadata, section headers.

---

### 2.3 Card (`web/src/components/ui/card.tsx`)

#### Purpose
Standard surface container grouping related document metadata, query answers, and comparison panels.

#### Variants
- `default`: Bordered card (`bg-[var(--surface)] border border-[var(--border)] rounded-lg shadow-sm`).
- `interactive`: Hover elevation with cursor pointer for clickable dashboard summaries.
- `selected`: Highlighted border with primary ring (`border-[var(--primary)] ring-2`).

---

### 2.4 Form Controls (`input.tsx`, `textarea.tsx`, `select.tsx`, `checkbox.tsx`)

#### Purpose
Accessible form controls for querying documents, editing metadata, filtering review queues, and selecting documents.

#### States & Accessibility
- `aria-invalid`: Form controls set `aria-invalid="true"` when validation fails and highlight borders with `var(--danger)`.
- `disabled`: Controls set `disabled={true}`, apply `disabled:opacity-50`, and prevent keyboard input.
- `Checkbox`: Automatically pairs with `<label htmlFor={inputId}>` for accessible click targeting.

---

### 2.5 Dialog (`web/src/components/ui/dialog.tsx`)

#### Purpose
Accessible modal dialog for critical confirmations (e.g., document upload, review rejection, destructive actions).

#### Features & Accessibility
- Focus management: Traps focus within modal while open.
- Keyboard dismissal: Listens for `Escape` key to trigger `onClose`.
- Semantics: Renders with `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and `aria-describedby`.
- Backdrop: Clicking the translucent backdrop triggers `onClose`.

---

### 2.6 Tooltip (`web/src/components/ui/tooltip.tsx`)

#### Purpose
Contextual micro-explanations for dense mathematical terms, confidence formulas, or truncated text.

#### Features & Accessibility
- Dual activation: Appears on mouse hover (`onMouseEnter`) and keyboard focus (`onFocus`).
- Semantics: Renders with `role="tooltip"` and links to trigger element via `aria-describedby`.

---

### 2.7 Table (`web/src/components/ui/table.tsx`)

#### Purpose
High-density structured data presentation for document inventories, extracted facts, and governance queues.

#### Sub-components
- `<Table>`: Outer responsive scroll container (`overflow-x-auto`) and `<table>` element.
- `<TableHeader>`: Standard uppercase muted header section with bottom border.
- `<TableBody>`: Alternating row separator body section.
- `<TableRow>`: Hover-highlighted table row (`hover:bg-[var(--surface-muted)]/50`).
- `<TableHead>`: Column header cell (`<th scope="col">`).
- `<TableCell>`: Data cell (`<td>`).
- `<TableCaption>`: Accessible table caption (`<caption>`).

---

### 2.8 Skeleton (`web/src/components/ui/skeleton.tsx`)

#### Purpose
Loading state placeholders preventing layout shift while fetching documents or query answers.

#### Variants
- `text`: Single line text placeholder.
- `card`: Card-sized container placeholder.
- `table`: Table row height placeholder.
- `circular`: Avatar / badge placeholder.
- Attributes: Always applies `aria-busy="true"` and `aria-hidden="true"`.

---

### 2.9 Alert (`web/src/components/ui/alert.tsx`)

#### Purpose
Contextual feedback banners communicating system errors, indexing completions, or queue updates.

#### Semantics
- Variants `danger` and `warning` render with `role="alert"`.
- Variants `info` and `success` render with `role="status"`.
- Each alert pairs iconography (`ℹ️`, `✓`, `⚠`, `⨂`) with bold title text to prevent color-only communication.
