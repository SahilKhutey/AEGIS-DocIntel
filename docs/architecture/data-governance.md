# Data Governance & Document Lifecycle Architecture

## 1. Classification & Sensitivity Levels

AEGIS-DocIntel classifies enterprise document assets into four deterministic governance levels:

```
+------------------+---------------------------------------------------------+
| Level            | Description & Policy Defaults                           |
+------------------+---------------------------------------------------------+
| PUBLIC           | Unrestricted distribution; zero redaction required.     |
| INTERNAL         | Organization-wide access; standard retention policies.  |
| CONFIDENTIAL     | Strict tenant-bound access; PII masked during indexing. |
| RESTRICTED       | Regulated data (e.g. HIPAA/GDPR); export locks apply.   |
+------------------+---------------------------------------------------------+
```

---

## 2. Retention Policies & Automated Expiration

Document lifecycles are governed by immutable `RetentionPolicy` contracts:

```python
@dataclass(frozen=True)
class RetentionPolicy:
    policy_id: str
    tenant_id: str
    name: str
    max_age_days: int
    delete_source: bool = True
    delete_derived_data: bool = True
    legal_hold_override: bool = False
```

### Expiration Evaluation
The exact expiry timestamp is derived deterministically:
$$\text{expires\_at} = \text{created\_at} + (\text{max\_age\_days} \times 86400)$$

`RetentionEngine.is_expired()` evaluates whether the document has crossed its expiration boundary. Documents that have not expired cannot be prematurely purged via automated retention pipelines.

---

## 3. Legal Hold Protection

When a document is subject to litigation, audit, or regulatory inquiry, authorized principals (`tenant_admin`, `platform_admin`) place a legal hold lock on the record:

```python
record = RetentionEngine.set_legal_hold(
    record,
    principal_id="legal-officer@tenant.com",
    reason="Pending litigation matter Matter-901",
)
```

### Immutability Guarantees
- Any automated purge or manual deletion attempt against a document under an active legal hold **immediately raises `LegalHoldActiveError`**.
- Deletion is categorically blocked until the hold is explicitly released by an authorized compliance officer.
- Audit records document who placed the hold, the timestamp, and the justification.

---

## 4. Cascading Purge & Audit Verification

When an eligible expired document is purged, `RetentionEngine.execute_purge()` triggers a cascading eradication workflow:

1. **Physical Storage**: Raw bytes removed from SQLite BLOB / S3 bucket.
2. **Derived Indices**: Vector embeddings removed from Milvus collections.
3. **Cache Invalidation**: Redis semantic cache keys and query citations invalidated.
4. **Governance Record**: Updated with `purged_at` timestamp and permanent `purge_audit_id`.
5. **Cryptographic Audit Event**: Emitted via `AuditLogger` with cryptographic hash proof of deletion.
