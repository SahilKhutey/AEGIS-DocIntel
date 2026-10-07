# Changelog

All notable changes to the AEGIS-DocIntel project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0-alpha.1] - October 2026

### Added
- **Real Security Hardening & Vulnerability Remediation (Phase 10):**
  - **Auth Bypass Gating:** Fixed critical vulnerability in `src/api/auth.py` where `dev-*` JWTs and `aegis-dev-key` API keys unconditionally granted admin/editor access to any tenant. Gated credentials strictly behind `AEGIS_ENVIRONMENT=development` (fail-safe default: `production`). Added security regression tests in `tests/test_auth.py`.
  - **Real Bandit Static Analysis:** Executed Bandit static scan across 42,761 LOC in `src/`. Published `production/security-audit/bandit_report.md` and `bandit_results.json` with comprehensive exploitability tracing (triaging SQL construction, local LLM URLs, 0.0.0.0 container bindings, and non-cryptographic hashes).
  - **Non-Cryptographic MD5 Annotation:** Explicitly annotated `hashlib.md5(..., usedforsecurity=False)` across `src/engines/recurrence/recurrence_engine.py` and `src/engines/retrieval/recurrence_search.py` for MinHash and LSH document fingerprinting.
  - **PyJWT Migration:** Migrated from `python-jose` to `PyJWT[crypto]>=2.9.0` across `src/api/auth.py`, `requirements-core.txt`, and `pyproject.toml`, eliminating transitive dependency on `ecdsa` (PYSEC-2026-1325 Minerva timing vulnerability).
  - **Real Pip-Audit Dependency Scan:** Conducted supply-chain vulnerability audit using `pip-audit` against all 62 resolved dependencies in `requirements-core.txt`; verified 0 known vulnerabilities and published `production/security-audit/pip_audit_report.md` and `pip_audit_results.json`.
  - **Redis Optionality Correction:** Corrected earlier Phase 2 claim in `STATUS.md` regarding `redis`: confirmed as a real, actively used optional dependency lazily imported in `hierarchical_memory.py` and `semantic_cache.py`.
  - **Systemic Bare `except Exception: pass` Remediation:** Completed Phase 9 exception audit across `src/engines/semantic/semantic_engine.py`, `src/memory_engine/semantic_cache.py`, `src/engines/context/context_builder.py`, `src/engines/llm/llm_interface.py`, and `src/engines/memory/retriever.py`, replacing silent swallowing with structured warning and debug logging.
