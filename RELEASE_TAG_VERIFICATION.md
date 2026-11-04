# AEGIS-DocIntel — Release Tag Verification (WP-09.06)
**Document ID**: `TAG-VER-20261104-01`  
**Target Release Tag**: `v1.0.0-rc.1`  
**Approved Commit SHA**: `c34fe022cec225de516bf4d7997cecf848ea4a1d`  
**Verification Status**: `CANDIDATE COMMIT VERIFIED`

---

## 1. Commit Verification Procedure
Prior to applying the git release tag, the release automation verifies:
1. `git rev-parse HEAD` equals approved candidate commit `c34fe022cec225de516bf4d7997cecf848ea4a1d`.
2. Working tree status is tracked and conforms to release freeze.
3. Checksums in `release/audit/checksums.sha256` match all release artifacts.

---

## 2. Release Tagging Commands
Upon final authorization:
```bash
git tag -a v1.0.0-rc.1 -m "AEGIS-DocIntel MVP Release Candidate 1" c34fe022cec225de516bf4d7997cecf848ea4a1d
git push origin v1.0.0-rc.1
```

---

## 3. Verification Confirmation
The candidate commit SHA `c34fe022cec225de516bf4d7997cecf848ea4a1d` is verified identical across:
- `RELEASE_CANDIDATE_MANIFEST.json`
- `FINAL_VERIFICATION_MATRIX.csv`
- `COMPLETE_VERIFICATION_REPORT.json`
- `REQUIREMENTS_TRACEABILITY.csv`
- `REVIEWER_SIGNOFF.md`
- `RELEASE_DECISION.md`
- `RELEASE_DECISION.json`
