# Project Status — Evidence-Linked

_Last verified: 2026-10-10 against `master` @ `5bec766` plus the Phase 0 changes (see [CHANGELOG.md](CHANGELOG.md))._

**One rule governs this file: a capability is listed as working only if a test, CI job or script in this repository re-checks it.** Numbers that rot (test counts, coverage) are not hard-coded — the CI badge in the [README](README.md) is the source of truth. Anything not re-verified is labelled as such.

**Overall: alpha research prototype — not production-ready.** The ingest → retrieve → delete pipeline runs end to end in-process, but answers are mock by default, state is held in memory, and production authentication is not implemented.

> **CI note:** `master` was red at the start of Phase 0 (test jobs aborted at collection; the secret scan flagged a placeholder hash). The Phase 0 fixes were verified locally from a fresh virtualenv; they have **not yet been observed passing on GitHub** — check the badge.

---

## What works (and how to re-verify it)

| Capability | State | Re-verify with |
|---|---|---|
| Ingest PDF / DOCX / PPTX / XLSX / image / text into structured elements | Working | `pytest tests/test_ingest_workflow.py tests/test_real_world_ingestion.py` |
| Table extraction | Working, but slow — re-parses the PDF once per page (I-14) | `tests/test_table_extraction_regression.py`, `python scripts/run_benchmark.py` |
| Real-corpus benchmark | 61 of 62 documents succeed; 220 tables detected — independently re-run and reproduced | `python scripts/run_benchmark.py`, artifacts in `production/performance-report/` |
| Tenant isolation on `/v1/documents` and `/v1/query` | Working | `tests/test_multitenancy.py`, `tests/test_retrieval_tenant_isolation.py` |
| **Deny-by-default authentication** — every non-public route returns 401 without credentials | Working (added in Phase 0) | `tests/test_auth_guard.py` |
| Dev-token bypass rejected outside `AEGIS_ENVIRONMENT=development` | Working | `tests/test_auth_guard.py` |
| Document delete returns 404 afterwards | Re-verified. The vector-store / cache cascade was **not** independently re-checked | manual probe, Oct 2026 |
| 9 Prometheus metrics | Each has at least one real call site (audited by grep) | `src/observability/metrics.py` |
| `aegis-docprep` | Alpha. Installs from source with only `numpy`; its documented examples and outputs are executed by tests | `tests/test_docs_examples.py`, `aegis-docprep/tests/` |
| Dependency single-source-of-truth | `pyproject.toml` generates `requirements-*.txt` | `python scripts/check_dependency_sync.py` |
| README install path | Run on a fresh virtualenv by CI | `scripts/cold_start_check.sh` |

## Not implemented or not real yet

| Gap | ID | Evidence |
|---|---|---|
| **Production authentication** — the RS256 JWT and API-key validators are stubs; outside development every credential is rejected | I-20 | `src/api/auth.py` |
| LLM answers are mock by default (`[MOCK]`) | I-17 | live query |
| Semantic embeddings are mock unless the ML tier is installed | I-18 | container warning |
| Persistence — document state is an in-memory dict, lost on restart | I-19 | `src/services/container.py` |
| Audit log | I-21 | no implementation |
| Signed releases / provenance | I-23 | no tags published |
| Any external validation — no pilots have been completed | I-24 | GitHub has no pilot issues |

## Known defects (open)

| Defect | ID | Pinned by |
|---|---|---|
| 5 `(method, path)` pairs are claimed by two handlers; for `POST /v1/query` the AEL query endpoint is unreachable | I-12, I-13 | `tests/test_api_route_integrity.py` (ratchet) |
| 3 duplicate OpenAPI operation IDs | I-12 | `tests/test_api_route_integrity.py` (ratchet) |
| Cross-tenant query returns 200 with a placeholder answer and citations lacking `chunk_id`/`doc_id`, instead of 404 | I-11 | manual probe |
| PII `PERSON` detection can leave the surname in clear text (`Customer John Smith` → `Customer John`) | I-15 | documented in `aegis-docprep/README.md` |
| PII does not detect emails, API keys or secrets, non-US phone formats, or local 7-digit numbers | I-28 | documented in `aegis-docprep/README.md` |
| `SubmodularKnapsackPacker` has no approximation guarantee (0.02 of optimal on a 2-chunk counterexample) | I-26 | `tests/test_packer_guarantee_gap.py` (strict xfail) |
| `/health` reports 503 in mock mode and the Docker healthcheck calls a route that does not exist | I-09, I-10 | manual probe |
| `/metrics` is public and its series are labelled with `tenant_id` | — | `src/api/auth_guard.py` (documented exposure) |
| Not on PyPI — install from source | I-08 | `pypi.org` returns 404 |
| `requires-python` declares 3.10+ but CI tests only 3.12 and 3.13 | I-30 | `pyproject.toml`, CI matrix |

