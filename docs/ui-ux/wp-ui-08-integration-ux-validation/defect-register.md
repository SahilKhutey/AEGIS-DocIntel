# WP-UI-08: Defect & Remediation Register

This register details all anomalies encountered during the integration and UX validation phase of WP-UI-08, their root cause analysis, and their verified remediations.

| Defect ID | Severity | Capability / Component | Symptom & Root Cause | Resolution & Verification |
| :--- | :--- | :--- | :--- | :--- |
| **DEF-001** | Medium | Accessibility (`app-sidebar.tsx`) | `aria-label="AEGIS home"` failed WCAG 2.5.3 (Label in Name) because visible brand text was `"AEGIS DocIntel"`. | Removed artificial `aria-label` override; accessible name now naturally derives from text. Verified via axe-core. |
| **DEF-002** | Medium | Accessibility (`ProvenanceViewer.tsx`) | `<span>` placed directly under `<div>` in `<dl>` violated W3C definition list hierarchy. | Encapsulated all secondary descriptions directly within `<dd>` elements. Verified via axe-core. |
| **DEF-003** | Low | Accessibility (Global CSS & Inputs) | Compact inputs and buttons in analytics and mathematics fell below 24x24px target size minimum (SC 2.5.8). | Enforced `min-height: 28px; min-width: 28px;` globally and in `TimeRangeSelector`. Verified via axe-core. |
| **DEF-004** | Medium | Accessibility (`global-search.tsx`) | `aria-expanded` on textbox triggered `aria-allowed-attr` violation. | Added `role="combobox"` and `aria-autocomplete="list"` to provide full combobox semantics. Verified via axe-core. |
| **DEF-005** | High | Layout / Responsive (Mobile 320px) | `scrollWidth` exceeded `innerWidth` on narrow mobile viewports due to unconstrained table wrappers. | Added `overflow-x: hidden; max-width: 100%;` to `html, body` and `overflow-x-hidden` on `AppShell`. Verified via Playwright. |
| **DEF-006** | Medium | Test Architecture (`e2e-user-journeys.spec.ts`) | Heading locator matched both sidebar navigation heading and page main heading in strict mode. | Specified exact hierarchy: `page.locator("main").getByRole("heading", { name: "Documents", level: 1 })`. |
| **DEF-007** | High | Test Architecture (`e2e-user-journeys.spec.ts`) | Browser fetches from port 3000 to port 8000 triggered preflight `OPTIONS` requests that failed CORS without explicit mock headers. | Implemented `handleCorsMock()` responding with 204 status and CORS headers (`Access-Control-Allow-Origin: *`). |
| **DEF-008** | Low | Unit Testing (`components.test.tsx`) | `SessionExpired` failed with `invariant expected app router to be mounted` in headless jsdom environment. | Added `vi.mock("next/navigation")` at top of test suite. Verified via Vitest. |
