# Dependency and Lockfile Policy

**Phase:** PROT-FINAL-04  
**Date:** 2026-11-18T04:20:09.415275+00:00  

---

## 1. Lockfile Governance
- Floating dependency versions in release builds are strictly prohibited.
- `web/package-lock.json` lockfile version 3 is committed to source control.
- Python requirements are synchronized via `scripts/check_dependency_sync.py`.

## 2. License Compliance
All direct and transitive dependencies are screened against commercial open-source allowlists (MIT, Apache-2.0, BSD-2/3-Clause, ISC). Zero copyleft GPL/AGPL libraries exist in the client distribution.