## Fixed in Phase 0

| Fix | ID |
|---|---|
| Anonymous callers could read other tenants' documents and wipe all documents (45 of 59 operations had no authentication) | I-27 |
| Undeclared dependencies (`hypothesis`, `python-docx`, `python-pptx`, `openpyxl`) made the documented install abort with zero tests run | I-01, I-02 |
| Two divergent dependency lists (pyproject vs requirements) | I-01 |
| Secret scan false positive (placeholder hash) | I-04 |
| Stale AEL integration test | I-05 |
| Tracked, test-mutated SQLite file (`data/annotations.db`) | I-25 |
| Documented examples that did not run, and documented outputs that were false | I-28 |
| Unsupported pilot case studies removed (quarantined in `_unverified_archive/pilot/`) | I-06 |
| Docs referenced an environment variable (`ALLOW_DEV_BYPASS`) that does not exist | I-31 |
| CI pinned to deprecated Node 20 actions and the floating `ubuntu-latest` | I-29 |

## Corrections to earlier claims

Earlier revisions of this file, the README and the changelog stated the following; each was found to be false or unsupported and has been corrected:

- "N tests passing" counts that disagreed with each other and with reality.
- Phase 10 and Phase 13 labelled "Verified" while most routes had no authentication and several routes were duplicated.
- Pilot case studies with specific metrics, which no public issue or statement corroborates.
- PII redaction of emails and API tokens; the implementation handles four entity types only.
- A "provably (1 − 1/e)" guarantee for the context packer (see I-26).
- A documented `ALLOW_DEV_BYPASS` variable that never existed; the real control is `AEGIS_ENVIRONMENT`.
- Python support "3.10–3.12"; CI tests 3.12 and 3.13.
- A memory figure and a single-document timing that cite no reproducible artifact.

The previous file is preserved unmodified, with a warning banner, at [docs/history/STATUS_2026-10-09.md](docs/history/STATUS_2026-10-09.md).

---

## Layer-by-Layer Implementation Status (Master State D)

Per Section 5.1 of the AMDI-OS Extended Monograph and its Appendix E
status matrix — the most detailed and honest implementation-status
assessment that exists in this project (a *self*-assessment — not independently audited):

| Layer | Meaning | Status |
|---|---|---|
| P | Page/element representation | Hardened |
| G | Geometric coordinate layer | Hardened |
| R | Structural recurrence | Hardened |
| F | Token frequency/weight | Hardened |
| M | Table-matrix relational | Hardened |
| T | Template fingerprint | Hardened |
| X | Structural linkage graph | Hardened |
| S | Semantic embedding | Mock fallback unless `sentence-transformers` installed — real path exists and works, but is optional and clearly flagged (`is_mock` on `MasterState.semantic_status`) |
| H | Hierarchical coordinate (persistent homology) | Proposed, not yet evaluated |
| E | Shannon-entropy | Hardened |

This table is enforced in code, not just documentation: `MasterState`
(added in this phase) carries a `LayerStatus` alongside every layer, so
`state.semantic_status.is_mock` or `state.hierarchy_status.is_proposed`
can be checked at runtime rather than only in a document no pipeline
consumer ever reads.

---

## Not Real (Previously Presented as Fact — Now Corrected)

- **"Production Ready" status** — removed. There is no evidence of any
  production deployment.
- **Penetration test report, threat model, vulnerability scan** — these were
  self-authored narrative documents, not real security testing output. Moved
  to `_unverified_archive/`. Replaced in Phase 10 with authentic `bandit` static
  analysis and `pip-audit` dependency scanning reports in `production/security-audit/`.
- **GDPR / SOC 2 / ISO 27001 "COMPLIANT" status** — self-declared, not
  certified by any accredited third party. No organization holds any formal
  compliance certification for this software. Replaced in Phase 11 with an
  honest gap analysis in `production/security-audit/compliance_gap_analysis.json`
  documenting real control implementations, partial implementations, and explicit gaps.
- **Signed release artifacts** (`SHA256SUMS.sig`, `.crt` files) — these were
  placeholder text, not real cryptographic signatures.
- **Benchmark results (94.2% accuracy, etc.)** — generated against a
  synthetic dataset (`generate_mock_dataset.py`), not real documents. The PDFs
  in that dataset do not open correctly and ground-truth entries contain
  literal placeholder text ("Mock Document eng_003"). No real-world accuracy
  claim can currently be made about this system.

---

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) and the 6-phase fix and reconstruction plan. Phase 0 (this document's baseline) restores a green, truthful starting point.
