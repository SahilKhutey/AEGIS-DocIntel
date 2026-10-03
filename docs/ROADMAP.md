# AEGIS-DocIntel → Viable Product
## 16-Phase Development & Remediation Roadmap

**Purpose of this document:** Convert AEGIS-DocIntel from an ambitious, partially-fabricated prototype into a credible, deployable document-intelligence component that AI teams can actually trust and adopt. Phases are sequential but some can run in parallel once noted.

**Guiding principle for every phase:** Nothing ships or gets claimed unless it has been independently verified. If a phase produces a number, a certification, or a "PASS," it must be reproducible by someone outside the project.

---

## PHASE 1 — Truth Audit & Public Credibility Reset
**Goal:** Stop the bleeding. Remove every claim that isn't backed by evidence before anyone else finds it first.

**Steps:**
1. Inventory every claim in `README.md`, `production/`, and the `Aegis Doc/` monographs (badges, "Production Ready," compliance statuses, benchmark numbers, signatures).
2. Classify each claim: **Verified / Partially true / Fabricated**.
3. Delete or quarantine fabricated artifacts (`penetration_test_report.md`, `compliance_check.json`, `.sig`/`.crt` files, `benchmark_results.json`) into an `_unverified_archive/` folder — do not present them as current status.
4. Replace README badges with accurate ones: `Status: Alpha / Experimental`, `Tests: 944 passing (unverified against real-world data)`.
5. Add a top-of-README `STATUS.md` disclosure: what's real, what's aspirational, what's fabricated-and-removed.

**Deliverable:** Honest README + `STATUS.md`.  
**Exit criteria:** A skeptical outside engineer reading the repo cannot find a single unverifiable claim presented as fact.  
**Time:** 3–5 days.

---

## PHASE 2 — Build & Dependency Repair
**Goal:** Make `git clone && pip install -r requirements.txt && pytest` actually work, first try, on a clean machine.

**Steps:**
1. Rebuild `requirements.txt` from actual imports (`pipreqs` or manual `grep -rn "^import\|^from" src/`).
2. Add missing packages found during my own test run: `scikit-learn`, `structlog`, `bcrypt`, `passlib`, `python-jose`, `prometheus-client`, `pytest-asyncio`.
3. Pin every dependency to a tested version range; commit `requirements.lock.txt` generated via `pip freeze` from a clean install.
4. Separate `requirements-core.txt` (light, math/API only) from `requirements-ml.txt` (torch, sentence-transformers, faiss) so lightweight deployments aren't forced into multi-GB installs.
5. Document minimum Python version and OS compatibility (test on Linux + macOS + WSL).

**Deliverable:** Verified, reproducible install path; two-tier requirements files.  
**Exit criteria:** Fresh clone → install → full test suite green, on a machine that has never touched this repo.  
**Time:** 1 week.

---

## PHASE 3 — Continuous Integration
**Goal:** Never let "it works on my machine" happen again.

**Steps:**
1. Add `.github/workflows/ci.yml`: install → lint (`ruff`/`flake8`) → type-check (`mypy`) → `pytest` on every push/PR.
2. Add a matrix build (Python 3.12/3.13, Ubuntu/macOS).
3. Add `pytest-cov`; fail CI if coverage drops below a set floor (start at whatever current real coverage is, ratchet up over time).
4. Add dependency vulnerability scanning (`pip-audit` or `safety`) as a CI step, not a hand-written claim.
5. Add a badge that pulls live from CI — not a hardcoded static badge.

**Deliverable:** Green CI pipeline, live badges.  
**Exit criteria:** Every merge to main is automatically tested; no manually-asserted "Tests: 860+ Passing" badges remain.  
**Time:** 3–5 days (can run parallel with Phase 2 completion).

---

## PHASE 4 — Architectural Deduplication
**Goal:** One canonical implementation per concern.

**Steps:**
1. Diff `src/connectors/` vs `src/ael/connectors/` line by line; decide which is more mature/tested.
2. Merge into a single connector module; delete the loser; update all imports and tests.
3. Delete the duplicate `Aegis Doc/` folder (byte-identical to `Aegis/`) — keep one canonical docs location.
4. Consolidate `_archive/AMDI-legacy`, `_archive/MDIE-legacy`, `_archive/amdi-os-legacy` into a single `docs/history.md` narrative, then remove the dead code weight from the repo (or move to a separate `archive` branch, not the main tree).
5. Run full test suite after each merge to confirm no regressions.

**Deliverable:** Single connector layer, single docs tree, ~8–10MB lighter repo.  
**Exit criteria:** `grep` for duplicate class/function names across the repo returns zero unintentional duplicates.  
**Time:** 1–2 weeks.

