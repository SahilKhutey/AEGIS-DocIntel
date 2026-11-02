# AEGIS-DocIntel — Release Verification & Validation Audit Package

This directory contains the complete, reproducible audit package establishing whether AEGIS-DocIntel is ready for an MVP release.

---

## Directory Layout

```
audit/
├── README.md                           # This document
├── audit-manifest.json                 # Machine-readable execution manifest with hashes
├── release-candidate.json              # Release candidate commit metadata and gate states
├── function_inventory.csv              # Full function-level audit inventory (Function -> Test -> Status)
├── test_matrix.csv                     # Itemized test specifications (ING, NOR, MAT, RET, INT, GOV, JOB, API, UI)
├── benchmark_manifest.json             # Benchmark corpus hashes, thresholds, and commands
├── findings_register.csv               # Audit discrepancies and reconciliation records
│
├── inventory/
│   ├── module-inventory.csv            # Comprehensive inventory of all Python modules
│   ├── function-inventory.csv          # Canonical copy of function inventory
│   ├── api-route-inventory.csv         # All 123 registered REST API operations
│   └── feature-scope-matrix.csv        # MVP inclusion/exclusion scope matrix
│
├── test-specifications/
│   ├── unit-test-matrix.csv            # Canonical unit test specifications
│   ├── integration-test-matrix.csv     # Integration & workflow test specifications
│   ├── security-test-matrix.csv        # Negative security & tenant isolation tests
│   ├── e2e-test-matrix.csv             # End-to-end user journey test specifications
│   └── acceptance-test-matrix.csv      # Gate acceptance criteria
│
├── results/
│   ├── pytest-results.xml              # Pytest XML test run output
│   ├── coverage.xml                    # Cobertura XML code coverage report
│   ├── coverage-summary.json           # Machine-readable coverage metrics by module
│   ├── test-failures.json              # Record of any failed or blocked tests
│   └── regression-results.json         # Performance regression metrics
│
├── benchmarks/
│   ├── benchmark-manifest.json         # Benchmark thresholds and dataset hashes
│   ├── extraction-results.json         # Reading order tau & table cell F1 results
│   ├── retrieval-results.json          # MRR, Recall@5, and abstention benchmark results
│   ├── intelligence-results.json       # Fact extraction F1 & conflict recall results
│   ├── packing-results.json            # Submodular knapsack approximation results
│   └── performance-results.json        # Latency distribution and capacity results
│
├── security/
│   ├── dependency-audit.json           # Pip-audit dependency vulnerability scan results
│   ├── bandit-report.json              # Static application security testing (SAST)
│   ├── secret-scan-summary.json        # Gitleaks / secret scan verification
│   ├── tenant-isolation-results.json   # Multi-tenant IDOR defense verification
│   └── security-findings.csv           # Security finding register (0 unmitigated P0/P1)
│
├── reliability/
│   ├── job-recovery-results.json       # Worker crash & lease recovery results
│   ├── migration-results.json          # Schema migration verification results
│   ├── backup-restore-results.json     # Online SQLite backup & restore recovery drill
│   └── failure-injection-results.json  # Transient network and timeout handling
│
└── final/
    ├── findings-register.csv           # Final findings and reconciliation register
    ├── risk-register.csv               # Project risk register with mitigations
    ├── known-limitations.md            # Documented research boundaries and limitations
    ├── release-verification-report.md  # Comprehensive executive release verification report
    └── release-decision.md             # Formal release determination (GO / NO-GO)
```

---

## Reproducing the Full Audit

To reproduce the complete audit on any system, run:

```bash
python scripts/run_mvp_audit.py
```

To run individual phases:

```bash
python scripts/run_mvp_audit.py --phase 1    # Candidate freeze & git verification
python scripts/run_mvp_audit.py --phase 4    # Coverage and quality gates
python scripts/run_mvp_audit.py --phase 5    # Quality benchmarks & evaluations
python scripts/run_mvp_audit.py --phase 6    # Security and integration workflows
```
