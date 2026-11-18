# Deployment Security Test Plan & Traceability Matrix

## Acceptance Test Suite (`tests/security/deployment/`)
| Test ID | Test Name | Target Invariant | Result |
|:---|:---|:---|:---:|
| `DEP-TEST-001` | Public Engine Port Scan | 0 public host mappings on engine | **PASS** |
| `DEP-TEST-002` | Direct Engine Request | Rejected without valid HMAC token | **PASS** |
| `DEP-TEST-003` | Evaluator DB Connection | Denied at network boundary | **PASS** |
| `DEP-TEST-004` | Gateway-to-Engine Auth | Authenticated with valid signed context | **PASS** |
| `DEP-TEST-005` | Untrusted Tenant Header | Stripped / overridden by server context | **PASS** |
| `DEP-TEST-006` | DB Role Escalation | DDL blocked for `aegis_app` | **PASS** |
| `DEP-TEST-007` | Staging Credential in Prod | Rejected at gateway & secret manager | **PASS** |
| `DEP-TEST-008` | Secret in Manifest | 0 plaintext secrets in compose manifests | **PASS** |
| `DEP-TEST-009` | Parser Sandboxing | Temp wipe & timeout enforcement | **PASS** |
| `DEP-TEST-010` | LLM Key Inspection | Server-side only; keys never leaked | **PASS** |
| `DEP-TEST-011` | Object Storage Direct Access | Blocked at network boundary | **PASS** |
| `DEP-TEST-012` | Post-Restore Revocation | Revoked licenses remain revoked | **PASS** |
| `DEP-TEST-013` | Database Outage Resilience | Fails closed with 503; no stack trace | **PASS** |
| `DEP-TEST-014` | Worker Crash Recovery | Scratchpad wiped post-crash | **PASS** |
| `DEP-TEST-015` | Health Endpoint Disclosure | Zero IPs, DB URIs, or secrets exposed | **PASS** |
| `DEP-TEST-016` | Unauthorized Internal Traffic | Blocked by network policy | **PASS** |
| `DEP-TEST-017` | Backup Restoration Recovery | RPO & RTO compliant | **PASS** |
| `DEP-TEST-018` | Deployment Rollback | Security & revocation state preserved | **PASS** |
