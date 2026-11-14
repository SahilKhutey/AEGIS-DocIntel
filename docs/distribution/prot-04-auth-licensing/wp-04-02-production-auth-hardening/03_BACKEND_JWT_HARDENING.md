# WP-04.02: Backend JWT Validation Hardening & Claim Policy

**Document:** `03_BACKEND_JWT_HARDENING.md`  
**Work Package:** PROT-04.02 — Production Authentication Hardening  
**Target:** PyJWT Decoding Engine, Cryptographic RS256 Verification & Startup Configuration  
**Status:** **AUDITED, HARDENED & VERIFIED**  
**Classification:** Internal Security Implementation Report  

---

## 1. Baseline Deficiencies & Hardening Implementations

Backend token validation (`src/api/auth.py`) was hardened to ensure fail-closed cryptographic security:

### 1.1 Startup Configuration Validation (`validate_production_auth_config`)
In previous revisions, missing public keys or absent configuration was only detected lazily when the first request arrived.
- **Implemented:** `validate_production_auth_config()` executes at application boot.
- If `AEGIS_ENVIRONMENT` is `production` and neither `AEGIS_JWT_PUBLIC_KEY` nor a valid `AEGIS_JWT_PUBLIC_KEY_PATH` is configured, startup fails immediately with `RuntimeError`.
- In strict evaluation mode (`AEGIS_EVALUATION_MODE=true` or `AEGIS_STRICT_JWT_VALIDATION=true`), startup fails if `AEGIS_JWT_ISSUER` or `AEGIS_JWT_AUDIENCE` is missing.

### 1.2 Mandatory Issuer & Audience Enforcement
When operating in strict evaluation mode:
```python
is_strict = (
    os.environ.get("AEGIS_EVALUATION_MODE", "").lower() in ("true", "1", "yes") or
    os.environ.get("AEGIS_STRICT_JWT_VALIDATION", "").lower() in ("true", "1", "yes")
)
if is_strict:
    if not jwt_issuer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Evaluation production requires AEGIS_JWT_ISSUER",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not jwt_audience:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Evaluation production requires AEGIS_JWT_AUDIENCE",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### 1.3 Strict Role Array & Type Boundary Validation
To defend against Finding A03 and role array injection:
- `role` must be a valid string belonging to `ALLOWED_ROLES` (`viewer`, `editor`, `reviewer`, `review_admin`, `tenant_admin`, `platform_admin`, `admin`).
- If `roles` is present in the JWT payload:
  - It must be a non-empty `list`, `tuple`, or `set`. If it is a string or empty array, it is rejected immediately with `HTTP 401 Unauthorized` (`AUTH-H-014`, `AUTH-H-015`).
  - Every single item in `roles` must be a valid string in `ALLOWED_ROLES`.
  - The primary `role` claim must be included in `roles` (preventing contradictory claim injection).

### 1.4 Claim Length & Format Sanity Checks
- `tenant_id` and `sub` are asserted to be non-empty strings stripped of whitespace with a maximum length of 256 characters (`AUTH-H-017`).
- Conflicting `tenant_id` and `tid` claims trigger immediate rejection with HTTP 401.

### 1.5 Generic Error Disclosure
- Low-level PyJWT decode exceptions (e.g. `InvalidTokenError`) return a sanitized generic error to the caller:
  ```python
  raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid authentication credentials",
      headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
  )
  ```
- Detailed trace and reason strings are preserved strictly in the secure append-only audit log.

---

## 2. Test Verification

In `tests/test_production_auth.py`, 19 automated tests verify:
- `test_production_jwt_roles_not_a_list_rejected` (AUTH-H-014) -> **PASSED**
- `test_production_jwt_empty_roles_array_rejected` (AUTH-H-015) -> **PASSED**
- `test_production_jwt_empty_tenant_id_rejected` (AUTH-H-017) -> **PASSED**
- `test_production_auth_config_startup_validation` (AUTH-H-030) -> **PASSED**
- `test_production_rejects_algorithm_confusion_hs256` (AUTH-H-005) -> **PASSED**
- `test_production_jwt_issuer_and_audience` (AUTH-H-010, 011) -> **PASSED**
