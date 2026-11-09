# 04 — Breadcrumbs Hierarchy

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03-04`  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: APPROVED ARCHITECTURE  

---

## 1. Overview & Purpose

Breadcrumbs provide secondary wayfinding directly above page titles. They expose the user's position within the route hierarchy and provide fast one-click navigation back to parent collections.

```
Workspace / Documents / Annual_Report_2026.pdf
```

---

## 2. Route Mapping Registry

Breadcrumbs are dynamically calculated from the URL pathname using `getBreadcrumbs(pathname)` in `web/src/lib/shell/breadcrumbs.ts`:

| Route Path | Breadcrumb Trail | Clickable Segments | Current Leaf |
| :--- | :--- | :--- | :--- |
| `/` | `Workspace` | None | `Workspace` |
| `/documents` | `Workspace > Documents` | `/` | `Documents` |
| `/documents/doc-123` | `Workspace > Documents > doc-123` | `/`, `/documents` | `doc-123` |
| `/ask` | `Workspace > Intelligence > Ask AEGIS` | `/`, `/ask` | `Ask AEGIS` |
| `/compare` | `Workspace > Intelligence > Compare` | `/`, `/compare` | `Compare` |
| `/reviews` | `Workspace > Governance > Review Queue` | `/`, `/reviews` | `Review Queue` |
| `/reviews/rev-456` | `Workspace > Governance > Review Queue > rev-456` | `/`, `/reviews` | `rev-456` |

---

## 3. Accessibility & DOM Structure

- **Landmark**: Semantic `<nav aria-label="Breadcrumb">`.
- **List Container**: `<ol className="flex items-center gap-1.5 text-xs text-[var(--muted)]">`.
- **Items**: `<li>` tags with `ChevronRight` decorative separators (`aria-hidden="true"`).
- **Active Segment**: The final item is rendered as `<span aria-current="page" className="font-medium text-[var(--foreground)]">` without an `href`.
- **Truncation**: Path labels longer than 32 characters are visually truncated with CSS `truncate` while preserving full text in `title` attribute.
