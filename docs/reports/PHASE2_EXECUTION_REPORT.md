# Phase 2 — Execution Report: Ingestion & Document Pipeline Hardening

**Base:** `fix/phase0-green-and-honest` @ `8a6035f` · **Result:** Commit `f2194c8` · **Date:** Oct 18, 2026  
**Status of this work:** Implemented, verified locally, and exported to patch/bundle.

---

## 1. Summary of Changes

| Defect / Optimization | Before Phase 2 | After Phase 2 | Verification Evidence |
|---|---|---|---|
| **Table Extraction PDF Re-parsing ($O(N^2)$ bottleneck)** | `_extract_tables` in `src/workflows/ingest_workflow.py` serialized `page_obj.parent.tobytes()` and invoked `pdfplumber.open(...)` on every page (re-parsing a multi-page PDF $N$ times) | `_normalize_pdf` opens `pdfplumber.open(io.BytesIO(doc.raw_bytes))` once at document level, passing `pl_page` to each iteration; fallback preserved | `tests/test_ingest_workflow.py` (8 passed in 20.31s); eliminates repetitive PDF decompress/parse |
| **Submodular Context Packer Guarantee (I-26)** | Density-greedy algorithm had no approximation guarantee on knapsack constraints; counterexample achieved 0.02 of optimal (tracked as strict xfail) | Added best-single-item fallback: returns $\max(F(S_{\text{greedy}}), \max_{i: c_i \le B} F(\{i\}))$, achieving the proven $\frac{1}{2}(1 - 1/e) \approx 0.316$ bound for monotone submodular knapsack | `tests/test_packer_guarantee_gap.py` (3 passed in 11.78s; strict xfail turned into active passing test); `aegis-docprep/tests/test_context_packer.py` (6 passed) |
| **PII Surname Matcher Leak (I-15)** | `NAME_REGEX` was a rigid 2-token match that captured capitalized prefixes (`Customer John Smith` -> `Customer John`), leaving `Smith` unredacted in clear text | Tokenizer processes consecutive Title-Case runs, strips non-name boundary words (`Customer`, `Call`, `Patient`, etc.), supports 2–3 word names, and protects surnames | `aegis-docprep/tests/test_pii_redaction.py` (9 passed); compliance suite (16 passed) |
| **`pyproject.toml` Python Path** | `pythonpath` in root `pyproject.toml` omitted `aegis-docprep`, causing pytest to load stale installed site-packages | `pythonpath = [".", "aegis-docprep", "sdk/python"]` ensures pytest tests run against current codebase | Root pytest run loads local repository cleanly (64 passed, 1 skipped) |
| **Package Documentation Alignment** | `aegis-docprep/README.md` and `docs/docprep.md` described I-15 and I-26 as open defects | Updated to state proven $(1 - 1/e)/2$ bound and surname leak resolution | `python scripts/check_docs_claims.py` passed (0 violations) |

---

## 2. Commit Details

Commit `f2194c8`:
```
feat(pipeline): eliminate O(N^2) table PDF re-parsing, implement submodular packer guarantee, and resolve PII surname leak

 aegis-docprep/README.md                       |  9 ++---
 aegis-docprep/aegis_docprep/context_packer.py | 26 +++++++++++++
 aegis-docprep/aegis_docprep/pii_redaction.py  | 53 +++++++++++++++++----------
 aegis-docprep/tests/test_pii_redaction.py     | 38 +++++++++++++++++++
 docs/docprep.md                               |  5 +--
 pyproject.toml                                |  2 +-
 src/compliance/redaction_engine.py            | 53 +++++++++++++++++----------
 src/engines/retrieval/submodular_packer.py    | 26 +++++++++++++
 src/workflows/ingest_workflow.py              | 53 +++++++++++++++++++--------
 tests/test_packer_guarantee_gap.py            |  8 +---
 10 files changed, 202 insertions(+), 71 deletions(-)
```

---

## 3. Machine Verification Evidence

1. **Automated Test Suites**:
   - `tests/test_ingest_workflow.py`: `8 passed` (table extraction verified).
   - `tests/test_packer_guarantee_gap.py`: `3 passed` (guarantee holds; xfail marker removed).
   - `aegis-docprep/tests/`: `20 passed` (context packing, PII, reading order).
   - `tests/test_compliance_redaction.py` + related: `16 passed`.
   - `tests/test_auth_guard.py`: `25 passed`.
   - `tests/test_docs_examples.py`: `7 passed, 1 skipped` (executed live against docs).
   - `tests/test_docs_claims.py`: `1 passed`.

2. **Automated Consistency & Hygiene Gates**:
   - `python scripts/check_docs_claims.py`: `OK — docs claims check passed (R1 cold-start, R2 links, R3 counts, R4 pilots, R5 readiness, R6 env-vars)`.
   - `python scripts/check_dependency_sync.py`: `OK — 5 requirements files match pyproject.toml`.
   - `ruff check src tests scripts aegis-docprep`: `All checks passed!`.
   - `OpenAPI diff`: `0 diff` against `openapi.json`.

---

## 4. Exported Artifacts

- Patch: [0001-feat-pipeline-eliminate-O-N-2-table-PDF-re-parsing-i.patch](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/outputs/phase2/0001-feat-pipeline-eliminate-O-N-2-table-PDF-re-parsing-i.patch)
- Git Bundle: [phase2.bundle](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/outputs/phase2/phase2.bundle)
