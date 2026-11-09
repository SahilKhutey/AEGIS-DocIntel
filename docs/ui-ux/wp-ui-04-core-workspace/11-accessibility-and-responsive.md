# 11 — Accessibility & Responsive Design

## 1. WCAG 2.2 Level AA Compliance

All Core Workspace components and pages have been designed and validated to meet the Web Content Accessibility Guidelines (WCAG) 2.2 Level AA standards.

---

## 2. ARIA Semantics and Landmark Tree

```
<main id="main-content">
  ├── <section aria-label="Workspace metrics">
  ├── <section aria-label="Items requiring attention">
  ├── <section aria-label="Recent activity">
  │     ├── <h2 ...>Recent Documents</h2>
  │     └── <h2 ...>Processing Summary</h2>
  ├── <section aria-label="Workbench capabilities">
  │
  ├── Document Library (/documents)
  │     ├── <h1 ...>Documents</h1>
  │     ├── <h2 ...>Document Workspace & Library</h2>
  │     ├── <div role="group" aria-label="Document status filters">
  │     │     └── <button aria-pressed="true|false">
  │     └── <table aria-label="Documents list">
  │           └── <th scope="col">
  │
  ├── Document Inspection (/documents/:id)
  │     ├── <h1 ...>Document Title</h1>
  │     ├── <div role="tablist" aria-label="Document inspection sections">
  │     │     └── <button role="tab" aria-selected="true|false" aria-controls="panel-...">
  │     └── <div role="tabpanel" id="panel-..." aria-labelledby="tab-...">
  │
  └── Processing Monitor (/processing)
        ├── <h1 ...>Processing Monitor</h1>
        ├── <div role="group" aria-label="Processing job status filters">
        ├── <table aria-label="Processing jobs list">
        └── <ol role="list" aria-label="Processing stages">
              └── <li aria-current="step"> (Active stage)
```

---

## 3. Keyboard Navigation & Focus Management

1. **Modal Dialog Focus Trap**:
   - Opening the `UploadDialog` shifts focus into the modal.
   - Pressing `Escape` closes the modal and returns focus to the trigger button.
2. **Tabbed Navigation**:
   - Arrow keys (`ArrowLeft`, `ArrowRight`) navigate between tabs in `DocumentInspector`.
   - Pressing `Tab` moves focus directly from the active tab into the active `tabpanel`.
3. **Skip-to-Content**:
   - The global skip-link (`.skip-link`) allows keyboard users to bypass header and sidebar landmarks and land directly on `#main-content`.

---

## 4. Responsive Breakpoint Matrix

| Breakpoint | Viewport Width | Layout Adaptations |
| :--- | :--- | :--- |
| **Mobile (`sm`)** | `< 640px` | - Single-column metrics stack<br>- Collapsible mobile navigation drawer<br>- Horizontal overflow scroll containers for wide tables<br>- Fullscreen modal dialogs |
| **Tablet (`md`)** | `640px – 1024px` | - Two/Three-column metrics grid<br>- Compact table columns (prioritizing Name, Status, Actions)<br>- Side-by-side activity cards |
| **Desktop (`lg` / `xl`)**| `1024px – 1440px`| - Persistent sidebar navigation<br>- Five-column operational metrics grid<br>- Full table view with pagination<br>- Two-column activity breakdown |
| **Ultra-Wide (`2xl`)** | `> 1440px` | - Centered maximum container constraint (`max-w-7xl`) preventing text line length fatigue |
