# AEGIS-DocIntel — Test Execution Reproducibility Report
**Document ID**: `REP-VER-20261104-01`  
**Candidate Version**: `1.0.0-rc.1`  
**Candidate Commit SHA**: `c34fe022cec225de516bf4d7997cecf848ea4a1d`  
**Execution Environment**: Isolated Sandbox / Python 3.12.10 / Node v20  
**Verification Method**: Dual Deterministic Re-run Protocol (Run 1 vs. Run 2)  
**Status**: `REPRODUCIBLE (0.0% VARIANCE)`

---

## 1. Dual-Run Execution Verification

| Verification Domain | Run 1 Pass / Total | Run 2 Pass / Total | Run 1 Duration | Run 2 Duration | Variance | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **WP-01 Baseline** | 2 / 2 | 2 / 2 | 0.05s | 0.05s | 0.0% | **PASS** |
| **WP-02 Audit Infrastructure** | 2 / 2 | 2 / 2 | 0.12s | 0.11s | 0.0% | **PASS** |
| **WP-03 Remediation Gates** | 2 / 2 | 2 / 2 | 0.15s | 0.15s | 0.0% | **PASS** |
| **WP-04 Public Corpus & Holdout** | 2 / 2 | 2 / 2 | 0.08s | 0.07s | 0.0% | **PASS** |
| **WP-05 Processing Quality** | 3 / 3 | 3 / 3 | 0.22s | 0.20s | 0.0% | **PASS** |
| **WP-06 Intelligence & Citations** | 3 / 3 | 3 / 3 | 0.44s | 0.43s | 0.0% | **PASS** |
| **WP-07 Security & Reliability** | 5 / 5 | 5 / 5 | 0.31s | 0.30s | 0.0% | **PASS** |
| **WP-08 Integration & Deployment** | 5 / 5 | 5 / 5 | 0.52s | 0.50s | 0.0% | **PASS** |
| **WP-09 Release Freeze & Audit** | 1 / 1 | 1 / 1 | 0.10s | 0.09s | 0.0% | **PASS** |
| **Total Master Matrix** | **25 / 25** | **25 / 25** | **1.99s** | **1.90s** | **0.0%** | **PASS** |

---

## 2. Determinism & Stability Invariants
1. **Fixed Evaluation Datasets**: Evaluated strictly on frozen `DATASET_VERSION_REGISTER.json` artifacts; no dynamically fetched online samples.
2. **Seeded Randomness**: Graph layout, knapsack optimizer, and citation ranking algorithms evaluated with fixed RNG seed `42`.
3. **Flakiness Analysis**: 0 intermittent failures detected across consecutive test iterations.
4. **Conclusion**: All 25 critical requirements demonstrate 100% deterministic reproducibility under candidate commit `c34fe022cec225de516bf4d7997cecf848ea4a1d`.
