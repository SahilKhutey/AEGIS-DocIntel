# Changelog

All notable changes to AEGIS-DocIntel are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] — 2026-10-08  "First Patch"

### Fixed
- PII redactor coverage for non-Latin phone formats (#1042)
- Helm chart refuses install without `jwtSecret` (#1043)
- Python 3.13 import compatibility (#1047)
- SDK async example merged (#1044, thanks @contributor)
- pytesseract input argument sanitization (security advisory #1051)

### Documentation
- SLA clarified for partial-outage coverage (#1048)

## [0.3.0] — 2026-09-30  "Deprecation Cleanup"

### Added
- **`tools/sweep_drift.py`** + `tools/deprecation_matrix.json` —
  continuous inventory of legacy imports. Runs nightly and on PR.
- **`tools/sweep_openapi_sync.py`** — guards gRPC ↔ REST agreement.
- **`tools/sweep_audit_integrity.py`** — nightly verifier of the
  hash-chained audit log.
- **`tools/sweep_dependency_audit.py`** — pip-audit-based CVE sweep.
- **`tools/sweep_demo_reel_schema.py`** — fails CI before golden
  trace mismatches when the trace shape changes.
- New GitHub issue templates (`bug`, `security`).
- `K-*` labels for roadmap categories.
- `docs/SLA.md` — uptime and performance promises.
- `docs/DISCLOSURES.md` — security advisory policy.
- `docs/SUPPORT.md` — community + commercial support channels.
- `docs/METRICS.md` — curated Prometheus metrics reference.
- `docs/ANNOUNCEMENTS.md` — release announcement index.
- `docs/BRANCH_STRATEGY.md` — git workflow for humans + bots.
- `docs/RELEASE_CADENCE.md` — schedule + SLAs.
- `docs/MAINTAINER_PLAYBOOK.md` — response times, decision matrix.

### Changed
- `legacy_bridge.py` now emits `FutureWarning` instead of
  `DeprecationWarning` (louder, IDE-friendly).
- `tests/migration/test_no_legacy_paths.py` runs in *strict mode* by
  default — every fragment is an error, not a warning.
- CI nightly cadence for the four sweeps.
- `pyproject.toml` version bumped to `0.3.0.dev0`.

### Deprecated
- All `backend.src.*` imports: **removed** (no bridge).
- All `src.amdi.*` imports: warning tier (removed in 0.4.0).
- All `amdi.legacy_bridge.*` names: warning tier (removed in 0.4.0).

### Fixed
- Existing citation-card contrast improved (WCAG 2.2 AA confirmation).
- SDK build CI now runs on PRs that touch `proto/amdi.proto`.

### Security
- SECURITY.md published with supported versions + contact email.
- `pip-audit` integrated nightly.

## [0.2.0] — 2026-07-01  "Mathematical Operating System"

### Added
- Async ingestion pipeline: arq + Redis + SSE progress (Deliverable B).
- Real hybrid 7-method retrieval: BM25 + Dense + RRF + reranker (Deliverable C).
- RAGAS evaluation harness (Deliverable D).
- Canonical module layout migration, import rewire (Deliverable E).
- Multi-language gRPC SDK scaffold from single `.proto` (Deliverable F).
- JWT auth, rate limiting, hash-chained audit log, Prometheus + Grafana (Deliverable G).
- LLMTokenOptimizedExporter with hard token-budget enforcement (Deliverable F5).
- 13-surface dashboard: Streamlit + React (Deliverable H).
- End-to-end demo reel with golden trace CI gate (Deliverable I).
- Release discipline: CHANGELOG, migration guide, release manifest (Deliverable J).

## [0.1.0] — 2026-04-12  "Initial prototype"

### Added
- Initial document ingestion prototype.
- Basic retrieval pipeline.
- FastAPI REST surface.

[Unreleased]: https://github.com/SahilKhutey/AEGIS-DocIntel/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/SahilKhutey/AEGIS-DocIntel/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/SahilKhutey/AEGIS-DocIntel/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/SahilKhutey/AEGIS-DocIntel/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/SahilKhutey/AEGIS-DocIntel/releases/tag/v0.1.0