- **Production Hardening & Performance Baselines (Phase 9):**
  - Instrumented `PDFLoader.load()` and all core engines with `time.perf_counter` timing; recorded Phase 9 baseline throughput on real corpus: 14-page / 1.3MB PDF loads in **~71–119ms**, normalization in **~246ms**, all engines combined in **~91ms**, total loader memory **0.14MB** (tracemalloc).
  - Fixed double text-extraction in `src/ingestion/pdf_loader.py`: `_extract_metadata()` previously called `page.get_text()` on the first 5 pages independently, then `load()` called it again on all pages — identified via instrumentation. Fixed by passing pre-extracted `text_parts` into `_extract_metadata()`, eliminating the redundant fitz pass.
  - Fixed `PDFLoader.validate()` to scan the first 1024 bytes instead of `startswith()`, so Ghostscript-style PDFs that prepend a version comment before the `%PDF-` marker are correctly accepted.
  - Added `tests/test_performance.py` with 5 `@pytest.mark.slow` regression tests: time budget (10s ceiling), double-extraction fix verification, Ghostscript-header validate() fix, 500MB memory budget, and char_count accuracy guard. All 5 pass in 2.58s.
  - Added `performance` CI job to [`.github/workflows/ci.yml`](.github/workflows/ci.yml): runs only on `main` branch pushes after the test job passes; executes `pytest tests/test_performance.py -m slow` and uploads `timing_results.csv` as a build artifact.
  - Added `scripts/run_benchmark.py`: evaluation harness that runs all loaders against `production/benchmark-dataset-real/{pdf-corpus,docx-corpus}` and writes real timing data to `production/benchmark-dataset-real/timing_results.csv`.
  - Fixed critical table extraction bug in `src/workflows/ingest_workflow.py`: `_extract_tables()` called non-existent `page_obj.parent.to_bytes()` and `pdfplumber.open(stream=...)` (no such parameter), silently swallowed by bare `except Exception: pass`. Fixed to `pdfplumber.open(io.BytesIO(page_obj.parent.tobytes()))` and added logged warnings, turning 0 detected tables into 220 tables detected across 29 documents.
  - Sourced real 62-document test corpus from MIT-licensed `jsvine/pdfplumber` test suite, populated `production/benchmark-dataset-real/pdf-corpus/`, and added `PROVENANCE.md` and `LICENSE.txt`.
  - Added regression test suite [`tests/test_table_extraction_regression.py`](tests/test_table_extraction_regression.py) asserting table extraction on `table-curves-example.pdf` and `federal-register-2020-17221.pdf`.
  - Audited and eliminated bare `except Exception: pass` pattern across `src/`, replacing silent swallowing with structured warnings or debug logs.
  - Added typed `EncryptedPDFError` in `src/ingestion/exceptions.py` to handle encrypted PDFs with clear actionable errors instead of raw PyMuPDF `ValueError`.
  - Published real benchmark reports in `production/performance-report/pdf_pipeline_benchmark.json` and `pdf_pipeline_benchmark_raw.json` with 61/62 (98.4%) success rate, replacing quarantined Phase 1 synthetic reports.
  - Corrected Phase 7 import diagnosis: aliased `ResponseVerificationLayer` as `ResponseVerifier` and exposed `CONNECTOR_REGISTRY = ConnectorFactory.REGISTRY`.

- **Formal Verification Baseline:** Added [`STATUS.md`](STATUS.md) detailing verified capabilities, known issues, and quarantined items.
- **16-Phase Roadmap:** Added [`docs/ROADMAP.md`](docs/ROADMAP.md) detailing the step-by-step path to production readiness.
- **Development Log:** Added [`docs/DEVLOG.md`](docs/DEVLOG.md) tracking tasks, findings, and test verification results.
- **Packaging Infrastructure:** Added [`pyproject.toml`](pyproject.toml) supporting PEP 517/621 standards with optional extras (`[ml]`, `[dev]`, `[all]`).
- **Tiered Requirements:** Added [`requirements-core.txt`](requirements-core.txt), [`requirements-ml.txt`](requirements-ml.txt), and [`requirements-dev.txt`](requirements-dev.txt).
- **Automated CI Workflow:** Added [`.github/workflows/ci.yml`](.github/workflows/ci.yml) with Ruff linting, Bandit security scanning, Pip-Audit vulnerability checking, and multi-version Python test matrix.

- **Contributing Guidelines:** Added [`CONTRIBUTING.md`](CONTRIBUTING.md) documenting branch protection rules and CI verification requirements.
- **Lock Files:** Added [`requirements-core.lock.txt`](requirements-core.lock.txt) and [`requirements-ml.lock.txt`](requirements-ml.lock.txt) from clean installs.
- **Infrastructure Requirements:** Added [`requirements-infra.txt`](requirements-infra.txt) isolating optional caching/tracing deps.
- **Architectural History:** Added [`docs/history.md`](docs/history.md) detailing codebase lineage from legacy iterations to unified canonical architecture.
- **Canonical Document Schema:** Added [`src/core/document_state.py`](src/core/document_state.py) implementing Pydantic v2 mathematical schema $D = (P, S, G, R, F, M, T, X, H, E)$ with topological invariants, transition validation, and UEO bridging.
- **Schema Test Suite:** Added [`tests/test_document_state.py`](tests/test_document_state.py) validating invariants, serialization, and transitions.
- **Ingestion Error Hierarchy:** Added typed exception hierarchy in [`src/ingestion/exceptions.py`](src/ingestion/exceptions.py).
- **Magic Byte Sniffer:** Added deep signature sniffing in [`src/ingestion/sniff.py`](src/ingestion/sniff.py) across PDF, Office, audio, and images.
- **Fallback Recovery Parser:** Added non-crashing multi-tier fallback parser in [`src/ingestion/fallback_parser.py`](src/ingestion/fallback_parser.py).
- **Text Loader:** Added dedicated [`src/ingestion/text_loader.py`](src/ingestion/text_loader.py) with structured metadata.
- **Hardening & Workflow Test Suites:** Added [`tests/test_ingestion_hardening.py`](tests/test_ingestion_hardening.py) (24 tests) and [`tests/test_workflows.py`](tests/test_workflows.py) (8 tests).

