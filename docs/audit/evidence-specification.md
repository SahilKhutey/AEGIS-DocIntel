# AEGIS-DocIntel — Audit Evidence & Traceability Specification

## Evidence Hierarchy
Audit runs are stored under `artifacts/audits/YYYY/MM/<run_id>/`:
```
artifacts/audits/2026/11/AG-20261103-034841-RQ1E/
├── run.json           # Comprehensive AuditRun entity
├── summary.json       # Consolidated statistical outcome
├── summary.md         # Formatted GitHub Markdown summary
├── provenance.json    # Cryptographic provenance manifest
├── suites/            # Per-suite results (unit.json, security.json, etc.)
├── findings/          # Isolated findings register
└── artifacts/         # Physical output logs, benchmark reports, traces
```

## Traceability Guarantees
- **Run ID**: Standard format `AG-YYYYMMDD-HHMMSS-<RANDOM_4_CHAR>` backed by UUID4.
- **Git State**: Captures full 40-character commit SHA, branch name, detached HEAD status, and clean vs dirty working tree state.
- **Fingerprint Invariance**: Finding fingerprints are calculated omitting line numbers:
  $$F = \text{SHA256}(\text{suite\_id} \parallel \text{rule\_id} \parallel \text{normalized\_file\_path} \parallel \text{normalized\_identity})$$
  Ensures defects are tracked accurately even if source lines shift due to surrounding edits.
- **Historical Comparison**: Compares runs against a common baseline, detecting regressions, resolved defects, and persistent findings.
