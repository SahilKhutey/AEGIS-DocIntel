# AEGIS-DocIntel — Branch Comparison Report
**Baseline ID**: AEGIS-BASELINE-001  
**Generated Date**: 2026-11-03  

## 1. Executive Summary
This report analyzes canonical branch alignment between `master` and `main`, as well as divergent development branches, specifically `feature/v0.3.0-full-production-hardening`.

## 2. Canonical Branches: `master` vs `main`
- **master HEAD SHA**: `7c05522643e503396795d99e381d201268ebe7fe`
- **main HEAD SHA**: `7c05522643e503396795d99e381d201268ebe7fe`
- **Diff Analysis (`git diff master..main`)**: Exactly 0 lines difference.
- **Status**: **IDENTICAL / ZERO-DIFF ALIGNED**.
- **Historical Note**: Prior notes referenced commit `2a0ce4c`. Both branches progressed through `e72ae0c`, `04527de`, `fdb4122`, `32dfcb9` to `7c05522`.

## 3. Divergent Branch Analysis: `origin/feature/v0.3.0-full-production-hardening`
A diff between `master` and `origin/feature/v0.3.0-full-production-hardening` reveals 12 divergent commits:
1. `883e761` — feat(acceptance): deliver Final Acceptance Checklist, Test Matrix, e2e suites, and verify_everything.py runner
2. `7d7e0de` — fix(tests): resolve remaining import references and rate limiter isolation in test suite
3. `5111fbf` — docs(readme): update badges and clean up legacy backend/ directory paths
4. `4887b01` — refactor(cleanup): remove legacy pre-migration src/ modules (archived to _archive/src_legacy)
5. `c1bf688` — test(ops,retrieval,api): add migration, ops, retrieval and security test suites
6. `70b3bde` — ci(github): add workflow automation for nightly sweeps, announcements, issue triage and RC releases
7. `0d07eca` — feat(release): add v0.3.0 release manifests, press announcements and week-1 patch governance
8. `1847280` — docs(ops): add SLA, security disclosures, support guidelines, maintainer playbook, roadmap and architectural analysis
9. `7280dff` — feat(tools): add sweep bots for drift, openapi, audit-chain integrity and CVE scanning
10. `9aeb109` — feat(ui): update frontend dashboards for 13 real surfaces across Streamlit and React
11. `627d8f4` — feat(eval,sdk,infra): add evaluation benchmark harness, multi-language gRPC SDKs, Helm chart and ops monitoring
12. `ed94525` — refactor(core): migrate layout to canonical src/amdi package and PEP 621 build config

### Architectural Decision & Governance
- **Mandate**: Do NOT wholesale-merge `feature/v0.3.0-full-production-hardening` into the baseline.
- **Justification**: The `v0.3.0` branch introduced widespread refactoring (such as renaming `src` to `src/amdi`), sweeping multi-surface UI changes, and packaging shifts that alter the verified module interfaces of MVP 0-8. Wholesale merging would introduce severe regressions into the established MVP test contracts.
- **Resolution**: Preserve `origin/feature/v0.3.0-full-production-hardening` as an isolated remote branch for selective, cherry-picked feature inspection in subsequent work packages.
