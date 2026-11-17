# PROT-04.08 — Dossier 11: Security Operations Test Plan & Verification Matrix

## 1. Scope & Verification Strategy
The WP-04.08 test suite validates all operational security controls, cryptographic hash chaining, threat detection rules, incident containment flows, and distribution packaging safeguards across **44 exhaustive automated test scenarios** in `tests/security/operations/test_security_operations_protocol.py`.

---

## 2. Test Scenario Matrix

| ID | Category | Target Invariant | Expected Outcome |
| :--- | :--- | :--- | :--- |
| `OPS-001` | Event Schema | Valid security event accepted | Stored with schema version 1 |
| `OPS-002` | Event Schema | Invalid severity string rejected | `ValidationError` raised |
| `OPS-003` | Event Catalog | Unknown event type emitted | Auto-assigned `Severity.HIGH` |
| `OPS-004` | Event Schema | Unexpected fields smuggled | `extra="forbid"` raises `ValidationError` |
| `OPS-005` | Redaction | Bearer token / private key in details | Redacted to `[REDACTED_TOKEN]` |
| `OPS-006` | Correlation | Missing request correlation | Auto-generates fallback ID |
| `OPS-007` | Isolation | Cross-tenant audit event query | Blocked; returns empty / error |
| `OPS-008` | Authorization | Evaluator requests internal audit | `PermissionError` / 403 Forbidden |
| `AUDIT-001`| Hash Chain | Append event computes SHA-256 | Valid sequential hash chain |
| `AUDIT-002`| Hash Chain | Verify intact chain | Returns `valid=True` |
| `AUDIT-003`| Tamper Detection | Historical event payload modified | Detected; fails with `HASH_MISMATCH` |
| `AUDIT-004`| Tamper Detection | Historical event deleted | Detected; fails with `HASH_MISMATCH` |
| `AUDIT-005`| Tamper Detection | Historical events reordered | Detected; fails with `HASH_MISMATCH` |
| `AUDIT-006`| Tamper Detection | `previous_hash` altered | Detected; fails with `PREVIOUS_HASH_MISMATCH` |
| `AUDIT-007`| Concurrency | 20 threads append simultaneously | Intact linear chain with 20 items |
| `AUDIT-008`| Checkpoints | External checkpoint signature tampered | Detected; emits `MON-010` critical alert |
| `AUDIT-009`| Append-Only | Update/delete called on audit repo | `PermissionError` strictly raised |
| `AUDIT-010`| Export | Audit export payload generated | Self-contained verifiable package |
| `MON-001` | Threat Engine | >5 activation failures for account | `MON-001` alert dispatched |
| `MON-002` | Threat Engine | >20 activation failures for IP | `MON-002` alert dispatched |
| `MON-003` | Threat Engine | Consumed refresh token replayed | `MON-003` critical alert + family revoked |
| `MON-004` | Threat Engine | Tampered license signature | `MON-004` critical alert dispatched |
| `MON-005` | Threat Engine | >=3 device transfers in 7 days | `MON-005` warning alert dispatched |
| `MON-006` | Threat Engine | Cross-tenant access attempt | `MON-006` critical alert dispatched |
| `MON-007` | Threat Engine | Quota reconciliation mismatch | `MON-007` high alert dispatched |
| `MON-008` | Reliability | Alert delivery sink failure | Logged to retry queue, telemetry emitted |
| `MON-009` | Accuracy | Legitimate activity under thresholds | Zero false positive alerts |
| `MON-010` | Degradation | Monitoring service degraded | Enforces fail-closed behavior |
| `IR-001` | Containment | Revoke compromised evaluator session | Session immediately returns 401 |
| `IR-002` | Containment | Suspend affected license | All protected calls return 403 |
| `IR-003` | Key Rotation | Rotate compromised API key | Old key fails; new key succeeds |
| `IR-004` | Key Rotation | Rotate signing key | Predecessor moves to `VERIFY_ONLY` |
| `IR-005` | Recovery | Restore database backup | Checksum verified prior to restore |
| `IR-006` | Recovery | Non-resurrection rule | Revoked licenses remain revoked |
| `IR-007` | Evidence | Attach forensic evidence to incident | Stored in incident evidence register |
| `IR-008` | Closure Policy | Close incident without evidence | `ValueError` strictly raised |
| `DIST-OPS-001` | Release Security | Scan release for private keys | Zero private keys found |
| `DIST-OPS-002` | Release Security | Scan for development token fallback | Zero dev token fallbacks found |
| `DIST-OPS-003` | Release Security | Scan for backend secrets | Zero secrets in client codebase |
| `DIST-OPS-004` | Release Security | Verify artifact manifest | Checksums match manifest |
| `DIST-OPS-005` | Release Security | Verify SBOM generation | CycloneDX v1.5 compliant |
| `DIST-OPS-006` | Release Security | Verify dependency gate | All dependencies pass audit |
| `DIST-OPS-007` | Release Security | Verify CI permissions | Least-privilege permissions verified |
| `DIST-OPS-008` | Release Security | Verify production config | Debug modes disabled |

---

## 3. Execution Verification
All 44 test scenarios execute and pass cleanly:
```
pytest tests/security/operations/test_security_operations_protocol.py -v
============================= 44 passed in 0.78s ==============================
```
Total security test suite: **400 passed in 39.16s** (100% green).
