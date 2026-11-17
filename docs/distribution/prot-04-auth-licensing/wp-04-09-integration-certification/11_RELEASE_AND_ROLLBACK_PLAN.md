# PROT-04.09 — Dossier 11: Release & Rollback Plan

## 1. Scope & Objective

This document defines the production deployment procedure, release verification gates, and emergency rollback procedures for the **AEGIS-DocIntel Protected Demo Edition**.

---

## 2. Release Gates & Staging Workflow

```mermaid
flowchart TD
    G1[Gate 1: Static Cleanliness & Secrets Scan] --> G2[Gate 2: Unit & Operations Test Suites]
    G2 --> G3[Gate 3: Full Integration Protocol (101 Scenarios)]
    G3 --> G4[Gate 4: Distribution Artifact Verification]
    G4 --> G5[Gate 5: Staging Canary Deployment]
    G5 --> G6[Gate 6: Production Cutover & Health Check]
```

### Gate Descriptions
1. **Gate 1: Static Cleanliness & Secrets Scan**
   - Run `npm --prefix web run verify:auth` (must report zero bypasses).
   - Run static regex scan for private keys, tokens, and backend connection strings.
2. **Gate 2: Unit & Operations Test Suites**
   - Execute all unit suites in `tests/security/` (400+ tests passing, 0 failures).
3. **Gate 3: Full Integration Protocol**
   - Execute `test_prot_04_09_integration_protocol.py` (all 101 scenarios passing).
4. **Gate 4: Distribution Artifact Verification**
   - Inspect build manifest: ensure zero engine files (`src/core/private_engine/`) in client archive.
5. **Gate 5: Staging Canary Deployment**
   - Deploy gateway to staging; run end-to-end journey tests (`JOURNEY-A` through `JOURNEY-F`).
6. **Gate 6: Production Cutover**
   - Promote to public evaluator gateway cluster with health-check monitoring active.

---

## 3. Emergency Rollback Strategy

If an unexpected regression, availability incident, or security defect is detected post-deployment:

### 3.1 Fast-Rollback Protocol (Zero-Downtime)
1. **Traffic Diversion**:
   - Update DNS / Load Balancer ingress target from current release tag to previous known-good release commit (`edd537f`).
2. **Session Preservation**:
   - In-memory / Redis session tokens remain valid across minor rollbacks due to backward-compatible token schemas.
3. **Revocation Registry Synchronization**:
   - Export the live revocation registry from the active gateway before rollback:
     ```bash
     python -c "from services.evaluation_gateway.revocation import registry; print(registry.get_revoked_set())" > /var/backup/revocations_pre_rollback.json
     ```
   - Load revocations into the rolled-back instance to ensure zero post-release revocations are resurrected.

### 3.2 Rollback Decision Matrix

| Severity | Incident Type | Rollback Trigger Window | Authorization Required |
| :--- | :--- | :--- | :--- |
| **Critical** | Authentication bypass / Secret leak | Immediate (< 5 min) | Security Architect / Incident Lead |
| **High** | Quota tracking failure / Data leakage | < 15 min | Engineering Lead |
| **Medium** | Transient gateway latency / WebSocket glitch | Can fix forward; rollback if unfixed in 1h | Release Engineer |
| **Low** | Cosmetic UI issue in evaluation desktop client | Fix forward in next patch | Triage Team |

---

## 4. Disaster Recovery Validation

The fail-closed non-resurrection disaster recovery rule (verified in `RES-INT-010`) ensures that:
- Restoring historical database backups automatically triggers authoritative revocation reconciliation.
- Any entity revoked after the snapshot timestamp remains strictly revoked.
- Zero resurrected access is mathematically possible.