---

## PHASE 5 — Core Schema Unification
**Goal:** Every engine reads/writes the same `DocumentObject` / Master State `D` shape — no drift between modules built in different sessions.

**Steps:**
1. Formally define the `D = (P, S, G, R, F, M, T, X, H, E)` schema as a single Pydantic model (`src/core/document_state.py`) with strict typing.
2. Audit every engine in `src/engines/` and `src/math_concepts/` against this schema; fix any engine that uses an ad-hoc shape instead.
3. Add schema-validation tests: feed a document through the full pipeline and assert the state object is valid at every stage transition.
4. Version the schema (`schema_version` field) so future changes don't silently break old exports.

**Deliverable:** One source of truth for document state, enforced by tests.  
**Exit criteria:** Full pipeline run end-to-end validates against the schema at every stage.  
**Time:** 2 weeks.

---

## PHASE 6 — Test Suite Hardening
**Goal:** Move from "944 unit tests pass" to "the system does what it claims, provably."

**Steps:**
1. Categorize existing tests: unit / integration / end-to-end. Most current tests appear to be unit-level — add missing integration coverage.
2. Write true end-to-end tests: real file in → full pipeline → assert on final export structure and content correctness (not just "no exception thrown").
3. Add property-based tests (via `hypothesis`) for the math engines — topology, spectral, optimization — to catch edge cases unit tests miss.
4. Add regression tests for every bug found in later phases (permanent lock-in).
5. Measure and publish real coverage % (not a claim — a CI-generated report).

**Deliverable:** Coverage report, integration test suite, property-based test suite for math core.  
**Exit criteria:** >80% real line coverage on `src/`, verified by CI, with meaningful (not trivial) assertions.  
**Time:** 3 weeks.

---

## PHASE 7 — Real-World Ingestion Validation
**Goal:** Prove the ingestion engines work on messy, real documents — not just clean synthetic fixtures.

**Steps:**
1. Collect a real, varied test corpus per format: multi-column academic PDFs, scanned/OCR'd contracts, complex Excel financial models, PowerPoint decks with embedded charts, real speech recordings with background noise.
2. Run each ingestion path (`PDF`, `DOCX`, `XLSX`, `PPTX`, Image, Speech) against this corpus; manually verify output correctness for a sample set.
3. Log and triage every failure mode (encoding issues, malformed tables, OCR garbage, diarization errors).
4. Fix top failure classes; re-test.
5. Publish a documented "known limitations" list — this alone builds more trust than a fake 100% pass claim.

**Deliverable:** Validated ingestion pipeline + honest limitations doc.  
**Exit criteria:** Each format type has been tested against ≥20 real-world documents with human-verified accuracy figures.  
**Time:** 3–4 weeks.

---

## PHASE 8 — Real Benchmark Dataset Construction
**Goal:** Replace the "Mock Document eng_003" placeholder benchmark with something a reviewer can't dismiss in five minutes.

**Steps:**
1. Source real, licensable/public datasets: DocBank, FUNSD, PubLayNet, RVL-CDIP, or your own de-identified sample documents (invoices, contracts, reports).
2. Build genuine ground-truth Q&A/extraction pairs per document — either manually annotated or via a validated semi-automated pipeline with human review.
3. Ensure every PDF in the dataset actually opens and parses (validate with `pymupdf` as a sanity gate before it enters the corpus).
4. Version and document dataset provenance (source, license, size, category breakdown).
5. Make the dataset (or an anonymized subset) publicly downloadable for reproducibility.

**Deliverable:** Real, reproducible benchmark corpus with public provenance.  
**Exit criteria:** An external party can download the dataset and re-run the eval script themselves.  
**Time:** 3–4 weeks (can overlap with Phase 7).

---

## PHASE 9 — Performance Benchmarking & Honest Publication
**Goal:** Replace fabricated performance numbers with real, reproducible ones — even if they're less flattering.

**Steps:**
1. Write an open evaluation harness (`scripts/run_benchmark.py`) that anyone can execute against the Phase 8 dataset.
2. Measure real accuracy, citation accuracy, hallucination rate, token reduction, and latency — using actual LLM calls where relevant, not assumed/estimated numbers.
3. Compare against real baselines: raw-text RAG, naive chunking, an existing open-source document loader (e.g. Unstructured.io) — not against strawmen.
4. Publish full raw results (per-document, not just aggregates) alongside the summary.
5. Re-run quarterly as the pipeline evolves; track trend over time, not a single snapshot.

