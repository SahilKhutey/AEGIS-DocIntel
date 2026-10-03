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

### Changed
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
