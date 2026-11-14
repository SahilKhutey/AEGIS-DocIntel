# WP-04.04 Dossier 02: License Claim Specification

**Work Package:** PROT-04.04  
**Title:** Evaluation License Claim Specification & Semantic Validation Rules  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  
**Classification:** Restricted Evaluation Distribution  

---

## 1. Overview & Standard Compliance

AEGIS-DocIntel evaluation licenses are modeled on RFC 7519 (JSON Web Token) and RFC 7515 (JSON Web Signature). Every license payload combines mandatory RFC 7519 registered claims with domain-specific evaluation claims that govern access control, multi-tenancy, device binding, and entitlement limits.

The token media type in the JWS header is strictly pinned to:
```json
{
  "typ": "AEGIS-EVALUATION-LICENSE",
  "alg": "EdDSA",
  "kid": "aegis-license-ed25519-2026-01"
}
```

---

## 2. Standard Registered Claims (RFC 7519)

| Claim | Type | Required | Description | Validation Rule |
| :--- | :--- | :--- | :--- | :--- |
| `iss` | `string` | **Yes** | Token Issuer URI / Identifier | Must equal `"aegis-license-authority"`. Any deviation causes immediate rejection (`LIC-010`, `LIC-011`). |
| `aud` | `string` | **Yes** | Intended Audience URI / Identifier | Must equal `"aegis-evaluation-client"`. Any deviation causes immediate rejection (`LIC-012`). |
| `sub` | `string` | **Yes** | Subject (Evaluator Identifier) | Unique evaluator ID (e.g., `"eval_user_123"`). Must match authoritative server record (`LIC-019`). |
| `jti` | `string` | **Yes** | JWT ID (Unique License Identifier) | Unique UUIDv4 string (e.g., `"lic_7f8a9b0c-..."`). Used for revocation and audit lookups. |
| `iat` | `integer` | **Yes** | Issued At timestamp (Unix epoch seconds) | Must be an integer timestamp $\le \text{current\_time}$. |
| `nbf` | `integer` | **Yes** | Not Before timestamp (Unix epoch seconds) | Token is not valid before this time. If $\text{current\_time} < \text{nbf}$, rejected (`LIC-015`). |
| `exp` | `integer` | **Yes** | Expiration timestamp (Unix epoch seconds) | Token expires at this time. If $\text{current\_time} \ge \text{exp}$, rejected (`LIC-013`, `LIC-014`). |

---

## 3. AEGIS Evaluation Domain Claims

| Claim | Type | Required | Description | Validation Rule |
| :--- | :--- | :--- | :--- | :--- |
| `license_type` | `string` | **Yes** | Classification tier of evaluation | Must be one of `["EVALUATION", "COMMERCIAL_PILOT", "ENTERPRISE_TRIAL"]`. Unknown values rejected (`LIC-017`). |
| `policy_version`| `string` | **Yes** | Version of licensing policy schema | Must be one of `["2026-01", "2026-02"]`. Unknown versions rejected (`LIC-018`). |
| `tenant_id` | `string` | **Yes** | Bound tenant isolation ID | Must match the tenant in server-side authoritative record (`LIC-020`). |
| `device_limit` | `integer` | **Yes** | Max concurrent devices permitted | Evaluator demo tier is strictly set to `1` (`LIC-001`). Must be $\ge 1$. |
| `features` | `array[string]`| **Yes** | Allowed capabilities list | Array of granted capability strings (e.g., `["document_ocr", "semantic_search"]`). |
| `quotas` | `object` | **Yes** | Daily / monthly usage caps | Key-value dictionary specifying resource bounds (e.g., `{"documents_per_day": 50}`). |
| `device_id` | `string` | Optional | Specifically bound device ID | When present, evaluated against the requesting device ID (`LIC-021`). |

---

## 4. Canonical Payload Example

```json
{
  "iss": "aegis-license-authority",
  "aud": "aegis-evaluation-client",
  "sub": "evaluator_acme_corp",
  "jti": "lic_9941a87b-4d32-4e0a-bf19-3e0e7a2512f4",
  "iat": 1773619200,
  "nbf": 1773619200,
  "exp": 1774828800,
  "license_type": "EVALUATION",
  "policy_version": "2026-01",
  "tenant_id": "tenant_eval_acme_448",
  "device_limit": 1,
  "features": [
    "document_ingestion",
    "ocr_pipeline",
    "semantic_search",
    "metadata_extraction"
  ],
  "quotas": {
    "documents_per_day": 50,
    "max_file_size_mb": 25,
    "concurrent_jobs": 2
  },
  "device_id": "dev_win11_x64_b89a"
}
```

---

## 5. Type Enforcement & Schema Guard

The validation pipeline enforces strict data types before validating semantics (`LIC-016`):
- `device_limit` must be an integer, not a string or boolean.
- `features` must be a list of strings, not a single string or dictionary.
- `quotas` must be a dictionary with integer limits.
- Timestamps (`iat`, `nbf`, `exp`) must be numeric Unix timestamps, not ISO-8601 strings.

Any type mismatch triggers a `LicenseVerificationError` with a clear explanation, preventing type-confusion attacks.