**Deliverable:** Public, reproducible benchmark report with raw data attached.  
**Exit criteria:** Someone outside the project reruns the harness and gets numbers within a reasonable margin of the published ones.  
**Time:** 2 weeks (after Phase 8).

---

## PHASE 10 — Security Hardening (Real)
**Goal:** Replace the fictional pentest report with actual security work.

**Steps:**
1. Run automated scans: `bandit` (Python static analysis), `pip-audit`/`safety` (dependency CVEs), `semgrep` (custom rule sets for injection/SSRF/path traversal patterns).
2. Manually test the claims already written in the fake report — SQLi, XSS, path traversal, SSRF, IDOR — as if they'd never been "verified" before, using real payloads against a running instance.
3. Fix confirmed issues; write regression tests for each.
4. If budget allows, commission a real third-party penetration test once the API surface is stable — this is the only way to legitimately claim "PASS."
5. Set up automated secret-scanning (`gitleaks`) in CI to prevent credential leaks going forward.

**Deliverable:** Real vulnerability scan reports (tool output, not narrative), fixed issues, regression tests.  
**Exit criteria:** Automated security scans run in CI on every PR; any real pentest findings are remediated and documented with dates and CVE/finding IDs.  
**Time:** 2–3 weeks.

---

## PHASE 11 — Compliance Documentation Rebuild
**Goal:** Only claim compliance posture you can actually defend under questioning.

**Steps:**
1. Rewrite `compliance_check.json` as a **gap analysis**, not a self-graded "COMPLIANT" scorecard: for each GDPR/SOC2/ISO27001 control, state current implementation status honestly (Implemented / Partial / Not Implemented / Not Applicable).
2. Prioritize genuinely achievable items first: encryption in transit (TLS), encryption at rest, audit logging, RBAC — implement and verify these for real if not already solid.
3. Do NOT claim SOC2/ISO27001 "compliance" without an actual accredited auditor engagement — those are formal certifications, not documents you write yourself.
4. If there's real enterprise interest, engage a compliance consultant for a readiness assessment before pursuing formal certification.
5. Keep this document versioned and dated, updated as controls are actually implemented — not written once and left static.

**Deliverable:** Honest compliance gap-analysis document, replacing fictional certification claims.  
**Exit criteria:** No compliance claim exists anywhere in the repo that couldn't survive a customer's security questionnaire follow-up question.  
**Time:** 1–2 weeks (documentation) + ongoing (actual control implementation depends on Phase 10 findings).

---

## PHASE 12 — Observability Activation
**Goal:** Turn the unused Prometheus/OpenTelemetry hooks into an actual working monitoring stack.

**Steps:**
1. Stand up a local Grafana + Prometheus instance via `docker-compose` and confirm metrics actually flow from `src/observability/`.
2. Instrument key pipeline stages with real latency/error/throughput metrics (per-engine, not just aggregate).
3. Add structured logging correlation IDs (`structlog` is already a dependency — use it consistently across all modules, not just where it happens to exist).
4. Build 2–3 real dashboards: ingestion throughput, engine latency breakdown, error rate by document type.
5. Add alerting rules for basic failure conditions (queue backup, error rate spike).

**Deliverable:** Working, screenshot-able observability stack — not just instrumentation code that's never been run.  
**Exit criteria:** You can run the docker-compose stack, ingest a document, and watch real metrics appear on a real dashboard.  
**Time:** 1–2 weeks.

---

## PHASE 13 — API & SDK Stabilization
**Goal:** Make the public-facing surface (REST API + Python/TS/Java/C++ SDKs) something external developers can rely on without breakage.

**Steps:**
1. Freeze and version the REST API (`/v1/...`) with an explicit versioning/deprecation policy.
2. Generate OpenAPI spec automatically from FastAPI (already partially there) and validate it's accurate against actual behavior.
3. Audit each SDK (`sdk/python`, `sdk/typescript`, `sdk/java`, `sdk/cpp`) for parity — do they all support the same operations? Are they tested against the live API in CI?
4. Add SDK-level integration tests that hit a real (test) instance of the API, not mocked responses only.
5. Publish the Python SDK to PyPI (even as a pre-release/alpha) so real developers can `pip install` and try it — this is a strong forcing function for quality.

**Deliverable:** Versioned, tested API contract; at least one SDK published and installable externally.  
**Exit criteria:** A developer unfamiliar with the codebase can `pip install` the SDK and successfully call the API following only the public docs.  
**Time:** 2–3 weeks.

---

## PHASE 14 — Scope Narrowing & Core Packaging
**Goal:** Stop being a "16-domain operating system" and become a focused, adoptable tool built around your strongest, most validated components.

