# 02 — Semantic Color Architecture & Themes

**Document Identifier**: `AEGIS-DOCINTEL-DS-002`  
**Work Package**: `WP-UI-02: Design System`  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. Palette Philosophy & Semantic Separation

AEGIS-DocIntel enforces strict semantic tokenization. Component styles do not reference hardcoded hex strings (e.g., `#2563EB`) or raw palette constants. Instead, components reference functional CSS custom properties (e.g., `var(--primary)`).

This architecture provides two critical guarantees:
1. **Theme Agnosticism**: Seamless support for both light and dark display modes without altering component class lists.
2. **Deterministic Contrast**: Guaranteed compliance with WCAG 2.2 Level AA contrast requirements across foreground/background pairs.

---

## 2. Core Palette

The AEGIS palette provides high-assurance differentiation across operational states:

| Swatch Name | Hex Code | Purpose & Semantic Role |
| :--- | :---: | :--- |
| **Navy** | `#111827` | Primary dark text, deep chrome headers, heavy borders in dark theme. |
| **Blue** | `#2563EB` | Primary brand color, interactive buttons, focused states, primary links. |
| **Teal** | `#0F766E` | Grounded mathematical evidence, geometry citations, topological alignment. |
| **Amber** | `#B45309` | Processing queue warnings, pending governance actions, review attention. |
| **Green** | `#15803D` | Successful indexing, verified citations, approved governance decisions. |
| **Red** | `#B91C1C` | Extraction errors, schema failures, rejected governance items, delete actions. |
| **Surface Muted** | `#F1F5F9` | Secondary cards, subtle table row alternations, inactive tab pills. |
| **Background** | `#F8FAFC` | Global viewport canvas background. |
| **Surface White** | `#FFFFFF` | Primary card, modal dialog, and input background. |

---

## 3. Semantic Token Register

### 3.1 Light Theme (`:root`)

```css
:root {
  color-scheme: light;

  /* Surfaces & Structural Canvas */
  --background: #f8fafc;
  --surface: #ffffff;
  --surface-muted: #f1f5f9;
  --foreground: #111827;
  --muted: #64748b;
  --border: #e2e8f0;

  /* Primary Interactive Brand */
  --primary: #2563eb;
  --primary-hover: #1d4ed8;
  --primary-foreground: #ffffff;

  /* Feedback & Operational States */
  --success: #15803d;
  --warning: #b45309;
  --danger: #b91c1c;
  --info: #0369a1;
}
```

### 3.2 Dark Theme (`[data-theme="dark"]`)

```css
[data-theme="dark"] {
  color-scheme: dark;

  /* Surfaces & Structural Canvas */
  --background: #0b1220;
  --surface: #111827;
  --surface-muted: #1e293b;
  --foreground: #f8fafc;
  --muted: #a1a1aa;
  --border: #334155;

  /* Primary Interactive Brand */
  --primary: #60a5fa;
  --primary-hover: #93c5fd;
  --primary-foreground: #0b1220;

  /* Feedback & Operational States */
  --success: #4ade80;
  --warning: #fbbf24;
  --danger: #f87171;
  --info: #38bdf8;
}
```

---

## 4. Contrast Verification Matrix (WCAG 2.2 AA)

To satisfy WCAG 2.2 AA, normal text ($<18\text{pt}$ or $<14\text{pt}$ bold) requires a contrast ratio of at least $4.5:1$, while large text requires at least $3.0:1$. Interactive UI boundaries and non-text indicators require at least $3.0:1$.

| Token Pair | Foreground | Background | Computed Ratio | Target | Compliance |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Normal Body Text | `--foreground` (`#111827`) | `--surface` (`#ffffff`) | **16.1 : 1** | $\ge 4.5:1$ | **PASS** |
| Muted Secondary Text | `--muted` (`#64748b`) | `--surface` (`#ffffff`) | **4.6 : 1** | $\ge 4.5:1$ | **PASS** |
| Primary Button Text | `--primary-foreground` (`#ffffff`) | `--primary` (`#2563eb`) | **4.6 : 1** | $\ge 4.5:1$ | **PASS** |
| Dark Mode Body Text | `--foreground` (`#f8fafc`) | `--surface` (`#111827`) | **15.2 : 1** | $\ge 4.5:1$ | **PASS** |
| Dark Mode Muted Text | `--muted` (`#a1a1aa`) | `--surface` (`#111827`) | **5.4 : 1** | $\ge 4.5:1$ | **PASS** |
| Dark Mode Primary Button | `--primary-foreground` (`#0b1220`) | `--primary` (`#60a5fa`) | **7.5 : 1** | $\ge 4.5:1$ | **PASS** |
| Success Badge Text | `#15803d` | `#dcfce7` (green-100) | **5.2 : 1** | $\ge 4.5:1$ | **PASS** |
| Danger Badge Text | `#b91c1c` | `#fee2e2` (red-100) | **5.8 : 1** | $\ge 4.5:1$ | **PASS** |
| Focus Ring Indicator | `--primary` (`#2563eb`) | `--background` (`#f8fafc`) | **4.7 : 1** | $\ge 3.0:1$ | **PASS** |

---

## 5. Non-Color Status Communication Rules

1. Every status badge contains a colored dot indicator *and* a capitalized textual label (e.g., `Approved`, `In Review`, `Conflict Detected`).
2. Danger alerts display warning iconography (`⨂`) alongside the textual heading and explanation.
3. Form validation errors highlight input borders with `var(--danger)` *and* set programmatic `aria-invalid="true"`.
