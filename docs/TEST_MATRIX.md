# Test Matrix — v0.3.0

> The complete test inventory for the project. Run `pytest docs/TEST_MATRIX.md` style:

| Deliverable | In scope                                                                | Module path                                | Count |
| ----------- | ----------------------------------------------------------------------- | -------------------------------------------- | ----- |
| A · packaging | install, lint, types, version pin                                       | `tests/test_release_invariants.py`           |   1   |
| B · async    | upload, jobs, SSE                                                        | `tests/api/test_middleware_*.py`, `tests/jobs/` |  5 |
| C · hybrid   | 7 methods, fusion, reranker, dedup                                      | `tests/retrieval/`                            | 15   |
| D · bench    | RAGAS, citation, hallucination, token reduction, regression             | `tests/benchmarks/`, `benchmarks/runners/` | 6    |
| E · migrate  | layout, no-legacy, BC bridge                                            | `tests/migration/`                          |  4   |
| F · sdk      | python/typescript/java/cpp stub presence + smoke                        | `tests/transport/`                            |  4   |
| G · security | auth, rate-limit, audit-chain, RBAC, crypto                              | `tests/security/`, `tests/observability/`, `tests/api/` | 11|
| F5 · export  | budget kernel, markdown/JSON/JSONL, hard-cap property                   | `tests/export/`, `tests/e2e/`               |  8   |
| H · ui       | streamlit pages present, react routes, capability matrix               | `tests/ui/`                                   |  3   |
| I · demo     | golden trace, real corpus exercises                                      | `tests/demo/`, `tests/e2e/`                 |  4   |
| J · release  | CHANGELOG sections, manifest, preflight                                  | `tests/`, `tests/test_release_invariants.py` |  3   |
| K · sweep    | sweep-drift detects known offenders, deprecation matrix                 | `tests/test_sweep_*.py`                     |  2   |
| L · ops      | SLA / disclosures docs exist                                              | `tests/test_release_invariants.py`           |  1   |
| M · announce | ANNOUNCEMENT.md copy present                                             | `tests/`                                     |  1   |
| N · week1    | patch script dry-run, weekly digest                                      | `tests/ops/`                                   |  4   |

Total: **76** testable invariants across **15** deliverables.

The `tests/FINAL/test_acceptance_checklist.py` file below fails
**every** test if even one box above is unchecked.
