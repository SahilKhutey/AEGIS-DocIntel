# PROT-04.08: Security Audit & Operational Telemetry

**Work Package:** PROT-04.08  
**Target:** Structured Audit Telemetry, Zero Credential Exposure & Operational Controls  
**Status:** **IMPLEMENTED & VERIFIED**

---

## 1. Security Audit Architecture

Security telemetry for the Evaluation Gateway is maintained by `SecurityAuditService` (`services/evaluation_gateway/audit.py`).
- **Format:** Append-only JSON Lines (`audit_events.jsonl`).
- **Protection:** Write-only from application runtime; ordinary evaluators cannot edit or clear audit events.
- **Event Scope:**
  - `auth.missing_token`, `auth.failed`
  - `activation.success`, `activation.invalid_code`, `activation.rate_limit_exceeded`, `activation.device_limit_exceeded`
  - `device.deactivated`
  - `session.rotated`, `session.logged_out`, `session.refresh_replay_detected`
  - `license.issued`, `license.expired`, `license.revoked`, `license.revoked_by_admin`
  - `quota.queries_exceeded`, `quota.documents_exceeded`, `quota.comparisons_exceeded`, `quota.rate_limit_exceeded`
  - `entitlement.denied`

---

## 2. Redaction & Credential Sanitization (`AUDIT-003`)

The audit service strictly sanitizes all event payloads prior to persistence or telemetry streaming:

```json
{
  "timestamp": "2026-11-13T04:15:00.123456Z",
  "event_type": "activation.success",
  "status": "SUCCESS",
  "actor_id": "evaluator-primary",
  "license_id": "67a14e9b-0294-4d89-9133-784f1b3c9b71",
  "device_id": "d-847291a4",
  "resource": "gateway",
  "details": {
    "platform": "windows",
    "version": "1.1.0",
    "token": "[REDACTED]",
    "access_token": "[REDACTED]",
    "activation_code": "AEGIS-EVAL-****"
  }
}
```

### Sanitization Rules Verified
- **Raw Bearer Tokens:** Replaced with `[REDACTED]`.
- **JWT Strings:** Matched via regex `eyJ...` and replaced with `[REDACTED_JWT]`.
- **Activation Codes:** Truncated to prefix + `****` or replaced with `[REDACTED]`.
- **Private Keys:** Matched via `-----BEGIN...PRIVATE KEY-----` and replaced with `[REDACTED_PRIVATE_KEY]`.
- **User Document Text / Queries:** Replaced with `[CONTENT_REDACTED]` to preserve evaluator data privacy.

---

## 3. Operational Recovery Procedures

1. **Lost Device / Re-Installation Recovery:**
   - Evaluator contacts `support@aegis-docintel.io` or logs into the web dashboard.
   - Administrator issues device deactivation via `POST /v1/evaluation/device/deactivate`.
   - The device slot is freed; the evaluator re-activates with their existing code.
2. **Compromised License Revocation:**
   - Security administrator issues `POST /v1/evaluation/admin/revoke` with the target `license_id`.
   - The license is appended to `revocation_registry` and synced across all gateway instances.
   - All active sessions are terminated immediately (< 12 ms).
