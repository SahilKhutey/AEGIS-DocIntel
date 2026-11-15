# WP-UI-09 — 13: Defect Remediation Register

**Work Package**: WP-UI-09 — Visual, Interaction & End-to-End Experience Validation  
**Document**: 13 — Defect Identification, Root Cause Analysis & Remediation Log  
**Status**: All Identified Defects Remediated & Verified  

---

## 1. Defect Classification & Severity Criteria

Defects uncovered during the WP-UI-09 validation suite were triaged according to standard engineering severity definitions:
- **P0 (Blocker)**: System crash, security bypass, or total block of core workflow with no workaround.
- **P1 (Critical)**: Major functional break, API preflight rejection, or severe accessibility barrier.
- **P2 (Major)**: Non-blocking usability defect, focus trap failure, or WCAG AA contrast non-conformance.
- **P3 (Minor)**: Cosmetic imperfection, minor timing sensitivity, or test selector drift.

---

## 2. Remediated Defect Ledger

| Defect ID | Severity | Component / Area | Description & Symptom | Root Cause | Remediation & Fix | Verification Status |
| :--- | :---: | :--- | :--- | :--- | :--- | :---: |
| **DEF-001** | **P1** | Next.js Turbopack | HMR WebSocket handshake failed on `127.0.0.1:3000` | Next.js 16 requires explicit origin whitelisting in dev mode | Added `allowedDevOrigins: ["127.0.0.1", "localhost"]` in `web/next.config.ts` | **VERIFIED (CLOSED)** |
| **DEF-002** | **P1** | FastAPI CORS | Cross-origin preflight `OPTIONS` requests failed on API calls | `cors_origins` in `src/core/settings.py` omitted `http://127.0.0.1:3000` | Added `"http://127.0.0.1:3000"` to default `cors_origins` list | **VERIFIED (CLOSED)** |
| **DEF-003** | **P2** | `UploadDialog` | Dialog did not trap focus or close on `Escape` key | Dialog lacked keyboard event listener and initial focus call | Added `keydown` listener, focus first child, and `aria-modal="true"` | **VERIFIED (CLOSED)** |
| **DEF-004** | **P2** | `ShellSkeleton` | Axe audit failed with `aria-prohibited-attr` rule | `aria-label` and `aria-busy` used on generic `div` without role | Assigned semantic `role="status"` to the wrapper `div` | **VERIFIED (CLOSED)** |
| **DEF-005** | **P2** | Operational / Math UI | Text color contrast fell below 4.5:1 on white card backgrounds | `text-slate-400` has ~2.5:1 ratio against `#ffffff` | Replaced with `text-slate-600` (`#475569`, ratio 5.9:1) | **VERIFIED (CLOSED)** |
| **DEF-006** | **P2** | `MatrixViewer` | Heatmap cell labels low contrast against light cell fills | Cell color ramp utilized light blue shades with light text | Updated cell background scales and dark text on light fills | **VERIFIED (CLOSED)** |
| **DEF-007** | **P3** | Test Suite Selector | `WF-DOC-011` failed finding unsupported file alert | Selector searched for outdated regex pattern | Updated regex in test to match active component copy (`not supported\|Failed`) | **VERIFIED (CLOSED)** |

---

## 3. Detailed Root Cause Analysis & Fix Records

### DEF-001: Next.js Turbopack Dev Origin Security
- **Symptom**: Console logged: `WebSocket connection to 'ws://127.0.0.1:3000/_next/hmr' failed: net::ERR_INVALID_HTTP_RESPONSE`. Next.js output: `Blocked cross-origin request to Next.js dev resource /_next/hmr from "127.0.0.1"`.
- **Root Cause**: Next.js 16.4 introduces origin validation for HMR dev resources. By default, only `localhost` is allowed unless configured.
- **Code Change**:
  ```typescript
  // web/next.config.ts
  const nextConfig: NextConfig = {
    reactStrictMode: true,
    allowedDevOrigins: ["127.0.0.1", "localhost"],
  };
  ```

### DEF-002: Backend FastAPI CORS Preflight Rejection
- **Symptom**: Browser requests from `http://127.0.0.1:3000` to `http://127.0.0.1:8000/api/v1/documents` aborted with CORS failure: `No 'Access-Control-Allow-Origin' header is present on the requested resource`.
- **Root Cause**: The FastAPI CORS middleware reads from `settings.cors_origins`, which only included `http://localhost:3000` by default.
- **Code Change**:
  ```python
  # src/core/settings.py
  cors_origins: list[str] = [
      "http://localhost:3000",
      "http://127.0.0.1:3000",
      "http://localhost:8000",
  ]
  ```

### DEF-003: Upload Dialog Focus Trap & Escape Dismissal
- **Symptom**: When `UploadDialog` opened, keyboard users pressing `Tab` continued tabbing through links behind the dialog backdrop, and pressing `Escape` did nothing.
- **Code Change**: Added `dialogRef` focusing the first button on mount, global `keydown` listener checking `e.key === "Escape"` to invoke `onClose()`, and `aria-modal="true"`.

### DEF-004: Axe ARIA Prohibited Attribute Violation
- **Symptom**: `@axe-core/playwright` flagged `aria-prohibited-attr` on `web/src/components/shell/shell-skeleton.tsx`.
- **Root Cause**: According to ARIA 1.2 specifications, generic `div` elements cannot carry naming attributes like `aria-label` without a supporting landmark or widget role.
- **Code Change**: Added `role="status"` to the container `div`.
