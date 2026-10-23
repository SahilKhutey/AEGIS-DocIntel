# Phase 0 — Execution Report: Restore Green & Restore Honesty

**Base:** `master` @ `5bec766` (Oct 9, 2026) · **Result:** 7 commits on `fix/phase0-green-and-honest` · **Date:** Oct 10, 2026
**Status of this work:** implemented and verified **locally**. Not pushed (no credentials) and **not yet observed passing on GitHub Actions**.

## 1. Outcome in one table

| Check | Before | After (verified locally, Python 3.12) |
|---|---|---|
| README install path (`pip install -r requirements-core.txt -r requirements-dev.txt` → `pytest tests/`) | Aborts: "Interrupted: 2 errors during collection", **0 tests run** | **Passes** — 1,107 passed, 5 skipped, 2 xfailed |
| Full suite with CI's coverage gate | red on GitHub | **1,108 passed, 5 skipped, 2 xfailed**; coverage **79.78%** (gate 75%) |
| Anonymous requests to non-public routes | **45 of 59** operations accepted them | **0** accepted (6 intentionally public paths remain) |
| `openapi.json` drift check | in sync | in sync |
| `ruff check src tests scripts` | — | clean |
| `actionlint` on the new workflow | — | clean |
| `gitleaks` over full history, all branches | 1 hit (false positive) | no leaks, via a documented allowlist |
| Docs claims checker (6 rules) | 20+ violations | passes |
| Documented examples in package docs | **all 5 in `docs/docprep.md` failed** | all run; documented outputs match real output |

The 2 xfails are **tracked defects** (strict): the shadowed AEL query endpoint and the packer's missing guarantee.

## 2. The 7 commits

1. `test(api)` — route-integrity ratchet; AEL test split into independent tests (`6b14655`)
2. `fix(security)` — deny-by-default authentication guard (`d228751`)
3. `build(deps)` — `pyproject.toml` is the single source of truth; requirements files generated (`1cc6d5c`)
4. `ci` — fixes red CI; README-as-test job; pinned runners and actions; untrack mutable DB (`ceee236`)
5. `test(docs)` — executes documented examples and compares outputs; claims checker; packer-guarantee xfail (`bdd1692`)
6. `docs` — evidence-linked `STATUS.md`; unsupported claims removed; pilot material quarantined (`bd542d5`)
7. `build` — lock file regenerated from a clean venv (66 pins; the old one had 40) (`02bd2a9`)

## 3. Findings (all reproduced by running code)

### Security
- **Critical — anonymous access to most of the API.** The legacy AEL tree, annotations, admin, advanced and webhook routers were never wired to authentication. Demonstrated impact: an anonymous caller exported another tenant's document (200, text leaked) and wiped every document (`DELETE /v1/document` → 204). **Fixed** with a deny-by-default ASGI guard (`src/api/auth_guard.py`). The tests were **mutation-tested**: with the guard disabled, exactly the three security tests fail and name the leaking routes.
- **Production authentication is still a stub** (RS256 JWT and API-key validators). Outside `AEGIS_ENVIRONMENT=development` every credential is rejected, so the API is only usable in dev mode. *Not fixed — Phase 5.*
- `/metrics` is public and labelled with `tenant_id`. *Documented, not fixed.*
- Tenant isolation on `/v1/documents` and `/v1/query` **holds**. (I first misread phantom citations as a leak; retrieval never runs for the wrong tenant.)

### CI and install
- Root causes confirmed from GitHub's own check-run annotations: pytest exit code 2 and "No files were found: coverage.xml" (collection abort), and "Leaks detected" (a placeholder `a1b2c3d4e5f6...` hash in an old commit).
- `hypothesis`, `python-docx`, `python-pptx`, `openpyxl` were undeclared; `pyproject.toml` and the requirements files were two drifting hand-edited lists.
- The **Performance Regression job could never run**: gated on `refs/heads/main` while pushes land on `master`.
- Actions were on Node 20; `ubuntu-latest` **migrates to Ubuntu 26 on 2026-10-19**. Pinned to Node 24 majors (read from each `action.yml`) and `ubuntu-24.04`.
- Version caps in `pyproject` (numpy<2.1 etc.) passed the suite identically in a capped venv (1,059 passed) — they weren't breaking anything, but pinned numpy five releases behind. Removed in favour of floors-only.