- **Real-World Ingestion Validation (Phase 7):**
  - Resolved workflow package import chain and added permanent regression test in [`tests/test_workflows_import.py`](tests/test_workflows_import.py) ensuring all four workflows (`IngestWorkflow`, `BatchWorkflow`, `QueryWorkflow`, `ExportWorkflow`) import cleanly together.
  - Resolved `GraphEngine` vs `GraphBuilder` in `src/workflows/ingest_workflow.py`: explicitly wired `self.graph_engine = GraphEngine()` to construct spatial-DAG nodes and edges per Monograph Section 6 while preserving `GraphBuilder` helper.
  - Enabled flexible workflow injection in [`src/workflows/query_workflow.py`](src/workflows/query_workflow.py) supporting both `ingest` and `ingest_workflow` parameter aliases.
  - Populated `char_count` and `word_count` across all document loaders ([`src/ingestion/docx_loader.py`](src/ingestion/docx_loader.py), [`src/ingestion/pdf_loader.py`](src/ingestion/pdf_loader.py), [`src/ingestion/pptx_loader.py`](src/ingestion/pptx_loader.py), [`src/ingestion/xlsx_loader.py`](src/ingestion/xlsx_loader.py), [`src/ingestion/image_loader.py`](src/ingestion/image_loader.py), [`src/ingestion/text_loader.py`](src/ingestion/text_loader.py), [`src/ingestion/speech_loader.py`](src/ingestion/speech_loader.py)), verified across 14 real monograph documents and rich fixtures.
  - Sourced and generated rich multi-format fixtures: [`tests/fixtures/real_research_paper.pdf`](tests/fixtures/real_research_paper.pdf) (14-page native PDF), [`tests/fixtures/real_presentation.pptx`](tests/fixtures/real_presentation.pptx) (multi-slide presentation with structured tables), [`tests/fixtures/real_spreadsheet.xlsx`](tests/fixtures/real_spreadsheet.xlsx) (multi-sheet workbook with formulas and merged headers), and [`tests/fixtures/real_scanned_page.png`](tests/fixtures/real_scanned_page.png).
  - Added real-world ingestion validation test suite in [`tests/test_real_world_ingestion.py`](tests/test_real_world_ingestion.py) verifying 14-page PDF normalization, non-zero character counts, non-scanned detection, full `MasterState` synthesis, and strict rejection of mock benchmark PDFs with `FormatError`.
