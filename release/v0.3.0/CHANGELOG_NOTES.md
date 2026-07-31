## [0.3.0] — 2026-09-30  "Deprecation Cleanup"

### Added
- Continuous drift sweeping: nightly + on PR via `tools/sweep_drift.py`.
- OpenAPI <-> gRPC agreement sweep via `tools/sweep_openapi_sync.py`.
- Audit-chain integrity sweep via `tools/sweep_audit_integrity.py`.
- Dependency CVE sweep via `tools/sweep_dependency_audit.py`.
- Demo-reel schema sweep via `tools/sweep_demo_reel_schema.py`.
- GitHub issue templates (`bug`, `security`).
- `K-*` GitHub labels (deprecation, perf, sdk, ui, obs, stable, policy, research, bot).

### Changed
- `legacy_bridge.py` now emits `FutureWarning` instead of `DeprecationWarning` (louder, IDE-friendly).
- `tests/migration/test_no_legacy_paths.py` runs in **strict mode**.
- `pyproject.toml` version bumped to `0.3.0.dev0`.
- CI nightly cadence for all four sweeps.

### Deprecated
- All `backend.src.*` imports: **removed** (no bridge).
- All `src.amdi.*` imports: warning tier (will be removed in 0.4.0).
- All `amdi.legacy_bridge.*` names: warning tier (will be removed in 0.4.0).

### Fixed
- Citation-card contrast (WCAG 2.2 AA) confirmed in the React UI.
- SDK build CI now triggers on every change to `proto/amdi.proto`.

### Security
- SECURITY.md published with supported versions + contact email.
- pip-audit integrated nightly.
- Audit-chain integrity sweep added.
