# WP-04.03 Dossier 09: Security Test Plan

**Work Package:** PROT-04.03  
**Title:** Comprehensive Security Test Plan & Traceability Matrix (DEV-001 to DEV-030)  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  

---

## 1. Test Methodology & Framework

The security verification framework executes under `pytest` with deterministic cryptographic harnesses, asynchronous concurrency executors (`concurrent.futures`), and clean test isolation fixtures (`clean_evaluation_environment`).

### Test Suite Location:
`tests/security/evaluation/test_device_binding_protocol.py`

---

## 2. Security Test Traceability Matrix (DEV-001 through DEV-030)

| Test ID | Test Function Name | Objective & Scenario | Expected HTTP / Outcome |
| :--- | :--- | :--- | :--- |
| **DEV-001** | `test_dev_001_stage1_challenge_creation_ed25519` | Valid code & Ed25519 PEM key generates challenge | `HTTP 200 OK` + canonical message |
| **DEV-002** | `test_dev_002_atomic_one_device_limit_enforcement` | Second device on same evaluation code rejected | `HTTP 409 DEVICE_LIMIT_EXCEEDED` |
| **DEV-003** | `test_dev_003_session_revocation_on_device_deactivation` | Sessions terminated immediately on device deactivation | `HTTP 401 UNAUTHORIZED` |
| **DEV-004** | `test_dev_004_deactivation_frees_device_slot_for_replacement` | Deactivated device slot can be claimed by new machine | `HTTP 200 OK` (active) |
| **DEV-005** | `test_dev_005_challenge_rejected_invalid_activation_code` | Bogus code rejected at Stage 1 | `HTTP 400 INVALID_ACTIVATION_CODE` |
| **DEV-006** | `test_dev_006_challenge_rejected_malformed_public_key` | Unparseable public key rejected | `HTTP 400 MALFORMED_PUBLIC_KEY` |
| **DEV-007** | `test_dev_007_activation_rejected_invalid_signature` | Corrupt or wrong-key signature rejected | `HTTP 401 INVALID_DEVICE_SIGNATURE` |
| **DEV-008** | `test_dev_008_activation_rejected_tampered_canonical_message` | Modified challenge payload rejected | `HTTP 401 INVALID_DEVICE_SIGNATURE` |
| **DEV-009** | `test_dev_009_challenge_expiry_rejected` | Challenge submitted after TTL rejected | `HTTP 400 CHALLENGE_EXPIRED` |
| **DEV-010** | `test_dev_010_challenge_single_use_replay_prevention` | Replayed challenge submission rejected | `HTTP 400 CHALLENGE_ALREADY_CONSUMED` |
| **DEV-011** | `test_dev_011_activation_nonexistent_challenge_id` | Unknown UUID challenge rejected | `HTTP 404 CHALLENGE_NOT_FOUND` |
| **DEV-012** | `test_dev_012_installation_id_mismatch_rejected` | Differing installation ID rejected | `HTTP 400 INSTALLATION_MISMATCH` |
| **DEV-013** | `test_dev_013_activation_rsa_2048_key` | RSA-2048 key activation verified | `HTTP 200 OK` (algorithm="RSA") |
| **DEV-014** | `test_dev_014_activation_ed25519_raw_base64_key` | Ed25519 raw 32-byte key verified | `HTTP 200 OK` (algorithm="Ed25519") |
| **DEV-015** | `test_dev_015_key_fingerprint_deterministic_and_unique` | Key fingerprint collision resistance | Deterministic SHA-256 match |
| **DEV-016** | `test_dev_016_idempotent_reactivation_same_device` | Same device re-binding refreshes session | `HTTP 200 OK` (no quota violation) |
| **DEV-017** | `test_dev_017_devices_listing_endpoint` | Evaluator lists own registered devices | `HTTP 200 OK` (contains device) |
| **DEV-018** | `test_dev_018_device_detail_endpoint` | Evaluator reads own device details | `HTTP 200 OK` (metadata matches) |
| **DEV-019** | `test_dev_019_cross_license_device_isolation` | Evaluator B blocked from Evaluator A device | `HTTP 404 NOT FOUND` |
| **DEV-020** | `test_dev_020_emergency_recovery_with_valid_code` | Emergency code deactivates lost device | `HTTP 200 OK` + slot freed |
| **DEV-021** | `test_dev_021_emergency_recovery_rejected_invalid_code` | Wrong recovery code rejected | `HTTP 401 RECOVERY_FAILED` |
| **DEV-022** | `test_dev_022_device_heartbeat_updates_timestamp` | Active device sends heartbeat | `HTTP 200 OK` (alive) |
| **DEV-023** | `test_dev_023_heartbeat_rejected_on_deactivated_device` | Deactivated device heartbeat fails | `HTTP 401 DEVICE_INACTIVE` |
| **DEV-024** | `test_dev_024_challenge_rate_limiting` | 11 rapid requests from 1 IP blocked | `HTTP 429 RATE_LIMIT_EXCEEDED` |
| **DEV-025** | `test_dev_025_hmac_lookup_never_leaks_or_stores_raw_codes` | Code privacy in memory and logs | Zero raw codes in keys/logs |
| **DEV-026** | `test_dev_026_concurrent_activation_race_condition` | 10 concurrent threads compete for 1 slot | Exactly 1 success (200), 9 conflicts (409) |
| **DEV-027** | `test_dev_027_idempotent_or_safe_duplicate_deactivation` | Repeated deactivation handled cleanly | `HTTP 200` or safe termination |
| **DEV-028** | `test_dev_028_empty_or_whitespace_activation_code_rejected` | Empty/whitespace code validation | `HTTP 400 INVALID_ACTIVATION_CODE` |
| **DEV-029** | `test_dev_029_tampered_signature_payload_byte_modification` | Bit-flipped signature rejected | `HTTP 401 INVALID_DEVICE_SIGNATURE` |
| **DEV-030** | `test_dev_030_complete_evaluation_lifecycle_end_to_end` | E2E challenge -> signature -> query -> recover | `HTTP 200 OK` at each valid step |
