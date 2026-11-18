# Database Architecture & Tenant Isolation (DEP-04)

## Logical Database Domains
1. **Identity:** `identity_evaluators`, `identity_sessions`.
2. **Evaluation:** `evaluation_licenses`, `evaluation_devices`.
3. **Authorization:** `authorization_entitlements`.
4. **Usage:** `usage_quota_counters`, `usage_reservations`.
5. **Documents:** `documents_metadata`, `processing_jobs`.
6. **Security:** `security_audit_events` (tamper-evident SHA-256 hash chained).

## Mandatory Query Scoping
All repository queries parameterize tenant identity:
```sql
SELECT * FROM documents_metadata WHERE id = :document_id AND tenant_id = :authenticated_tenant_id;
```

## Role Privilege Separation
- `aegis_app`: Least-privilege runtime role (SELECT, INSERT, UPDATE, DELETE). DDL operations (DROP, ALTER, CREATE) are explicitly denied (`DEP-TEST-006`).
- `aegis_migration`: Pipeline role for schema versioning.
- `aegis_readonly`: SELECT-only for compliance and security auditing.
