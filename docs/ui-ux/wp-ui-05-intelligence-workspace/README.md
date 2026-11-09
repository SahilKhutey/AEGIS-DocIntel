# WP-UI-05 — Intelligence Workspace

## Objective
Deliver an integrated intelligence workspace for grounded question answering, document retrieval, evidence inspection, knowledge visualization, and cross-document comparison within AEGIS-DocIntel.

## Scope
1. **Ask AEGIS (`/ask`)**: Natural-language question answering across authorized documents with strictly grounded citations, claim-to-citation mapping, safe abstention, and conversation context.
2. **Retrieval Interface (`/intelligence/retrieval`)**: Passage retrieval and search interface, exposing hybrid BM25 and vector relevance scores, ranking metadata, and source navigation.
3. **Evidence Explorer (`/intelligence/evidence`)**: Verbatim passage inspection, page and coordinate references, ground truth provenance, and citation integrity validation.
4. **Knowledge Visualization (`/intelligence/knowledge`)**: Entity-relationship graph visualization of extracted concepts, facts, and document connections, paired with an accessible table alternative (WCAG 2.2 AA).
5. **Comparison Interface (`/compare`)**: Multi-document comparison workspace supporting structured fact alignment, conflict detection, and direct handoff to human governance review.
6. **Central Intelligence Hub (`/intelligence`)**: Central operational overview connecting all intelligence capabilities and displaying workspace grounding readiness.

## Dependencies
- **WP-UI-01: Product UX Architecture**: Personas, route register, access matrix, and user workflows.
- **WP-UI-02: Design System**: Design tokens, typography, colors, and reusable UI components (`Button`, `Input`, `StatusBadge`, `ErrorState`, `EmptyState`).
- **WP-UI-03: Application Shell**: Primary navigation, workspace selector, header, notifications, and responsive containers.
- **WP-UI-04: Core Workspace**: Document library, upload pipeline, document inspector, and processing monitor.
- **FastAPI Backend Contracts**: `/v1/query`, `/v1/answers`, `/v1/documents/{id}/chunks`, `/v1/documents/{id}/facts`, `/v1/intelligence/compare`, and `/v1/intelligence/conflicts`.

## Implementation Principles
- **Strict Grounding & Provenance**: Every generated answer and extracted finding must map to verifiable source documents. Never present an AI statement as "verified" without human governance confirmation.
- **Zero Fictional APIs**: All interactions map directly to verified FastAPI backend contracts or explicitly surface unavailable state with documented backend dependencies.
- **Integrity Validation**: Detect broken or dangling citation references client-side and display transparent warnings.
- **Universal Accessibility**: Support keyboard navigation, high-contrast states, and provide an accessible structured tabular fallback for visual graph representations (WCAG 2.2 AA).
- **Tenant Boundary Preservation**: All queries and retrieval requests are scoped to the authenticated tenant and authorized workspace.

## Documentation Index
1. [01-intelligence-workspace-overview.md](01-intelligence-workspace-overview.md)
2. [02-information-architecture.md](02-information-architecture.md)
3. [03-ask-aegis.md](03-ask-aegis.md)
4. [04-retrieval-interface.md](04-retrieval-interface.md)
5. [05-evidence-explorer.md](05-evidence-explorer.md)
6. [06-knowledge-visualization.md](06-knowledge-visualization.md)
7. [07-comparison-interface.md](07-comparison-interface.md)
8. [08-data-contracts-and-schemas.md](08-data-contracts-and-schemas.md)
9. [09-api-contract-mapping.md](09-api-contract-mapping.md)
10. [10-state-management-and-error-handling.md](10-state-management-and-error-handling.md)
11. [11-security-and-evidence-integrity.md](11-security-and-evidence-integrity.md)
12. [12-accessibility-and-responsive-design.md](12-accessibility-and-responsive-design.md)
13. [13-functional-requirements.md](13-functional-requirements.md)
14. [14-test-plan-and-test-cases.md](14-test-plan-and-test-cases.md)
15. [15-acceptance-criteria.md](15-acceptance-criteria.md)
16. [16-implementation-and-execution-log.md](16-implementation-and-execution-log.md)

## Evidence Directory
See [`docs/ui-ux/wp-ui-05-intelligence-workspace/evidence/`](evidence/):
- `baseline/`: Initial commit, lint, unit tests, and build logs.
- `ask-aegis/`: Ask workbench test logs and grounding validation.
- `retrieval/`: Passage search and ranking tests.
- `evidence-explorer/`: Passage inspection and citation integrity tests.
- `knowledge-visualization/`: Graph rendering and accessible table tests.
- `comparison/`: Multi-document alignment and conflict tests.
- `security/`: Tenant boundary and citation integrity tests.
- `accessibility/`: Keyboard and tabular fallback checks.
- `final-audit/`: Complete Vitest, Playwright, TypeScript, and build logs.

## Release Decision
**GO** — All 5 core capabilities delivered, 100% unit tests passing (22 suites, 118 tests), 100% Playwright E2E passing (19 suites, 53 tests), 0 TypeScript errors, 0 ESLint warnings.
