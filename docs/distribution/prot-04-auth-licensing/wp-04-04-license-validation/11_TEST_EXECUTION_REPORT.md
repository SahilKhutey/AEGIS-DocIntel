# WP-04.04 Dossier 11: Test Execution Report

**Work Package:** PROT-04.04  
**Title:** Automated Test Execution Report & Regression Verification  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  
**Classification:** Restricted Evaluation Distribution  

---

## 1. Test Execution Metadata

| Parameter | Execution Value |
| :--- | :--- |
| **Execution Date** | 2026-11-14 |
| **Platform** | Windows 11 (AMD64) |
| **Python Runtime** | Python 3.12.10 |
| **Core Libraries** | PyJWT 2.13.0, cryptography 49.0.0, FastAPI 0.115.12, pydantic 2.10.6 |
| **Test Framework** | pytest 9.1.1, pluggy 1.6.0 |
| **Target Branch** | `product_hunt_launch_packaging` |
| **Commit Baseline** | `287f0cf` |

---

## 2. WP-04.04 Dedicated Suite Execution

### Command
```powershell
python -m pytest tests/security/evaluation/test_license_validation_protocol.py -v
```

### Execution Result
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\ASUS\.gemini\antigravity\worktrees\Aegis-DocIntel\product_hunt_launch_packaging
configfile: pyproject.toml
plugins: anyio-4.12.1, hypothesis-6.156.6, langsmith-0.14.4, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO
collected 40 items

tests/security/evaluation/test_license_validation_protocol.py::test_lic_001_issue_valid_license PASSED [  2%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_002_issue_without_admin_permission PASSED [  5%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_003_issue_with_invalid_policy PASSED [  7%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_004_duplicate_idempotency_key PASSED [ 10%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_005_valid_ed25519_signature PASSED [ 12%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_006_modified_payload_rejected PASSED [ 15%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_007_modified_signature_rejected PASSED [ 17%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_008_unsupported_algorithm_rejected PASSED [ 20%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_009_unknown_kid_rejected PASSED [ 22%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_010_missing_issuer_rejected PASSED [ 25%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_011_incorrect_issuer_rejected PASSED [ 27%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_012_incorrect_audience_rejected PASSED [ 30%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_013_missing_expiry_rejected PASSED [ 32%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_014_expired_license_rejected PASSED [ 35%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_015_future_nbf_rejected PASSED [ 37%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_016_invalid_claim_types_rejected PASSED [ 40%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_017_unknown_license_type_rejected PASSED [ 42%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_018_unknown_policy_version_rejected PASSED [ 45%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_019_evaluator_mismatch_against_authoritative_record PASSED [ 47%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_020_tenant_mismatch_against_authoritative_record PASSED [ 50%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_021_device_mismatch_rejected PASSED [ 52%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_022_license_record_absent_in_authoritative_db PASSED [ 55%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_023_license_suspended_in_authoritative_db PASSED [ 57%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_024_license_revoked_in_authoritative_db PASSED [ 60%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_025_device_deactivated_associated_with_license PASSED [ 62%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_026_signing_key_compromised_emergency_invalidation PASSED [ 65%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_027_old_key_in_verify_only_state PASSED [ 67%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_028_old_key_retired_behavior PASSED [ 70%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_029_new_key_after_rotation_signs_and_verifies PASSED [ 72%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_030_revocation_cache_invalidation PASSED [ 75%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_031_fail_closed_on_authority_unavailable PASSED [ 77%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_032_client_clock_moved_backwards PASSED [ 80%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_033_client_clock_moved_forwards PASSED [ 82%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_034_token_controlled_key_url_rejected PASSED [ 85%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_035_oversized_token_rejected PASSED [ 87%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_036_malformed_compact_jws_rejected PASSED [ 90%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_037_private_key_excluded_from_client_bundle PASSED [ 92%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_038_private_key_excluded_from_public_source PASSED [ 95%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_039_raw_token_never_in_logs PASSED [ 97%]
tests/security/evaluation/test_license_validation_protocol.py::test_lic_040_cross_evaluator_license_access_denied PASSED [100%]

============================= 40 passed in 2.70s ==============================
```

---

## 3. Full System Regression Verification

### Command
```powershell
python -m pytest tests/security/evaluation/ tests/test_production_auth.py tests/test_auth_guard.py tests/distribution_security/ demo/tests/ -q
```

### Execution Result
```text
........................................................................ [ 38%]
........................................................................ [ 77%]
...........................................                              [100%]
187 passed in 26.56s
```

### Breakdown of Regression Suite (187 Total Tests)
- **WP-04.04 License Validation Protocol Tests (`LIC-001` - `LIC-040`)**: 40 passed
- **WP-04.03 Device Binding Protocol Tests (`DEV-001` - `DEV-030`)**: 30 passed
- **Evaluation Security Base Tests (`test_activation`, `test_license_validation`, etc.)**: 41 passed
- **Production Authentication Hardening Tests (`tests/test_production_auth.py`)**: 16 passed
- **Authentication Guard Suite (`tests/test_auth_guard.py`)**: 16 passed
- **Distribution Security Verification (`tests/distribution_security/`)**: 23 passed
- **Evaluation Demo Application Tests (`demo/tests/`)**: 21 passed
- **Total Failures / Errors**: **0**
