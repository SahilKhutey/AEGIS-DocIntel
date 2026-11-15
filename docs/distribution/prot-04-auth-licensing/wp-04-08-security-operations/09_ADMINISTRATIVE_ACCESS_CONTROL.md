# PROT-04.08 — Dossier 09: Administrative Access Control & RBAC

## 1. Role-Based Access Control (RBAC) Model
AEGIS-DocIntel enforces strict role boundaries between evaluation users and operational personnel. Administrative and operational capabilities are completely segregated from evaluation credentials.

### Defined Roles:
1. `evaluator`:
   - Allowed: Run evaluation workflows, consume granted quotas, activate bound devices, refresh active sessions.
   - Denied: Administrative routes, internal audit logs, security event queries, key rotation, incident declarations.
2. `security_operator`:
   - Allowed: Inspect tenant security event logs, view active threat alerts, declare incidents, execute containment actions.
   - Denied: Key compromise, root backup restoration, tenant secret modifications.
3. `security_admin`:
   - Allowed: Full access to cryptographic key management, root audit exports, emergency key compromises, system-wide session termination.

---

## 2. API Endpoint Authorization Matrix

| Endpoint Route | HTTP Method | Permitted Roles | Failure Status |
| :--- | :--- | :--- | :--- |
| `/v1/evaluation/session` | `GET` | `evaluator` | `401 Unauthorized` |
| `/v1/evaluation/session/logout` | `POST` | `evaluator` | `401 Unauthorized` |
| `/v1/evaluation/security/health` | `GET` | Public / Evaluator | N/A |
| `/v1/admin/evaluation/security/events` | `GET` | `security_operator`, `security_admin` | `403 Forbidden` |
| `/v1/admin/evaluation/security/audit/export` | `GET` | `security_admin` | `403 Forbidden` |
| `/v1/admin/evaluation/security/audit/verify` | `POST` | `security_operator`, `security_admin` | `403 Forbidden` |
| `/v1/admin/evaluation/security/audit/checkpoint` | `POST` | `security_admin` | `403 Forbidden` |
| `/v1/admin/evaluation/security/alerts` | `GET` | `security_operator`, `security_admin` | `403 Forbidden` |
| `/v1/admin/evaluation/security/incidents` | `POST` / `GET` | `security_operator`, `security_admin` | `403 Forbidden` |
| `/v1/admin/evaluation/security/incidents/{id}/contain` | `POST` | `security_operator`, `security_admin` | `403 Forbidden` |
| `/v1/admin/evaluation/security/incidents/{id}/close` | `POST` | `security_operator`, `security_admin` | `403 Forbidden` |
| `/v1/admin/evaluation/security/keys/rotate` | `POST` | `security_admin` | `403 Forbidden` |
| `/v1/admin/evaluation/security/keys/compromise` | `POST` | `security_admin` | `403 Forbidden` |
| `/v1/admin/evaluation/security/backup/verify` | `POST` | `security_admin` | `403 Forbidden` |
| `/v1/admin/evaluation/security/backup/restore` | `POST` | `security_admin` | `403 Forbidden` |

---

## 3. Enforcement Invariants
1. **Evaluator Rejection (OPS-008)**: Presentation of valid evaluator JWTs or API keys to `/v1/admin/*` routes returns `403 Forbidden` and emits a `CRITICAL` audit event (`MON-011`).
2. **Tenant Scoping (OPS-007)**: Administrative queries for events require an explicit `tenant_id` filter unless executed by root `security_admin`.