- **Test Suite Hardening (Phase 6):**
  - Added multi-format ingestion integration test suite [`tests/test_ingest_workflow.py`](tests/test_ingest_workflow.py) with real fixtures across PDF, DOCX, PPTX, XLSX, IMAGE, and TEXT, plus corrupt-file resilience verification.
  - Added CLI test suite [`tests/test_cli.py`](tests/test_cli.py) covering `--help`, configuration parsing, and all CLI subcommands (`ingest`, `query`, `batch`, `export`, `serve`).
  - Added normalization test suite [`tests/test_normalization.py`](tests/test_normalization.py) covering `TextCleaner`, `LayoutDetector`, and `OCREngine` (bringing normalization coverage from 0% to 100%).
  - Added property-based theorem tests in [`tests/test_theorem_properties.py`](tests/test_theorem_properties.py) using Hypothesis to mathematically verify Theorem 6.1 (Spatial DAG Acyclicity), Theorem 6.2 (Kahn Determinism), Theorem 9.1 (1/2-Knapsack Bound), and Monotone Submodular (1 - 1/e) bound.
  - Renamed 6 import-only framework tests (`test_dashboard.py`, `test_dashboard_pages.py`, `test_optimization_framework.py`, `test_validation_framework.py`, `test_benchmarks_framework.py`, `test_security_framework.py`) to honest `*_imports_cleanly` smoke tests and added real behavioral assertions.
  - Resolved weak credibility test stubs in [`tests/test_credibility_cases.py`](tests/test_credibility_cases.py): implemented real spectral graph clustering assertions in `TC-NE-2`, real orchestrator throughput verification in `TC-NE-6`, and honest `@pytest.mark.skip` for `TC-NE-1` and `TC-NE-3` with traceable monograph citations.
  - Hardened `src/workflows/ingest_workflow.py` with typed error handling (`DocumentCorruptError`), dual-access `IngestionWorkflowResult`, and `MasterState` integration.
  - Raised CI coverage gate in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) from 70% to 75%, with total repository coverage reaching 80% across 1,030 passing tests.
- **Core Schema Unification (Phase 5 — AMDI-OS Monograph Section 5.1 & 5.2):**
  - Implemented [`src/core/master_state.py`](src/core/master_state.py) establishing the canonical 10-tuple $D = (P, S, G, R, F, M, T, X, H, E)$ per Section 5.1 of the AMDI-OS Extended Monograph, with explicit `LayerStatus` honesty flags (`is_hardened`, `is_mock`, `is_proposed`) per Appendix E.
  - Implemented `Element` ($E_i = (x_i, y_i, w_i, h_i, p_i, \theta_i, t_i, c_i)$) with modulo angle wrapping into $[0, 2\pi)$ and `PageRepresentation` ($P_i$) with aggregate bounding box computation.
  - Added property-based tests in [`tests/test_master_state_theorems.py`](tests/test_master_state_theorems.py) mathematically verifying Theorem 5.1 (Scale Invariance) and Theorem 5.2 (Metric Validity of Euclidean distance).
  - Migrated [`src/core/orchestrator.py`](src/core/orchestrator.py) to populate and synchronize one canonical `MasterState` per document (`self._doc_state`), maintaining backward compatibility through dynamic property accessors and dual dict/attr access wrappers (`IngestionStats`, `QueryResult`).
  - Added permanent multi-tenant data isolation regression suite in [`tests/test_multitenancy_isolation.py`](tests/test_multitenancy_isolation.py) validating strict isolation across queries, element access, and state retrieval.
  - Added schema versioning and migration framework in [`src/core/schema_migrations.py`](src/core/schema_migrations.py) with test coverage in [`tests/test_schema_migrations.py`](tests/test_schema_migrations.py).
  - Surfaced the monograph's Appendix E layer status honesty matrix in [`STATUS.md`](STATUS.md).
