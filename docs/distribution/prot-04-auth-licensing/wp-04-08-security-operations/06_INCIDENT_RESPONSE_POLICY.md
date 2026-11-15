# PROT-04.08 — Dossier 06: Incident Response Policy & Threat Register

## 1. Incident Response Objectives & Legal Basis
The AEGIS Incident Response Policy defines the formal lifecycle for identifying, containing, remediating, and documenting security events impacting evaluation instances, client telemetry, cryptographic keys, or multi-tenant boundaries.

The core policy mandates:
1. **Immediate Automated Containment**: Critical threats trigger deterministic programmatic containment within $< 50\text{ms}$ without waiting for human intervention.
2. **Forensic Evidence Enforcement (IR-008)**: An incident cannot be closed without at least one verifiable forensic evidence attachment.
3. **Fail-Closed Default**: Where ambiguity exists regarding tenant isolation or credential validity, operations default to fail-closed denial.

---

## 2. Canonical Threat Register
The platform defines 10 standardized threat identifiers linked to detection rules and runbooks:

| Threat ID | Threat Name | Impact Level | Associated Runbook |
| :--- | :--- | :--- | :--- |
| `THREAT-SESS-001` | Compromised Evaluator Session | High | `IR-01` |
| `THREAT-KEY-001` | Leakage of Private Signing Key | Critical | `IR-02` |
| `THREAT-API-001` | Gateway API Key Leakage | High | `IR-03` |
| `THREAT-LIC-001` | Commercial License Forgery / Abuse | High | `IR-04` |
| `THREAT-ACT-001` | Activation Code Brute-Force Campaign | Medium | `IR-05` |
| `THREAT-REP-001` | Refresh Token Replay / Interception | Critical | `IR-06` |
| `THREAT-ISO-001` | Cross-Tenant Memory / Data Access | Critical | `IR-07` |
| `THREAT-DATA-001` | Backup Tampering / State Desynchronization | High | `IR-08` |
| `THREAT-AUDIT-001`| Audit Trail Tampering / History Truncation | Critical | `IR-09` |
| `THREAT-DIST-001` | Distribution Package Tampering / Malware Injection | Critical | `IR-10` |

---

## 3. Incident State Machine

```
              +--------------------------+
              |         DECLARED         |
              | (Threat identified/logged|
              +--------------------------+
                           |
                           v
              +--------------------------+
              |        CONTAINED         |
              | (Tokens revoked, IP block|
              +--------------------------+
                           |
                           v
              +--------------------------+
              |     EVIDENCE_PENDING     |
              | (Forensic artifacts added|
              +--------------------------+
                           |
             [Requires Evidence Artifact]
                           v
              +--------------------------+
              |          CLOSED          |
              | (Post-mortem signed off) |
              +--------------------------+
```

### Invariant: Mandatory Forensic Evidence on Close
Attempting to invoke `incident_service.close_incident(incident_id, resolution_notes)` on an incident with zero attached `evidence_ids` raises `ValueError: Cannot close incident without forensic evidence`.

Accepted evidence formats include:
- Cryptographic audit trail exports (`audit-export-*.json`).
- Network packet traces / access logs (`*.pcap`, `access-*.log`).
- Signing key revocation receipts (`receipt-*.json`).
- Memory dump hashes and database reconciliation diffs.
