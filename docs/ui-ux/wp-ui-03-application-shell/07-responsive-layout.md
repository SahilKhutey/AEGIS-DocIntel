# 07 — Responsive Shell Standards

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03-07`  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: APPROVED ARCHITECTURE  

---

## 1. Breakpoint Architecture & Behavioral Matrix

The shell responds dynamically to screen geometry across four primary viewport tiers:

| Breakpoint Tier | Viewport Width | Sidebar Display | Header Layout | Quick Navigation |
| :--- | :--- | :--- | :--- | :--- |
| **Mobile** | $320\text{px} - 767\text{px}$ | Collapsed in slide-out modal drawer (`MobileNavigation`) | Hamburger trigger, compact selector, icon buttons | Horizontal scroll quick nav bar (`<nav aria-label="Mobile navigation">`) |
| **Tablet** | $768\text{px} - 1023\text{px}$ | Collapsed in slide-out modal drawer | Hamburger trigger, full workspace name, global search bar | Horizontal scroll quick nav bar |
| **Desktop** | $1024\text{px} - 1439\text{px}$ | Persistent expanded sidebar ($256\text{px}$ width) | Full operational header, hamburger hidden | Hidden (replaced by desktop sidebar) |
| **Wide** | $\ge 1440\text{px}$ | Persistent expanded sidebar | Full operational header, centered content container ($1440\text{px}$ max) | Hidden |

---

## 2. Mobile Drawer Standards (`MobileNavigation`)

- **ARIA Semantics**:
  - Modal container: `role="dialog"`, `aria-modal="true"`, `aria-label="Mobile navigation"`.
- **Focus Management & Body Lock**:
  - Upon opening, body scroll is locked via `document.body.style.overflow = "hidden"`.
  - Upon closing, body scroll is restored.
  - Pressing <kbd>Escape</kbd> closes the drawer immediately.
  - Backdrop click closes the drawer immediately.
- **Close Button**:
  - Accessible button with `aria-label="Close navigation"`.

---

## 3. Horizontal Overflow Audit

To prevent layout breakages on mobile and tablet screens:
1. `document.documentElement.scrollWidth <= window.innerWidth` across all breakpoints.
2. Quick mobile navigation uses `overflow-x: auto` with `whitespace-nowrap`.
3. Table and chart wrappers inside `<main>` use explicit container boundaries.
