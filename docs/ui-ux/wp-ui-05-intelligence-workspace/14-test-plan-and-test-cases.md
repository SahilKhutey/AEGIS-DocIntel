# 14 — Test Plan & Test Cases

## 1. Test Strategy Overview
The Intelligence Workspace test strategy guarantees correctness through multiple layers of verification:
- **Pure Unit Tests**: Citation validation, broken reference detection, claim-to-citation mappings.
- **Component Unit Tests**: Form submission, loading states, accessibility labels, user interactions.
- **End-to-End Playwright Tests**: Full browser simulation verifying rendering, keyboard accessibility, user flows, and backend mock integration.
- **Zero-Regression Mandate**: Existing tests (`workbench.spec.ts`, `navigation.spec.ts`, `document-library.spec.ts`, `processing.spec.ts`, `upload.spec.ts`) must pass with zero failures.

## 2. Test Execution Matrix

### Unit Test Suites (Vitest)
| Test Suite | Path | Tests | Coverage Focus |
|---|---|---|---|
| Citation Integrity | `tests/unit/citation-integrity.test.ts` | 6 tests | Citation validation, broken references, unreferenced citations |
| Question Composer | `tests/unit/question-composer.test.tsx` | 3 tests | Form validation, thinking state, submit event |
| Retrieval Search | `tests/unit/retrieval-search.test.tsx` | 3 tests | Search form, empty prevention, loading indicator |
| Evidence Detail | `tests/unit/evidence-detail.test.tsx` | 3 tests | Verbatim rendering, page coordinates, document link |
| Comparison Workspace | `tests/unit/comparison-workspace.test.tsx` | 3 tests | Minimum document threshold (min 2), mode toggle |
| Knowledge Graph | `tests/unit/knowledge-graph.test.tsx` | 3 tests | Canvas controls, accessible table view, type filtering |
| **Total Unit Tests** | `22 test files` | **118 tests** | **100% Pass Rate** |

### End-to-End Browser Specs (Playwright)
| Spec File | Path | Key Test Cases | Status |
|---|---|---|---|
| Ask AEGIS | `tests/e2e/intelligence/ask-aegis.spec.ts` | Renders workspace, prevents empty submit | Passed |
| Retrieval Interface | `tests/e2e/intelligence/retrieval.spec.ts` | Form rendering, query submit, button enable | Passed |
| Evidence Explorer | `tests/e2e/intelligence/evidence-explorer.spec.ts` | Scope selection, verbatim passage view | Passed |
| Knowledge Visualization | `tests/e2e/intelligence/knowledge-visualization.spec.ts` | Canvas rendering, accessible table toggle | Passed |
| Comparison Workspace | `tests/e2e/intelligence/comparison.spec.ts` | Document selector, mode options | Passed |
| Legacy Workbench | `tests/e2e/workbench.spec.ts` | E2E-009/010 (Ask & Citations), E2E-012 (Compare) | Passed |
| Shell Navigation | `tests/e2e/navigation.spec.ts`, `shell-navigation.spec.ts` | Route access, link visibility | Passed |
| **Total E2E Tests** | `19 test files` | **53 tests** | **100% Pass Rate** |
