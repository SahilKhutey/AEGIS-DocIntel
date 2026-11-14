# WP-04.04 Dossier 10: Security Test Plan

**Work Package:** PROT-04.04  
**Title:** Comprehensive Security Test Plan & Verification Matrix  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  
**Classification:** Restricted Evaluation Distribution  

---

## 1. Test Architecture Overview

The WP-04.04 test suite is codified in `tests/security/evaluation/test_license_validation_protocol.py`. It comprises **40 targeted, automated security tests** designed to validate every cryptographic, semantic, administrative, and fault-tolerance boundary of the license validation engine.

---

## 2. Verification Matrix: Scenarios LIC-001 through LIC-040

| Test ID | Category | Severity | Requirement Description | Test Function |
| :--- | :--- | :--- | :--- | :--- |
| **LIC-001** | Issuance | HIGH | Issue valid signed Ed25519 evaluation license | `test_lic_001_issue_valid_license` |
| **LIC-002** | Authorization | CRITICAL | Reject license issuance without admin credentials | `test_lic_002_issue_without_admin_permission` |
| **LIC-003** | Validation | MEDIUM | Reject issuance with invalid policy configuration | `test_lic_003_issue_with_invalid_policy` |
| **LIC-004** | Idempotency | MEDIUM | Duplicate idempotency key returns identical license record | `test_lic_004_duplicate_idempotency_key` |
| **LIC-005** | Cryptography | CRITICAL | Cryptographically valid Ed25519 signature succeeds verification | `test_lic_005_valid_ed25519_signature` |
| **LIC-006** | Anti-Tamper | CRITICAL | Modified JWS payload fails signature verification | `test_lic_006_modified_payload_rejected` |
| **LIC-007** | Anti-Tamper | CRITICAL | Modified signature bytes fails signature verification | `test_lic_007_modified_signature_rejected` |
| **LIC-008** | Algorithm Guard | CRITICAL | Unsupported algorithm (HS256, none) rejected | `test_lic_008_unsupported_algorithm_rejected` |
| **LIC-009** | Key Management | HIGH | Token with unknown kid rejected | `test_lic_009_unknown_kid_rejected` |
| **LIC-010** | Claim Validation | HIGH | Missing issuer claim (iss) rejected | `test_lic_010_missing_issuer_rejected` |
| **LIC-011** | Claim Validation | HIGH | Incorrect issuer claim rejected | `test_lic_011_incorrect_issuer_rejected` |
| **LIC-012** | Claim Validation | HIGH | Incorrect audience claim (aud) rejected | `test_lic_012_incorrect_audience_rejected` |
| **LIC-013** | Claim Validation | HIGH | Missing expiration claim (exp) rejected | `test_lic_013_missing_expiry_rejected` |
| **LIC-014** | Lifecycle | HIGH | Expired license token rejected | `test_lic_014_expired_license_rejected` |
| **LIC-015** | Lifecycle | MEDIUM | Token with future nbf claim rejected | `test_lic_015_future_nbf_rejected` |
| **LIC-016** | Schema Guard | MEDIUM | Invalid claim data types rejected | `test_lic_016_invalid_claim_types_rejected` |
| **LIC-017** | Schema Guard | MEDIUM | Unknown license_type claim rejected | `test_lic_017_unknown_license_type_rejected` |
| **LIC-018** | Schema Guard | MEDIUM | Unknown policy_version claim rejected | `test_lic_018_unknown_policy_version_rejected` |
| **LIC-019** | Authoritative DB | CRITICAL | Evaluator mismatch against authoritative DB rejected | `test_lic_019_evaluator_mismatch_against_authoritative_record` |
| **LIC-020** | Authoritative DB | CRITICAL | Tenant mismatch against authoritative DB rejected | `test_lic_020_tenant_mismatch_against_authoritative_record` |
| **LIC-021** | Device Binding | HIGH | Device ID mismatch rejected | `test_lic_021_device_mismatch_rejected` |
| **LIC-022** | Authoritative DB | CRITICAL | License record absent from authoritative DB rejected | `test_lic_022_license_record_absent_in_authoritative_db` |
| **LIC-023** | Lifecycle | HIGH | Suspended license rejected (HTTP 403) | `test_lic_023_license_suspended_in_authoritative_db` |
| **LIC-024** | Lifecycle | CRITICAL | Revoked license rejected (HTTP 403) | `test_lic_024_license_revoked_in_authoritative_db` |
| **LIC-025** | Device Binding | HIGH | Deactivated device cannot validate license | `test_lic_025_device_deactivated_associated_with_license` |
| **LIC-026** | Incident Response| CRITICAL | Key marked COMPROMISED immediately invalidates tokens | `test_lic_026_signing_key_compromised_emergency_invalidation` |
| **LIC-027** | Key Lifecycle | MEDIUM | Key in VERIFY_ONLY verifies existing tokens but cannot sign | `test_lic_027_old_key_in_verify_only_state` |
| **LIC-028** | Key Lifecycle | HIGH | Retired key rejects validation | `test_lic_028_old_key_retired_behavior` |
| **LIC-029** | Key Rotation | HIGH | New active key signs and verifies successfully after rotation | `test_lic_029_new_key_after_rotation_signs_and_verifies` |
| **LIC-030** | Revocation | HIGH | Revocation immediately clears cached license validity | `test_lic_030_revocation_cache_invalidation` |
| **LIC-031** | Fault Tolerance | CRITICAL | Fail-closed behavior when authoritative DB is unreachable | `test_lic_031_fail_closed_on_authority_unavailable` |
| **LIC-032** | Anti-Replay | MEDIUM | Client clock rollback detected and handled safely | `test_lic_032_client_clock_moved_backwards` |
| **LIC-033** | Lifecycle | LOW | Client clock skew into future handled safely by server | `test_lic_033_client_clock_moved_forwards` |
| **LIC-034** | Input Validation | CRITICAL | Token-controlled key URLs (jku, x5u) strictly rejected | `test_lic_034_token_controlled_key_url_rejected` |
| **LIC-035** | DoS Prevention | MEDIUM | Oversized token (>8KB) rejected immediately | `test_lic_035_oversized_token_rejected` |
| **LIC-036** | Input Validation | MEDIUM | Malformed compact JWS rejected cleanly | `test_lic_036_malformed_compact_jws_rejected` |
| **LIC-037** | IP Protection | CRITICAL | Private signing key strictly excluded from client demo package | `test_lic_037_private_key_excluded_from_client_bundle` |
| **LIC-038** | IP Protection | CRITICAL | Private signing key strictly excluded from public repository | `test_lic_038_private_key_excluded_from_public_source` |
| **LIC-039** | Privacy | HIGH | Raw license tokens never logged into application logs | `test_lic_039_raw_token_never_in_logs` |
| **LIC-040** | Authorization | HIGH | Cross-evaluator license access rejected (HTTP 403) | `test_lic_040_cross_evaluator_license_access_denied` |

---

## 3. Automated Execution Suite Command

```powershell
python -m pytest tests/security/evaluation/test_license_validation_protocol.py -v
```
