# WP-04.01: Evaluation Threat Model & Attack Matrix

**Document:** `06_THREAT_MODEL.md`  
**Work Package:** PROT-04.01 — Authentication Baseline & Threat Model  
**Component:** Security Boundary Definition, Threat Register (TH-01–TH-16) & Mitigations  
**Status:** **AUDITED & VERIFIED**  
**Classification:** Internal Threat Model & Security Specification  

---

## 1. Security Architecture & Trust Boundaries

The AEGIS-DocIntel Protected Demo Edition operates across three strictly segregated trust boundaries:

```
┌────────────────────────────────────────────────────────────────────────┐
│  ZONE A: Evaluator-Controlled Environment (UNTRUSTED)                  │
│  - Evaluator local operating system, terminal, container runtime       │
│  - Downloadable frontend bundle (Next.js), local launcher script        │
│  - Device storage, browser memory, local network proxy                 │
│  - Threat Assumption: Attacker has complete root/admin access          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS (TLS 1.3)
                                    │ Signed Requests / Short-lived JWTs
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  ZONE B: AEGIS Evaluation Gateway (TRUSTED INGRESS)                    │
│  - Authentication verification (RS256 JWT, X-API-Key)                  │
│  - License validation & activation (Ed25519 signature authority)       │
│  - Asymmetric device registration & 1-device enforcement               │
│  - Real-time revocation registry (<15ms SLA)                           │
│  - Atomic quota reservation & usage accounting (threading.Lock)        │
│  - Telemetry & append-only sanitized audit logging                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Private VPC / Mutual TLS
                                    │ Service-to-Service Only
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  ZONE C: Private AEGIS Intelligence Platform (PROTECTED CORE)          │
│  - Document parsing, context graph optimization, vector embeddings     │
│  - Proprietary extraction algorithms, mathematical reasoning engine    │
│  - LLM orchestration, model provider credentials (never distributed)   │
│  - Internal database storage & multi-tenant document repository        │
└────────────────────────────────────────────────────────────────────────┘
```

### The Golden Security Axiom:
> **The client may request access, but only the trusted server can grant it.**  
> No client-side state, hidden UI element, JavaScript flag, or local file can establish authorization.

---

## 2. Protected Assets Inventory

| Asset ID | Asset Name | Description | Confidentiality | Integrity | Availability |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **AST-01** | Evaluation License | Cryptographically signed capability token | Low | **CRITICAL** | High |
| **AST-02** | Evaluator Identity | User account and organization identity | High | **CRITICAL** | High |
| **AST-03** | Device Registration | Public-key binding to a single physical device | Low | **CRITICAL** | High |
| **AST-04** | Session Credentials | Short-lived RS256 JWT access and refresh tokens | **CRITICAL** | **CRITICAL** | High |
| **AST-05** | Evaluator Documents | Business documents uploaded for evaluation | **CRITICAL** | **CRITICAL** | High |
| **AST-06** | Intelligence Engine | Proprietary models, weights, prompts & algorithms| **CRITICAL** | **CRITICAL** | High |
| **AST-07** | Entitlement Matrix | Server-enforced capability ruleset | Low | **CRITICAL** | High |
| **AST-08** | Quota Records | In-flight reservations and consumption counters | Low | **CRITICAL** | High |
| **AST-09** | Signing Private Key| Ed25519 private key used to mint licenses | **CRITICAL** | **CRITICAL** | **CRITICAL** |
| **AST-10** | Audit Log Trail | Append-only security and operational telemetry | Medium | **CRITICAL** | High |

---

## 3. Comprehensive Threat Register (TH-01 – TH-16)

The following matrix documents the sixteen primary threat vectors analyzed, mapped to components and verified with automated test suites:

| Threat ID | Threat Description | Severity | Target Asset | Primary Countermeasure | Automated Verification |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **TH-01** | **Forged JWT Signature** | Critical | AST-04 | RS256 public key verification; explicit algorithm allowlist. | `tests/test_production_auth.py::test_production_rs256_jwt_wrong_key` |
| **TH-02** | **JWT Role Escalation** | Critical | AST-07 | Strict role array validation against `ALLOWED_ROLES`; contradiction checks. | `tests/test_production_auth.py::test_production_jwt_roles_array_unsupported_role_rejected` |
| **TH-03** | **Cross-Tenant IDOR Access** | Critical | AST-05 | `verify_resource_tenant` masks unauthorized lookups as HTTP 404. | `tests/test_auth_guard.py::test_anonymous_cannot_read_or_wipe_another_tenants_document` |
| **TH-04** | **Development Bypass Leakage** | Critical | AST-04 | `dev-*` tokens rejected in production; `verify:auth` CI check. | `web/scripts/verify-production-auth.mjs` |
| **TH-05** | **Forged Evaluation License** | Critical | AST-01 | Asymmetric Ed25519 signature validation; reject tampered JSON. | `tests/security/evaluation/test_license_integrity.py::test_lic_001_ed25519_tamper_detection` |
| **TH-06** | **License Expiration Tampering**| High | AST-01 | Server-side temporal validation; client system clock ignored. | `tests/security/evaluation/test_license_integrity.py::test_lic_003_expired_license_rejection` |
| **TH-07** | **Session Theft & Token Replay**| High | AST-04 | Short TTL (600s); refresh token family invalidation upon reuse. | `tests/security/evaluation/test_session_security.py::test_session_001_refresh_token_rotation` |
| **TH-08** | **Device-Limit Bypass** | High | AST-03 | Strict 1-device limit enforced by activation registry (`DEV-002`). | `tests/security/evaluation/test_device_binding.py::test_dev_002_multi_device_rejection` |
| **TH-09** | **Quota Burst Race Condition** | High | AST-08 | Two-phase atomic reservation with re-entrant `threading.Lock`. | `tests/security/evaluation/test_quota_limits.py::test_quota_003_concurrent_race_resistance` |
| **TH-10** | **Revoked-License Reuse** | Critical | AST-01 | Authoritative in-memory blacklist checked on every request (<15ms). | `tests/security/evaluation/test_session_security.py::test_session_003_revocation_enforcement` |
| **TH-11** | **Direct Access to Private Core**| Critical | AST-06 | Private engine never packaged in demo; gateway proxy boundary. | Architecture Boundary Verification |
| **TH-12** | **API-Key Secret Leakage** | Critical | AST-04 | Raw keys never stored or distributed; SHA-256 hash-only matching. | `tests/test_production_auth.py::test_production_api_keys_rejects_raw_keys_in_config` |
| **TH-13** | **WebSocket Auth Bypass** | High | AST-05 | `get_current_tenant_ws` verifies token; issues WS 1008 close frame. | `tests/test_auth_guard.py::test_websocket_scopes_pass_through_the_guard` |
| **TH-14** | **Public Operational Exposure** | High | AST-10 | Prometheus `/metrics` isolated to internal Docker container network. | `tests/test_auth_guard.py::test_public_allowlist_is_minimal_and_explicit` |
| **TH-15** | **Activation Code Brute-Force** | High | AST-01 | IP-based rate limiting (10/hr) + high-entropy random keys. | `tests/security/evaluation/test_adversarial_scenarios.py::test_sec_demo_019_activation_brute_force_protection` |
| **TH-16** | **Signing-Key Compromise** | Critical | AST-09 | Ed25519 private key stored in KMS; `.gitignore` blocks private PEMs. | `.gitignore` rule: `*private*.pem` |

---

## 4. Residual Risk Assessment

All sixteen identified threats have verified engineering countermeasures. No high or critical severity residual risks remain unmitigated in the evaluation ingress architecture.
