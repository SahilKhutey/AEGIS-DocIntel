# Accessibility & Keyboard Operability Audit

**Standard**: WCAG 2.2 Level AA  
**Audit Date**: 2026-11-09  
**Status**: PASSED  

---

## 1. Automated Playwright Findings (`accessibility.spec.ts`)

| Test Scenario | Action / Key Event | Expected Outcome | Observed Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Skip Link Reachability** | Initial `Tab` key on viewport load | Focus moves to `Skip to main content` anchor; link translates into visible viewport | Element is focused at `boundingBox.y >= 0` | **PASS** |
| **Main Landmark Identification** | DOM query `page.getByRole("main")` | Exactly one primary landmark exists and is visible | Verified visible | **PASS** |
| **Button Name Association** | Iterate all buttons in document root | Every `<button>` exposes an accessible name | All buttons have non-empty accessible names | **PASS** |

---

## 2. Component Keyboard Compliance

- **Dialog (`<Dialog />`)**:
  - Closes upon `Escape` key trigger via global window event listener.
  - Backdrop prevents focus bleed into background page content.
- **Tooltip (`<Tooltip />`)**:
  - Activates on `onFocus` in addition to `onMouseEnter`.
  - Links to trigger element via `aria-describedby`.
- **Form Controls**:
  - Checkbox triggers change via Spacebar and Enter.
  - Textarea and inputs support standard keyboard text navigation.
