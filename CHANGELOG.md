# Changelog

All notable changes to the AEGIS-DocIntel project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0-alpha.1] - October 2026

### Added
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