### Documentation was fiction in several places
- `docs/docprep.md`: all 5 examples imported classes that do not exist.
- The package README's PII example documented a detected phone number and a redacted full name; **real output left both in clear text**. PII actually handles **4 entity types** (SSN, credit card, area-code phone, Title-Case name); emails and API tokens are **not** detected, contrary to the README. A capitalized word before a name (`Customer John Smith`) makes the matcher return `Customer John`, leaving the surname in clear.
- The documented **"provably (1 − 1/e)" packer guarantee is false**: density-greedy under a knapsack budget achieved **0.02 of optimal** on a 2-chunk counterexample. (The existing Theorem 9.1 test is valid but exercises a *different* algorithm that has the best-single-item fallback.)
- `docs/security.md` said the dev bypass was "completely excised" and named an `ALLOW_DEV_BYPASS` variable that **never existed** in code.
- Pilot "case studies": 0 stars/forks/issues on GitHub, results committed together with the recruitment post, citing issues #1–#5 that do not exist. **Quarantined** (not deleted) in `_unverified_archive/pilot/`. This does not prove they didn't happen — only that they can't be treated as evidence.
- Also fixed: stale test counts, a fabricated sample test output, "Python 3.10–3.12" support (CI tests 3.12/3.13), a case-sensitivity bug (`Architecture.md`) that breaks the docs site on Linux.

### API structure
- **5 `(method, path)` pairs are claimed by two handlers**; for `POST /v1/query` the AEL query endpoint is unreachable. **3 duplicate OpenAPI operation IDs** remain (the old STATUS said they were eliminated). Frozen by a ratchet test so the list can only shrink. *Fix is Phase 3.*

## 4. Mistakes I made and corrected along the way

- I called `passlib`/`bcrypt` "dead dependencies" from a `src/`-only search; `backend/security/` uses them. Kept.
- My first route enumeration saw only 8 operations (newer FastAPI nests routers lazily). I built a proper walker (`src/api/route_inspect.py`).
- My docs-claims checker initially **missed a known-bad case** because its own docstring polluted its search corpus. Found by testing it against a known violation.
- Rebuilding the commit series silently **re-tracked `data/annotations.db`**; my own hygiene test caught it, fixed via fixup.
- I deleted a test file before re-reading it; recovered the original from git and confirmed every assertion was preserved.

## 5. What is NOT verified

- **GitHub Actions has not run these changes.** In particular the new `v7`/`v3` action majors (only their Node 24 runtime was checked) and that `gitleaks-action` honours `.gitleaksignore`.
- **Python 3.13 was not tested** — only 3.12. CI's matrix includes 3.13.
- Only Linux. No macOS or Windows runs.
- The `LangChain` doc example was verified manually (`langchain-core` 1.6.7), not in CI. The LlamaIndex example was removed as unverifiable.
- Real OCR needs the `tesseract` binary; tests don't exercise it.
- Vector-store / cache cascade on delete was not re-checked (only delete → 404).

## 6. Applying this work

```bash
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git && cd AEGIS-DocIntel
git checkout -b fix/phase0-green-and-honest origin/master
git am /path/to/phase0/*.patch          # or: git fetch /path/to/phase0.bundle <branch>
scripts/cold_start_check.sh             # the README's own commands, fresh venv
```

## 7. Remaining open work (maps to the 6-phase plan)

| Open | Plan phase |
|---|---|
| `pip install aegis-docprep` (not on PyPI); `/health` 503 + wrong Docker healthcheck | 2 |
| 5 route collisions; cross-tenant query returns 200 + phantom citations instead of 404 | 3 |
| Table extraction re-parses PDF per page (~68× slower than naive); perf job covers the loader only | 4 |
| PII surname leak; packer guarantee (add best-single-item fallback) | 4 |
| Production auth, persistence, audit log, real LLM/embeddings in CI | 5 |
| Stranded feature branch (29 conflicts), signed release, real pilots | 6 |
| `requires-python` declares 3.10+ but only 3.12/3.13 are tested | 2 |