- **Architectural Deduplication (Phase 4):**
  - Consolidated `BoundingBox` into canonical Pydantic model in [`src/models/geometry_object.py`](src/models/geometry_object.py) with positional argument support, tuple conversion, and page normalization.
  - Consolidated `Citation` into canonical Pydantic model in [`src/models/context_object.py`](src/models/context_object.py) with bounding box support and confidence calculation.
  - Consolidated `UniversalExportObject`, `MarkdownExporter`, `JSONExporter`, and `YAMLExporter` into [`src/export/`](src/export/) with static and instance execution methods, UEO layer serialization, and backward-compatible re-exports in `src/ael/`.
  - Consolidated `DocumentObject` into canonical superset Pydantic model in [`src/models/document_object.py`](src/models/document_object.py) with magic byte sniffing, full `DocumentFormat` enum support, dynamic attributes (`extra="allow"`), and migrated all 32 calling modules across `src/` and `tests/`.
  - Synchronized documentation into canonical `Aegis Doc/` directory containing all 14 `.docx` monographs, removing redundant `Aegis/`.
  - Archived pre-rename legacy codebases (`AMDI-legacy`, `MDIE-legacy`, `amdi-os-legacy`) into dedicated orphan branch `archive/legacy-history`.
  - Cataloged remaining lower-risk class duplications in [`docs/known-duplication.md`](docs/known-duplication.md).
- **Pipeline & Loader Hardening:** Hardened `PDFLoader`, `DOCXLoader`, `XLSXLoader`, `PPTXLoader`, `ImageLoader`, `SpeechLoader`, and `IngestionService.ingest` with timeout support and fallback recovery.
- **Workflow & Engine Defensiveness:** Added PageRank centrality scoring in `DocumentGraph` and `GraphEngine`, dynamic `compute_weights` in `AdaptiveFusionEngine` and `FusionEngine`, array dimension flattening in `SemanticEngine`, and safe graph metric handling in `ExportWorkflow`.
- **Connectors Reconciliation:** Reconciled `src/connectors/` as the single canonical agent integration layer; unified sync and async execution paths (`send`, `stream`, `send_ueo`, `query`), and redirected AEL exporter and export workflows to `src/connectors`.
- **Dependency Repair:** Updated [`requirements.txt`](requirements.txt) to include missing runtime packages (`networkx`, `scipy`, `scikit-learn`, `loguru`) and split dependencies into modular tiers.
- **README Restructuring:** Rewrote [`README.md`](README.md) with live CI badge, measured coverage badge (76%), and tiered install instructions.
- **Defensive CLI Logging:** Updated `src/cli.py` with safe logging fallback.
- **Typing Fixes:** Fixed 18 `F821` undefined typing names in `src/` to ensure clean linter passes.
- **Release Documentation:** Annotated [`production/PRODUCTION_RELEASE_CHECKLIST.md`](production/PRODUCTION_RELEASE_CHECKLIST.md) and [`production/release/RELEASE_NOTES_v1.0.0.md`](production/release/RELEASE_NOTES_v1.0.0.md) to indicate development prototype status.
- **License Annotation:** Annotated [`LICENSE`](LICENSE) template noting no commercial licenses have yet been issued.

### Quarantined / Removed
- **Duplicate Connectors:** Deleted obsolete `src/ael/connectors/` tree (8 files).
- **Duplicate Documentation:** Deleted redundant `Aegis Doc/` directory (12 `.docx` files, 4.47 MB), preserving canonical documentation in `Aegis/` and `docs/`.
- **Archived Legacy Trees:** Removed abandoned legacy trees `_archive/AMDI-legacy`, `_archive/MDIE-legacy`, `_archive/amdi-os-legacy` (420 files, ~2.5 MB) from the working tree to eliminate indexer noise; archived permanently in Git history.
- **Broken CI Workflow:** Removed unbuildable `.github/workflows/test.yml` and contaminated `requirements.lock.txt`.
- **Unverified Audits:** Moved self-generated penetration tests and compliance scorecards to `_unverified_archive/security-audit/`.
- **Synthetic Benchmarks:** Moved mock dataset and synthetic accuracy reports to `_unverified_archive/benchmark-dataset-mock/` and `_unverified_archive/performance-report/`.
- **Placeholder Signatures:** Moved mock PGP signatures and certificates to `_unverified_archive/release-signatures/`.
- **Stale Binaries:** Deleted corrupt/placeholder `RELEASE_NOTES_v1.0.0.pdf`.
