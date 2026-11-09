# 10 — Accessibility Standards (WCAG 2.2 AA)

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03-10`  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: APPROVED ARCHITECTURE  

---

## 1. Compliance Baseline & Scope

The AEGIS Application Shell implements WCAG 2.2 Level AA accessibility compliance across keyboard navigation, landmark structure, focus management, and screen reader announcements.

---

## 2. Landmark Structure & Strict Hierarchy

The shell defines clear, unambiguous ARIA landmarks:

| Landmark | HTML Element | ARIA Attributes | Purpose |
| :--- | :--- | :--- | :--- |
| **Skip Link** | `<a>` | `href="#main-content"`, `class="skip-link"` | Allows keyboard users to bypass navigation. Must be first focusable element. |
| **Primary Navigation**| `<nav>` inside `<aside>`| `aria-label="Primary navigation"` | Contains workflow groupings and operational navigation links. |
| **Mobile Navigation** | `<nav>` | `aria-label="Mobile navigation"` | Horizontal quick navigation bar on mobile/tablet. |
| **Mobile Drawer** | `<div>` modal | `role="dialog"`, `aria-modal="true"`, `aria-label="Mobile navigation"` | Full drawer for mobile screens. |
| **Breadcrumb** | `<nav>` | `aria-label="Breadcrumb"` | Route hierarchy tracking. |
| **Main Content** | `<main>` | `id="main-content"`, `tabindex="-1"` | Single main content container on the page. |

---

## 3. Keyboard Interaction Contracts

| Key | Context | Behavior |
| :--- | :--- | :--- |
| <kbd>Tab</kbd> | Document initial load | Focuses `.skip-link` immediately without skipping. |
| <kbd>Enter</kbd> / <kbd>Space</kbd> | On skip link | Scrolls directly to and focuses `<main id="main-content">`. |
| <kbd>Escape</kbd> | Workspace selector listbox | Closes listbox and refocuses selector trigger button. |
| <kbd>Escape</kbd> | Notification center flyout | Closes flyout and refocuses notification bell button. |
| <kbd>Escape</kbd> | User menu flyout | Closes flyout and refocuses avatar trigger button. |
| <kbd>Escape</kbd> | Mobile navigation drawer | Closes modal drawer, unlocks body scroll, and refocuses hamburger button. |

---

## 4. Visual Focus & Color Standards

1. **Focus Ring**: Uniform 3px focus ring using `var(--primary)` with 2px offset (`:focus-visible { outline: 3px solid var(--primary); outline-offset: 2px; }`).
2. **Contrast**: All text items (navigation links, breadcrumb labels, badge counts) exceed a 4.5:1 contrast ratio against their respective surfaces.
3. **No Color Alone**: Unread notifications, active routes, and planned indicators use text labels, icon badges, and geometric states in addition to color changes.
