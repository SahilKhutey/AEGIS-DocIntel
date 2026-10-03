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

### Changed
- **Dependency Repair:** Updated [`requirements.txt`](requirements.txt) to include missing runtime packages (`scikit-learn`, `structlog`, `bcrypt`, `passlib`, `python-jose`, `prometheus-client`, `pytest-asyncio`).
- **README Restructuring:** Rewrote [`README.md`](README.md) to replace unverified marketing claims with honest badges (`Status: Alpha / Experimental`, `Tests: 944_passing_(local)`), an alert disclaimer, and clear positioning as a Pre-LLM Context Compiler.
- **Release Documentation:** Annotated [`production/PRODUCTION_RELEASE_CHECKLIST.md`](production/PRODUCTION_RELEASE_CHECKLIST.md) and [`production/release/RELEASE_NOTES_v1.0.0.md`](production/release/RELEASE_NOTES_v1.0.0.md) to indicate development prototype status.
- **License Annotation:** Annotated [`LICENSE`](LICENSE) template noting no commercial licenses have yet been issued.

### Quarantined / Removed
- **Unverified Audits:** Moved self-generated penetration tests and compliance scorecards to `_unverified_archive/security-audit/`.
- **Synthetic Benchmarks:** Moved mock dataset and synthetic accuracy reports to `_unverified_archive/benchmark-dataset-mock/` and `_unverified_archive/performance-report/`.
- **Placeholder Signatures:** Moved mock PGP signatures and certificates to `_unverified_archive/release-signatures/`.
- **Stale Binaries:** Deleted corrupt/placeholder `RELEASE_NOTES_v1.0.0.pdf`.
