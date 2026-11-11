# WP-UI-09 — 10: Visual Regression Testing Architecture

**Work Package**: WP-UI-09 — Visual, Interaction & End-to-End Experience Validation  
**Document**: 10 — Visual Regression Suite, Baselines & Snapshot Policies  
**Status**: Approved & Baseline Verified  
**Execution File**: `web/tests/visual/visual-regression.spec.ts` (29 tests passing)  

---

## 1. Overview & Visual Regression Strategy

Visual regression testing prevents unintended visual side-effects, CSS regressions, and layout misalignments when modifying shared components, design tokens, or utility classes.

The suite utilizes Playwright's native screenshot engine with deterministic viewport configurations, font pre-loading, and dynamic content masking to guarantee zero false positives across development and CI environments.

---

## 2. Screenshot Test Specifications

| Test ID | Visual Target / Route | State Captured | Masked Elements | Status |
| :--- | :--- | :--- | :--- | :---: |
| **VIS-001** | Application Shell | Desktop Expanded (1366x768) | Timestamp, user email | **PASS** |
| **VIS-002** | Application Shell | Collapsed Mini Sidebar | Timestamp | **PASS** |
| **VIS-003** | `/` (Overview) | Default Populated Cards | Relative time strings | **PASS** |
| **VIS-004** | `/documents` | Document Library Table | Ingestion timestamp | **PASS** |
| **VIS-005** | `/documents` | Upload Modal Active | None | **PASS** |
| **VIS-006** | `/documents/[id]` | Document Inspector Split Pane | Document UUID | **PASS** |
| **VIS-007** | `/documents/[id]` | Chunk Metadata Flyout | None | **PASS** |
| **VIS-008** | `/ask` | Initial Question Ready State | Placeholder cursor | **PASS** |
| **VIS-009** | `/ask` | Grounded Answer with Badges | Processing duration | **PASS** |
| **VIS-010** | `/ask` | Citation Drawer Open | Source highlight | **PASS** |
| **VIS-011** | `/compare` | Document Selector Empty | None | **PASS** |
| **VIS-012** | `/compare` | Side-by-Side Diff View | Comparison latency | **PASS** |
| **VIS-013** | `/reviews` | Human Review Queue Populated | Item UUIDs | **PASS** |
| **VIS-014** | `/reviews` | Fact Verification Panel Open | None | **PASS** |
| **VIS-015** | `/reviews` | Conflict Resolution Panel | None | **PASS** |
| **VIS-016** | `/reviews` | Immutable Audit Timeline | Exact ISO dates | **PASS** |
| **VIS-017** | `/analytics` | System Analytics Dashboard | Dynamic counters | **PASS** |
| **VIS-018** | `/mathematics` | KaTeX Mathematical Viewer | None | **PASS** |
| **VIS-019** | `/mathematics` | Matrix Heat Map View | None | **PASS** |
| **VIS-020** | `/mathematics` | 3D Vector Embedding Projection| Rotation angle | **PASS** |
| **VIS-021** | `/pipelines` | Pipeline DAG Graph View | Node execution ms | **PASS** |
| **VIS-022** | `/pipelines` | Stage Details Log Drawer | Log timestamps | **PASS** |
| **VIS-023** | `/monitoring` | Operational Telemetry & Gauges | Real-time jitter | **PASS** |
| **VIS-024** | `/monitoring` | Service Health Indicator Grid | None | **PASS** |
| **VIS-025** | `/developer` | API Credential Manager | Redacted secrets | **PASS** |
| **VIS-026** | `/developer` | Webhook Configuration Form | None | **PASS** |
| **VIS-027** | Shell Skeleton | Initial Loading Skeleton State | CSS animation pulse | **PASS** |
| **VIS-028** | Mobile Drawer | Mobile Hamburger Open (390x844)| Battery/signal bar | **PASS** |
| **VIS-029** | Error Boundary | Uncaught Error Recovery View | Error stack trace | **PASS** |

---

## 3. Stability & Determinism Guidelines

To eliminate flaky test failures arising from rendering jitter, the visual suite enforces:
1. **Network Idle & Font Readiness**: Each test waits for `networkidle` and asserts `document.fonts.ready` before capturing screenshots.
2. **CSS Animation Disabling**: All CSS transitions and animations are disabled during snapshot capture via injected stylesheet:
   ```css
   *, *::before, *::after {
     transition: none !important;
     animation: none !important;
     caret-color: transparent !important;
   }
   ```
3. **Dynamic Element Masking**: Non-deterministic data elements (live ISO timestamps, random mock UUIDs, animated spinners) are passed to Playwright's `mask` option to prevent pixel mismatch.
4. **Tolerance Threshold**: Visual diffs permit a maximum pixel delta ratio of `maxDiffPixelRatio: 0.01` to account for subpixel font anti-aliasing differences across operating system graphics drivers.
