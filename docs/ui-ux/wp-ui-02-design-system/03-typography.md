# 03 — Typography System

**Document Identifier**: `AEGIS-DOCINTEL-DS-003`  
**Work Package**: `WP-UI-02: Design System`  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. Typeface Roles & Mathematical Readability

The AEGIS-DocIntel typography stack is optimized for high-density document reading, structured tables, mathematical coordinate displays, and code citations.

### 1.1 Font Families

| Role | Font Stack | CSS Variable | Usage |
| :--- | :--- | :--- | :--- |
| **Primary Sans-Serif** | `Arial, Helvetica, sans-serif` | `--font-sans` | Body text, UI labels, buttons, navigation items, page titles, table content. |
| **Monospace / Code** | `"Cascadia Code", Consolas, monospace` | `--font-mono` | Document IDs, chunk IDs, coordinate bounding boxes, JSON payloads, formulas. |

---

## 2. Modular Type Scale

The modular scale ensures clear optical hierarchy while preventing layout shifts across viewports:

| Token | Rem Value | Pixel Equiv | Weight | Line Height | Usage Context |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `--text-xs` | `0.75rem` | 12px | Regular (400) / Medium (500) | `1.25` (`--leading-tight`) | Metadata labels, timestamps, confidence scores, pill badges. |
| `--text-sm` | `0.875rem` | 14px | Regular (400) / Medium (500) | `1.50` (`--leading-normal`) | Form field inputs, table cells, secondary descriptions, buttons. |
| `--text-base` | `1.00rem` | 16px | Regular (400) / Semi-bold (600) | `1.50` (`--leading-normal`) | Primary body copy, document excerpts, card titles. |
| `--text-lg` | `1.125rem` | 18px | Semi-bold (600) | `1.50` (`--leading-normal`) | Modal headers, sub-section headings (H4). |
| `--text-xl` | `1.25rem` | 20px | Semi-bold (600) | `1.25` (`--leading-tight`) | Section headings (H3), drawer titles. |
| `--text-2xl` | `1.50rem` | 24px | Semi-bold (600) | `1.25` (`--leading-tight`) | Panel headings (H2), major workspace titles. |
| `--text-3xl` | `1.875rem` | 30px | Bold (700) | `1.25` (`--leading-tight`) | Top-level page titles (H1). |

---

## 3. Line Height Standards

1. `--leading-tight` (`1.25`): Reserved for headings (`h1` through `h6`) and compact table headers to preserve tight vertical rhythm.
2. `--leading-normal` (`1.50`): Default body text, form field labels, and button labels.
3. `--leading-relaxed` (`1.65`): Long-form extracted document quotes and evidence explanations.

---

## 4. Heading Hierarchy Rules

- Every page must contain exactly one `<h1>` landmark inside `<main id="main-content">`.
- Heading ranks must never be skipped (e.g., an `<h3>` must never directly follow an `<h1>` without an intervening `<h2>`).
- All headings must have optical letter-spacing set to `-0.02em` for improved reading density.
