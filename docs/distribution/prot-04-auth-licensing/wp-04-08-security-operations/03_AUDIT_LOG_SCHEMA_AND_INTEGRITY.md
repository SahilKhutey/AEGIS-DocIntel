# PROT-04.08 — Dossier 03: Cryptographic Audit Log Schema & Integrity

## 1. Cryptographic Hash-Chaining Invariant
To guarantee that historical evaluation audit logs cannot be modified, reordered, truncated, or forged by compromised processes or malicious operators, the system implements sequential cryptographic hash chaining.

### Mathematical Formulation
The genesis block hash is defined as:
$$H_0 = \text{SHA256}(\text{"AEGIS-AUDIT-GENESIS-2026-v1"})$$

For each subsequent event $E_i$ ($i \ge 1$), the entry hash $H_i$ is computed sequentially:
$$H_i = \text{SHA256}\Big(H_{i-1} \;\parallel\; \text{Canonical}\big(\text{StripEnvelope}(E_i)\big)\Big)$$

Where:
- $\parallel$ denotes byte-level concatenation.
- $\text{StripEnvelope}(E_i)$ removes envelope metadata fields (`previous_hash`, `current_hash`, `entry_id`) prior to hashing, ensuring that the hash reflects the pure payload content.
- $\text{Canonical}(D)$ produces deterministic JSON serialization with lexicographically sorted keys, compact separators `(",", ":")`, and UTF-8 encoding without whitespace.

```
+---------------------------------------------------------------------------------+
|                                 Genesis Block                                   |
| Hash: e4d2... (SHA-256("AEGIS-AUDIT-GENESIS-2026-v1"))                          |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| Entry 1: AUTH_SUCCESS                                                           |
| Previous Hash: e4d2...                                                          |
| Current Hash:  8a1f... = SHA256(Previous Hash || Canonical(EventData))          |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| Entry 2: ACTIVATION_SUCCESS                                                     |
| Previous Hash: 8a1f...                                                          |
| Current Hash:  c39b... = SHA256(Previous Hash || Canonical(EventData))          |
+---------------------------------------------------------------------------------+
```

---

## 2. External Checkpoint Anchoring
To prevent an attacker from rewriting the entire chain from scratch (history rewrite attack), the system anchors periodic checkpoints signed by the evaluation platform's Ed25519 signing key.

### Checkpoint Structure:
```json
{
  "checkpoint_id": "chk-0001",
  "timestamp": "2026-03-01T12:00:00Z",
  "chain_length": 1420,
  "head_hash": "c39b4f2...",
  "key_id": "aegis-license-ed25519-2026-01",
  "signature": "base64(Ed25519_Sign(head_hash || chain_length || timestamp))"
}
```

Checkpoints are exported to external append-only storage sinks (e.g., S3 Object Lock, external audit SIEM, or signed witness logs). During audit verification, if `current_head_hash` diverges from the latest registered checkpoint, a `CRITICAL` alert (`MON-010`) is triggered and the audit repository locks.

---

## 3. Tamper Detection Capabilities & SLA
The cryptographic verification engine (`AuditVerificationService`) detects all four classes of tampering with mathematical certainty:

| Attack Vector | Detection Mechanism | Error Code | SLA |
| :--- | :--- | :--- | :--- |
| **Historical Modification** | $H_k \ne \text{SHA256}(H_{k-1} \parallel \text{Canonical}(E_k'))$ | `HASH_MISMATCH` | Immediate ($< 5\text{ms}$) |
| **Event Deletion** | Hash chain discontinuity at removed entry index $k$. | `HASH_MISMATCH` | Immediate ($< 5\text{ms}$) |
| **Event Reordering** | Swapped positions alter sequential prefix inputs. | `HASH_MISMATCH` | Immediate ($< 5\text{ms}$) |
| **History Truncation** | Discrepancy with signed external checkpoint. | `EXTERNAL_CHECKPOINT_MISMATCH` | Immediate ($< 10\text{ms}$) |

---

## 4. Redaction & Data Leakage Prevention
Audit logs must never become an exfiltration conduit for evaluator credentials. `src/security/event_redaction.py` implements structural and regular-expression sanitization across all emitted event dictionaries:

1. **Bearer Tokens**: `Bearer [A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_.-]+` $\to$ `Bearer [REDACTED_TOKEN]`
2. **Private Keys**: `-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----` $\to$ `[REDACTED_PRIVATE_KEY]`
3. **Database Credentials**: `(?:postgres|mysql|mongodb)://[^:]+:([^@]+)@` $\to$ password redacted.
4. **Targeted Field Masking**: Keys matching `authorization`, `cookie`, `secret`, `private_key`, `token`, `password` are replaced with `[REDACTED]`.
