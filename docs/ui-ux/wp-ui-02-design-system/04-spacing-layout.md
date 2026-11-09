# 04 — Spacing, Elevation & Layout System

**Document Identifier**: `AEGIS-DOCINTEL-DS-004`  
**Work Package**: `WP-UI-02: Design System`  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. 4px Base Spacing Scale

To eliminate arbitrary CSS pixel values and ensure predictable vertical and horizontal rhythm, AEGIS-DocIntel standardizes strictly on a **4px base grid**. Every padding, margin, gap, and dimension is an integer multiple of $4\text{px}$.

| Token | Rem Value | Pixel Value | Typical Application Context |
| :--- | :---: | :---: | :--- |
| `--space-1` | `0.25rem` | 4px | Icon-to-text gap, compact badge padding, table cell vertical micro-padding. |
| `--space-2` | `0.50rem` | 8px | Button inline gaps, input inner horizontal padding, chip margins. |
| `--space-3` | `0.75rem` | 12px | Form control padding, breadcrumb item separation. |
| `--space-4` | `1.00rem` | 16px | Standard component gap, alert box padding, card inner padding. |
| `--space-5` | `1.25rem` | 20px | Standard card padding (`p-5`), modal header separation. |
| `--space-6` | `1.50rem` | 24px | Large card padding, dashboard widget grid gap. |
| `--space-8` | `2.00rem` | 32px | Major section vertical separation, workspace panel margins. |
| `--space-10` | `2.50rem` | 40px | Hero banner padding, empty-state container padding. |
| `--space-12` | `3.00rem` | 48px | Page-level section dividers. |
| `--space-16` | `4.00rem` | 64px | Page header to main content separation. |

---

## 2. Geometry & Border Radius Tokens

Rounded geometry is restrained to maintain an enterprise, professional appearance:

| Token | Value | Pixel | Usage |
| :--- | :---: | :---: | :--- |
| `--radius-sm` | `0.25rem` | 4px | Checkbox corners, tooltip containers, inline code pills. |
| `--radius-md` | `0.50rem` | 8px | Standard buttons, text inputs, select dropdowns, alerts. |
| `--radius-lg` | `0.75rem` | 12px | Surface cards, dialog modal windows, evidence panels. |
| `--radius-xl` | `1.00rem` | 16px | Large dashboard summary widgets, preview sheets. |

---

## 3. Elevation & Depth Tokens

Depth in AEGIS is functional, not decorative. Elevation is used exclusively to lift interactive modals and elevated dropdowns above background content layers:

| Token | Value | Purpose |
| :--- | :--- | :--- |
| `--shadow-sm` | `0 1px 2px rgb(15 23 42 / 0.06)` | Base card resting elevation. |
| `--shadow-md` | `0 4px 12px rgb(15 23 42 / 0.08)` | Modal dialogs, floating tooltips, active dropdown menus. |

---

## 4. Layout Dimensions & Breakpoint Standards

```typescript
export const BREAKPOINTS = {
  mobile: 640,
  tablet: 768,
  desktop: 1024,
  wide: 1280,
} as const;
```

### Layout Constants
- **Header Height**: 64px (`--header-height: 4rem;`). Fixed sticky top with border separator.
- **Sidebar Width**: 256px (`--sidebar-width: 16rem;`). Persistent on desktop viewports ($\ge 1024\text{px}$), collapsible on tablet.
- **Main Content Max Width**: 1440px (`--content-max-width: 90rem;`). Constrains general workspace screens (`max-w-7xl` or `max-w-[90rem]`) while centering content horizontally.
