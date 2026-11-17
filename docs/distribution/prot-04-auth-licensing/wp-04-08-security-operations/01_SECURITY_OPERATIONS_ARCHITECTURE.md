# PROT-04.08 — Dossier 01: Security Operations Architecture

## 1. Executive Summary & Operational Mission
The **AEGIS-DocIntel Protected Demo Edition** operates within evaluator-controlled, multi-tenant, and potentially hostile client environments. The Security Operations Architecture establishes the authoritative server-side boundary, observability, audit trail immutability, automated threat containment, cryptographic key lifecycle, and disaster recovery procedures.

Security operations ensure that:
1. **Every Security-Relevant Action is Observed & Validated**: All events flow through a strictly validated Pydantic v2 schema with deep automated redaction.
2. **Audit Trails are Cryptographically Non-Repudiable**: An append-only hash chain guarantees $H_i = \text{SHA256}(H_{i-1} \parallel \text{Canonical}(E_i))$ with periodic external Ed25519-signed checkpoints.
3. **Automated Threat Detection Operates in Real Time**: Sliding time-window rules (MON-001 through MON-012) detect brute-force attacks, token replays, key compromises, and cross-tenant access attempts.
4. **Incidents Follow Standardized Containment**: 10 formal operational runbooks (IR-01 through IR-10) govern automated and manual containment actions with mandatory forensic evidence preservation.
5. **Secrets & Keys Follow Strict Lifecycle Controls**: Automated Ed25519 signing key rotation with graceful predecessor verification (`VERIFY_ONLY`) and emergency atomic compromise invalidation.
6. **Disaster Recovery is Fail-Closed**: Authoritative revocation reconciliation prevents the resurrection of revoked licenses, sessions, or devices from restored database snapshots.

---

## 2. Global Security Operations Topology

```
+-----------------------------------------------------------------------------------+
|                        AEGIS-DocIntel Client / Gateway Layer                      |
+-----------------------------------------------------------------------------------+
     |                     |                     |                     |
[Evaluation Client]  [REST Gateway]      [WebSocket Conn]     [Engine Workers]
     |                     |                     |                     |
     +---------------------+---------------------+---------------------+
                           |
                           v
        +-----------------------------------------+
        |   Central Security Event Interceptor    |
        |   - Taxonomy Validation (Catalog)       |
        |   - Strict Pydantic Schema (V1)         |
        |   - Multi-Pattern Secret Redactor       |
        |   - Tenant Context / Correlation Stamp  |
        +-----------------------------------------+
                           |
         +-----------------+-----------------+
         |                                   |
         v                                   v
+------------------------+          +------------------------+
| Append-Only Audit Log  |          | Threat Detection Engine|
| - Sequential Hash Chain|          | - Rules MON-001..012   |
| - Tamper Verification  |          | - Sliding Time Windows |
| - External Checkpoints |          | - Delivery Retries     |
+------------------------+          | - Degraded Fail-Closed |
         |                          +------------------------+
         v                                   |
+------------------------+                   v
| External Verifiers     |          +------------------------+
| & Compliance Regulators|          | Incident Response / IR |
+------------------------+          | - Containment Actions  |
                                    | - Evidence Enforcement |
                                    | - Key Rotation Svc     |
                                    +------------------------+
```

---

## 3. Subsystem Breakdown & Repository Mapping

| Subsystem Component | Repository Path | Functional Responsibility |
| :--- | :--- | :--- |
| **Event Taxonomy & Catalog** | `src/security/event_catalog.py` | Authoritative registry of 36 canonical event types and default severities. |
| **Strict Event Schema** | `src/security/event_schema.py` | Strict Pydantic model (`extra="forbid"`) enforcing schema v1 compliance. |
| **Automated Redactor** | `src/security/event_redaction.py` | Regex and structural redactor removing tokens, keys, passwords, and URIs. |
| **Hash-Chain Integrity** | `src/security/audit_integrity.py` | SHA-256 sequential hashing, canonical serialization, and Ed25519 checkpoints. |
| **Audit Repository** | `src/repositories/security_operations/audit_repository.py` | Append-only store strictly rejecting in-place updates or deletions. |
| **Event Repository** | `src/repositories/security_operations/security_event_repository.py` | Tenant-isolated and role-gated storage for operational security events. |
| **Incident Repository** | `src/repositories/security_operations/incident_repository.py` | Threat registry, incident state machine, and evidence attachment validation. |
| **Key Metadata Repository** | `src/repositories/security_operations/key_metadata_repository.py` | Cryptographic key lifecycle state (`ACTIVE`, `VERIFY_ONLY`, `RETIRED`, `COMPROMISED`). |
| **Event Emission Service** | `src/services/security_operations/security_event_service.py` | Central emission facade coordinating sanitization, indexing, and alerting. |
| **Audit Verification Svc** | `src/services/security_operations/audit_verification_service.py` | Chain auditor, checkpoint anchor, and tamper-evident exporter. |
| **Threat Detection Svc** | `src/services/security_operations/alert_evaluation_service.py` | MON-001..012 sliding-window evaluator with delivery failure management. |
| **Incident Response Svc** | `src/services/security_operations/incident_service.py` | Orchestrates declaration, containment, evidence capture, and closure. |
| **Key Rotation Svc** | `src/services/security_operations/key_rotation_service.py` | Executes scheduled rotations, API key re-issuance, and emergency compromises. |
| **Backup Verification Svc** | `src/services/security_operations/backup_verification_service.py` | Checksum verifier and non-resurrection state reconciliation engine. |

---

## 4. Multi-Tenant Isolation & Least Privilege Invariants
1. **Evaluator Role Denial**: Users possessing only evaluation credentials cannot query internal audit trails or administrative event streams. All queries require `security_operator` or `security_admin` roles.
2. **Tenant Scoping**: All operational events carry a tenant context. Cross-tenant queries are blocked fail-closed; a tenant administrator can only inspect audit records pertaining to their own tenancy.
3. **Immutability of Historical Trails**: The audit log exposes no `update` or `delete` interfaces. Direct repository attempts raise `PermissionError` unconditionally.
