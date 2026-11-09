# 13 — Functional & Non-Functional Requirements

## 1. Functional Requirements Matrix

| ID | Requirement | Implementation | Verification |
|---|---|---|---|
| **IW-FR-001** | Ask natural-language questions | `QuestionComposer.tsx`, `/ask` | `question-composer.test.tsx`, `ask-aegis.spec.ts` |
| **IW-FR-002** | Select authorized document scope | Scope filter pill bar on `/ask` and `/intelligence/*` | `ask-aegis.spec.ts`, `workbench.spec.ts` |
| **IW-FR-003** | Display generated answers | `ChatMessage.tsx`, `/ask` | `workbench.spec.ts:403` |
| **IW-FR-004** | Display citation references | `CitationList.tsx`, `EvidencePanel.tsx` | `workbench.spec.ts:403`, `citation-integrity.test.ts` |
| **IW-FR-005** | Inspect claim-to-citation mappings | `ChatMessage.tsx`, `getClaimCitations` | `citation-integrity.test.ts` |
| **IW-FR-006** | Display answer warnings & safe abstention | `ChatMessage.tsx` abstention banner | `ask.schema.ts`, `ChatMessage.tsx` |
| **IW-FR-007** | Preserve conversation context | `ChatMessageItem[]` state on `/ask` | `AskContent` in `ask/page.tsx` |
| **IW-FR-008** | Search authorized documents | `RetrievalSearch.tsx` | `retrieval-search.test.tsx`, `retrieval.spec.ts` |
| **IW-FR-009** | Display retrieved passages | `RetrievalResult.tsx` | `retrieval.spec.ts` |
| **IW-FR-010** | Display ranking metadata when supplied | `RetrievalResult.tsx` score & rank badges | `RetrievalResult.tsx` |
| **IW-FR-011** | Filter retrieval results | Scope selector on `/intelligence/retrieval` | `retrieval.spec.ts` |
| **IW-FR-012** | Navigate to retrieved evidence | "Inspect evidence" router push | `retrieval/page.tsx` |
| **IW-FR-013** | Inspect source passages and page references | `EvidenceDetail.tsx` | `evidence-detail.test.tsx`, `evidence-explorer.spec.ts` |
| **IW-FR-014** | Identify broken citation references | `findBrokenCitationReferences` | `citation-integrity.test.ts` |
| **IW-FR-015** | Open source documents through routes | "Open source document" -> `/documents/[id]` | `EvidenceDetail.tsx` |
| **IW-FR-016** | Display structured knowledge nodes | `KnowledgeGraph.tsx` SVG canvas & table | `knowledge-graph.test.tsx` |
| **IW-FR-017** | Display structured relationships | `KnowledgeGraph.tsx` edges & labels | `knowledge-graph.test.tsx` |
| **IW-FR-018** | Filter graph data | Node type filter buttons | `knowledge-graph.test.tsx`, `knowledge-visualization.spec.ts` |
| **IW-FR-019** | Navigate from graph to evidence | Node details document links | `KnowledgeGraph.tsx` |
| **IW-FR-020** | Provide accessible graph alternative | Tabular view toggle (WCAG 2.2 AA) | `knowledge-graph.test.tsx`, `knowledge-visualization.spec.ts` |
| **IW-FR-021** | Select documents for comparison | `ComparisonWorkspace.tsx` selection grid | `comparison-workspace.test.tsx`, `comparison.spec.ts` |
| **IW-FR-022** | Compare two or more documents | Enforces min 2 documents in `/compare` | `comparison-workspace.test.tsx`, `workbench.spec.ts:421` |
| **IW-FR-023** | Display differences and summaries | `ComparisonResult.tsx` | `ComparisonResult.tsx` |
| **IW-FR-024** | Link differences to source evidence | Left and Right evidence quotes & links | `ComparisonResult.tsx` |
| **IW-FR-025** | Display significance when assessed | StatusBadge (`conflict`, `warning`, `ready`) | `ComparisonResult.tsx` |
| **IW-FR-026** | Handle long-running comparison jobs | Loading state & job compatibility | `comparison/page.tsx` |
| **IW-FR-027** | Display loading, empty, error states | `EmptyState`, `ErrorState`, loading spinners | Verified across all 5 capabilities |
| **IW-FR-028** | Preserve workspace isolation | Tenant-scoped headers via `api-client` | `api-client.ts`, `ask.api.ts` |
| **IW-FR-029** | Handle cancellation and retry | `AbortSignal` & onRetry handlers | Handled in API services and error components |
| **IW-FR-030** | Maintain accessible interactions | Semantic landmarks, aria labels, focus states | `accessibility.spec.ts`, WCAG 2.2 AA audit |

## 2. Non-Functional Requirements
- **IW-NFR-001**: Backend-enforced authorization and tenant boundaries.
- **IW-NFR-002**: No cross-tenant data leakage.
- **IW-NFR-003**: 100% Zod validation on incoming backend responses.
- **IW-NFR-004**: Verifiable citation and evidence traceability.
- **IW-NFR-005**: Zero fabricated confidence scores or LLM claims.
- **IW-NFR-006**: XSS prevention via text-node escaping.
- **IW-NFR-007**: Responsive across mobile (390px), tablet (844px), desktop (1280px).
- **IW-NFR-008**: WCAG 2.2 Level AA accessibility compliance.
- **IW-NFR-009**: Cancellation signals passed for in-flight queries.
- **IW-NFR-010**: Zero regressions across legacy E2E test suites.
- **IW-NFR-011**: Accessible tabular alternative for knowledge graphs.
- **IW-NFR-012**: Reproducible test evidence archived in `evidence/`.
