# 15 — Acceptance Criteria & Release Gates

## 1. Acceptance Criteria Checklist

### Capability 01: Ask AEGIS (`/ask`)
- [x] Natural-language question composer submits to `/api/v1/ask` or `/v1/query`.
- [x] Document scope filter restricts query or searches all authorized documents.
- [x] Displays grounded answers with inline numbered citations (`[1]`, `[2]`).
- [x] Clicking citation highlights entry in `EvidencePanel` and links to source document.
- [x] Displays "Safe Abstention: Insufficient Evidence" when confidence threshold is not met.
- [x] Displays citation integrity warning if claims reference missing citations.
- [x] Retains backward compatibility with `workbench.spec.ts:403`.

### Capability 02: Retrieval Interface (`/intelligence/retrieval`)
- [x] Search input accepts query with validation (prevents empty submit).
- [x] Document scope selector allows single or multi-document retrieval.
- [x] Renders ranked passage cards with score and ranking metadata.
- [x] Provides direct handoff to Evidence Explorer.
- [x] Graceful empty and error states with retry capability.

### Capability 03: Evidence Explorer (`/intelligence/evidence`)
- [x] Displays verbatim passages with chunk ID, page number, and section path.
- [x] Deep linking via query parameters (`?document_id=...&passage_id=...`).
- [x] Provides "Open source document" routing to `/documents/[id]`.
- [x] Citation integrity utilities identify unreferenced and broken citations.

### Capability 04: Knowledge Visualization (`/intelligence/knowledge`)
- [x] SVG canvas displays entity and relationship nodes and directed edges.
- [x] Node selection displays detailed metadata and connected edges in sidebar.
- [x] Node type filtering (all, entity, document, concept).
- [x] Zoom in, zoom out, reset view controls.
- [x] Accessible structured table view alternative conforming to WCAG 2.2 AA.

### Capability 05: Comparison Interface (`/compare`)
- [x] Document selector matrix enforces minimum of 2 documents before comparing.
- [x] Mode selector toggles structured, semantic, and content modes.
- [x] Summarizes differences and categorized discrepancy cards.
- [x] Retains detailed alignment table and conflict flags with links to `/reviews`.
- [x] Retains backward compatibility with `workbench.spec.ts:421`.

### Capability 06: Intelligence Hub (`/intelligence`)
- [x] Operational overview cards displaying document readiness and integrity status.
- [x] Quick navigation cards into all 5 capabilities.

## 2. Release Gates

| Release Gate | Required Threshold | Observed Result | Status |
|---|---|---|---|
| TypeScript Compilation | 0 errors | 0 errors (`tsc --noEmit`) | PASS |
| Code Linting | 0 warnings, 0 errors | 0 warnings, 0 errors (`eslint`) | PASS |
| Unit Test Suite | 100% passing | 118 / 118 tests passed (22 suites) | PASS |
| End-to-End Suite | 100% passing | 53 / 53 tests passed (19 suites) | PASS |
| Zero Regressions | Legacy E2E tests pass | `workbench.spec.ts` 100% passed | PASS |
| Next.js Production Build | Successful build, 15 routes | All 15 routes optimized | PASS |
| Final Recommendation | Unanimous GO | **GO** | **APPROVED** |
