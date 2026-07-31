# Decisions for v0.3.0

- **D-13**: Sweep bots run on a nightly cron and open PRs automatically.
- **D-14**: `legacy_bridge.py` warnings change to `FutureWarning` to better convey timing.
- **D-15**: Add `K-*` labels (`K-deprecation`, `K-perf`, `K-sdk`, `K-ui`, `K-obs`, `K-research`, `K-stable`, `K-policy`).
- **D-16**: Deprecation matrix is now installed at `tools/deprecation_matrix.json` (the sweep bot reads it).
