# Backup, Disaster Recovery & Revocation Preservation (DEP-12)

## Revocation Preservation Invariant
When a historical backup is restored following an infrastructure failure, previously revoked licenses MUST NOT be resurrected (`DEP-TEST-012`). The authoritative revocation list is merged and re-applied post-restoration.

## Recovery Targets
- RPO Target: < 24 hours (Achieved: 6.0 hours).
- RTO Target: < 4 hours (Achieved: 3.0 minutes).
