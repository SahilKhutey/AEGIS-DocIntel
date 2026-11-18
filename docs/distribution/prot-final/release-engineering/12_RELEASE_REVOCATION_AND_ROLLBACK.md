# Release Revocation and Rollback Safeguards

**Phase:** PROT-FINAL-04  
**Service Implementation:** `services/evaluation_gateway/release_policy.py`  
**Date:** 2026-11-18T04:20:09.415275+00:00  

---

## 1. Server-Side Client Release Policy
The evaluation gateway maintains an authoritative release policy:
```json
{
  "minimum_supported_version": "1.0.0",
  "blocked_versions": [],
  "release_channel": "evaluation",
  "policy_revision": 1
}
```
During session activation and API requests, the client version (`X-Client-Version`) is evaluated. Compromised or superseded versions are rejected with `HTTP 403 Forbidden` (`CLIENT_VERSION_BLOCKED` or `CLIENT_VERSION_UNSUPPORTED`).

## 2. Rollback Safeguards
Rollback procedures guarantee that reverting software can never:
- Reactivate revoked evaluation licenses.
- Restore terminated evaluator session families.
- Re-enable compromised signing keys.
- Reset quota consumption tallies.
