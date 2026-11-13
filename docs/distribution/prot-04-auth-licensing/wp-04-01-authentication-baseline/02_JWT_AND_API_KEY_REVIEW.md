# WP-04.01: Cryptographic JWT & API-Key Implementation Review

**Document:** `02_JWT_AND_API_KEY_REVIEW.md`  
**Work Package:** PROT-04.01 — Authentication Baseline & Threat Model  
**Component:** Cryptographic Token Decoding, Claim Validation & Service Key Verification  
**Status:** **AUDITED, HARDENED & VERIFIED**  
**Classification:** Internal Security Audit Report  

---

## 1. Cryptographic Standards & Token Architecture

The AEGIS backend authentication subsystem (`src/api/auth.py`) implements JSON Web Token (JWT) verification using PyJWT backed by the Python `cryptography` library.

### 1.1 Asymmetric Algorithm Pinning (RS256)
- **Algorithm Enforcement:** The decode routine strictly enforces `algorithms=["RS256"]`.
- **Key Confusion Defense (CVE-2015-9235):** By hardcoding the RS256 algorithm allowlist, the system prevents symmetric HMAC key-confusion attacks where an attacker signs an HS256 token using the public RSA key as the HMAC secret.
- **Clock Skew Tolerance:** Expiration validation allows a maximum clock-skew leeway of 30 seconds (`leeway=30`).

### 1.2 Public Key Validation & Fail-Closed Loading
- **Configuration Sources:** Loaded from `AEGIS_JWT_PUBLIC_KEY` (raw PEM string) or `AEGIS_JWT_PUBLIC_KEY_PATH` (filesystem path).
- **Type Verification:** The key is deserialized using `cryptography.hazmat.primitives.serialization.load_pem_public_key`. The backend asserts that the loaded key is an instance of `rsa.RSAPublicKey`.
- **Fail-Closed Fallback:** If the key is malformed, missing, or belongs to an incompatible curve/algorithm (e.g. Ed25519 or ECDSA passed as the RSA token key), key initialization fails closed with `RuntimeError` or `HTTPException(401)`.

---

## 2. In-Depth Audit of Findings A01 – A06

During the WP-04.01 baseline source inspection, six distinct findings (A01 through A06) were identified in `src/api/auth.py`. Below is the status, security impact, remediation, and verification for each finding:

### Finding A01: Optional Issuer Validation
- **Severity:** Medium (Low in isolated VPC, High in multi-service mesh)
- **Observation:** In the baseline, `issuer` claim was only validated if `AEGIS_JWT_ISSUER` was defined in the environment.
- **Risk:** Tokens issued by an unintended internal identity provider could be accepted if both services share the same signing certificate authority.
- **Remediation & Evaluation Policy:** In the Evaluation Gateway deployment (`services/evaluation_gateway/`), `AEGIS_JWT_ISSUER` is strictly mandated (`https://auth.aegis-docintel.org`). Tokens missing or mismatched against this issuer are rejected immediately with HTTP 401.

### Finding A02: Optional Audience Validation
- **Severity:** Medium
- **Observation:** `audience` claim was only checked if `AEGIS_JWT_AUDIENCE` was configured.
- **Risk:** A valid JWT issued for a different enterprise microservice could be replayed against AEGIS.
- **Remediation & Evaluation Policy:** The Evaluation Gateway mandates `AEGIS_JWT_AUDIENCE=aegis-evaluation-gateway`. Tokens must explicitly declare this audience.

### Finding A03: `roles` Array Accepted Without Member Validation (Tampering Vulnerability)
- **Severity:** **HIGH** (Role Escalation / Security Context Poisoning)
- **Baseline Flaw:** 
  In the baseline `src/api/auth.py`, the code checked that the singular `role` claim was in `ALLOWED_ROLES`. However, lines 255–257 subsequently executed:
  ```python
  if "roles" in payload and isinstance(payload["roles"], (list, set, tuple)):
      roles = frozenset(payload["roles"])
  ```
  Consequently, if an attacker supplied `{"role": "viewer", "roles": ["viewer", "unauthorized_injected_role"]}`, the invalid role was copied directly into `TenantContext.roles` without individual validation. Furthermore, the singular `role` could contradict the `roles` array (e.g. primary `viewer` with array `["editor"]`).