**Steps:**
1. Based on Phases 7–9 results, identify the 2–3 components with the best validated accuracy/value: most likely candidates are the **spatial reading-order engine**, the **submodular context packer**, and the **PII redaction/compliance gate**.
2. Extract these into a standalone, independently installable package (e.g. `pip install aegis-docprep`) decoupled from the full 16-domain math suite.
3. Write focused, example-driven documentation for this narrow package — one clear use case (e.g. "drop-in document loader for LangChain/LlamaIndex RAG pipelines that reduces token cost by X% without losing citation accuracy").
4. Keep the full 16-domain research platform as a separate, clearly-labeled "research/experimental" repo or mode — don't force adopters to buy the whole system to get the useful part.
5. This is the single highest-leverage strategic decision in the roadmap: a focused tool with honest, verified numbers beats an unfocused "operating system" with unverifiable ones, every time, in developer adoption.

**Deliverable:** A narrow, installable, documented package solving one clear problem well.  
**Exit criteria:** Someone can solve a real RAG context-budgeting or PII-redaction problem using only this package, without touching the rest of the monorepo.  
**Time:** 2–3 weeks.

---

## PHASE 15 — Pilot Deployment & External Validation
**Goal:** Get real usage and real feedback before making any more claims.

**Steps:**
1. Recruit 5–10 external developers/teams (open-source community, dev forums, LinkedIn/X technical audience) to pilot the Phase 14 package against their own real documents.
2. Set up a lightweight feedback loop: GitHub Issues templates for bug reports, a short structured survey for accuracy/usefulness feedback.
3. Track real usage metrics if pilots opt in (with consent and privacy safeguards): document types processed, error rates encountered, token savings observed.
4. Fix the top recurring issues surfaced by pilots.
5. Collect 2–3 honest testimonials or case studies (with permission) — real user validation is worth more than any self-written benchmark.

**Deliverable:** Real usage data, real bug fixes driven by real users, honest case studies.  
**Exit criteria:** At least 5 external users have successfully run the tool against their own data and provided usable feedback.  
**Time:** 4–6 weeks (mostly waiting on pilot usage + iteration).

---

## PHASE 16 — Productization & Go-to-Market Readiness
**Goal:** Package everything above into something a business or team can adopt with confidence.

**Steps:**
1. Rewrite all public-facing materials (README, website copy, pitch deck if applicable) around the Phase 14–15 validated reality — lead with the narrow, proven value, not the aspirational 16-domain vision.
2. Decide licensing model deliberately: open-core (narrow package open-source, advanced features/support paid) is a common, credible path for this kind of tool.
3. Set up proper support channels: issue triage SLA, documentation site (e.g. via `mkdocs` or `docusaurus`), changelog discipline.
4. Only pursue formal SOC2/ISO certification at this stage if enterprise pilots specifically require it and there's a funded plan to pay for and pass a real audit.
5. Define a public roadmap for the remaining 13 math domains as "planned / experimental" — turn the ambition into an honest forward-looking roadmap rather than a present-tense claim.

**Deliverable:** A credible, adoptable open-core product with honest public positioning and a real support/development cadence.  
**Exit criteria:** A new user can go from "hears about this tool" → "reads honest docs" → "installs it" → "gets real value" → "trusts the team enough to consider paying for more," entirely based on verifiable claims.  
**Time:** Ongoing.

---

## Summary Timeline

| Phase | Focus | Approx. Duration | Can Run in Parallel With |
|---|---|---|---|
| 1 | Truth audit & credibility reset | 3–5 days | — |
| 2 | Build/dependency repair | 1 week | Phase 1 |
| 3 | CI/CD | 3–5 days | Phase 2 |
| 4 | Deduplication | 1–2 weeks | — |
| 5 | Schema unification | 2 weeks | Phase 4 (end) |
| 6 | Test suite hardening | 3 weeks | Phase 5 |
| 7 | Real ingestion validation | 3–4 weeks | Phase 8 |
| 8 | Benchmark dataset construction | 3–4 weeks | Phase 7 |
| 9 | Performance benchmarking | 2 weeks | — (after 7&8) |
| 10 | Security hardening | 2–3 weeks | Phase 9 |
| 11 | Compliance rebuild | 1–2 weeks | Phase 10 |
| 12 | Observability | 1–2 weeks | Phases 10–11 |
| 13 | API/SDK stabilization | 2–3 weeks | Phase 12 |
| 14 | Scope narrowing & packaging | 2–3 weeks | — (after 13) |
| 15 | Pilot deployment | 4–6 weeks | — (after 14) |
| 16 | Productization & GTM | Ongoing | — (after 15) |