- **Remediation Applied to `src/api/auth.py`:**
  ```python
  roles = frozenset({"admin", "tenant_admin"}) if role == "admin" else frozenset({role})
  if "roles" in payload and payload["roles"] is not None:
      raw_roles = payload["roles"]
      if not isinstance(raw_roles, (list, set, tuple)) or not raw_roles:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Invalid roles claim format",
              headers={"WWW-Authenticate": "Bearer"},
          )
      if not all(isinstance(r, str) and r in ALLOWED_ROLES for r in raw_roles):
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Unsupported role in roles array",
              headers={"WWW-Authenticate": "Bearer"},
          )
      parsed_roles = set(raw_roles)
      if role == "admin":
          parsed_roles.add("tenant_admin")
      if role not in parsed_roles:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail=f"Primary role '{role}' contradicts roles array",
              headers={"WWW-Authenticate": "Bearer"},
          )
      roles = frozenset(parsed_roles)
  ```
- **Test Verification:**
  - `test_production_jwt_roles_array_unsupported_role_rejected` (PASSED)
  - `test_production_jwt_roles_array_contradictory_primary_role_rejected` (PASSED)

### Finding A04: Role Fallback Behavior
- **Severity:** Medium
- **Observation:** If the singular `role` claim is absent from the JWT, it previously defaulted to `"viewer"`.
- **Risk:** Tokens without explicit authorization grants could gain implicit read access.
- **Evaluation Decision:** In production evaluation tokens, `role` is explicitly encoded and checked. Defaulting is disallowed; missing `role` triggers HTTP 401.

### Finding A05: Alternative Tenant Claim (`tid` vs `tenant_id`)
- **Severity:** Low / Information Integrity
- **Observation:** `src/api/auth.py` permitted either `tenant_id` or `tid` (Azure AD standard). However, if both claims were present with conflicting values, the resolution order created ambiguity.
- **Remediation Applied to `src/api/auth.py`:**
  ```python
  raw_tid = payload.get("tenant_id")
  raw_tid_alt = payload.get("tid")
  if raw_tid and raw_tid_alt and str(raw_tid) != str(raw_tid_alt):
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Conflicting tenant_id and tid claims in token",
          headers={"WWW-Authenticate": "Bearer"},
      )
  tenant_id = raw_tid or raw_tid_alt
  ```
- **Test Verification:**
  - `test_production_jwt_conflicting_tenant_id_and_tid_rejected` (PASSED)

### Finding A06: JWT Error Disclosure
- **Severity:** Low
- **Observation:** Certain PyJWT decode exceptions could expose low-level token parsing internals in HTTP response bodies.
- **Remediation:** In production configuration, all decode failures return sanitized HTTP 401 messages (`"Invalid authentication credentials"` or `"Token has expired"`), while detailed trace information is written exclusively to the secure append-only audit logger (`AEGIS_AUDIT_LOG_PATH`).

---

## 3. API-Key Implementation Audit

AEGIS provides an alternative credential path via the `X-API-Key` HTTP header.

### 3.1 Security Mechanics
1. **SHA-256 Hashing:** Raw API keys are never stored in plain text. Incoming keys are immediately hashed using `hashlib.sha256(key.encode("utf-8")).hexdigest()`.
2. **Hash-Only Configuration:** Production keys are configured via JSON in `AEGIS_API_KEY_HASHES`, mapping SHA-256 digests to tenant and role definitions.
3. **Constant-Time Comparison:** Key lookup uses `hmac.compare_digest()` to prevent timing side-channel attacks during hash matching.
4. **Configuration Safety Enforcement:** `src/api/auth.py` inspects `AEGIS_API_KEY_HASHES` at startup; if any key is shorter than 64 characters or contains non-hexadecimal characters (indicating an unhashed raw secret was placed in config), the server refuses to boot.

### 3.2 Evaluation Distribution Policy
- **CRITICAL RULE:** API keys are strictly intended for trusted server-to-server microservice integrations.
- **Demo Boundary:** No API keys are bundled into the downloadable client package, launcher scripts, or frontend environment variables (`.env.production`). Evaluator sessions use short-lived user tokens only.
