# Dossier 09: Session Security Test Plan & Coverage

**Work Package:** PROT-04.07  
**Module:** `AEGIS-DocIntel Automated Verification Protocols`  
**Test Suite:** `tests/security/evaluation/test_session_lifecycle_protocol.py`  
**Status:** **PASSED / CERTIFIED & SIGNED OFF**

---

## 1. Test Matrix (42 Scenarios)

| Scenario ID | Test Function | Description | Result |
| :--- | :--- | :--- | :--- |
| **SESSION-001** | `test_session_001_direct_activation_creates_active_session` | Direct activation produces active session & family | **PASSED** |
| **SESSION-002** | `test_session_002_two_stage_device_challenge_activation_creates_session` | Two-stage challenge binds session to device & license | **PASSED** |
| **SESSION-003** | `test_session_003_access_and_refresh_token_ttl_specifications` | 600s access token TTL & 7-day absolute limit | **PASSED** |
| **SESSION-004** | `test_session_004_raw_refresh_token_never_persisted_at_rest` | Only SHA-256 digests exist at rest | **PASSED** |
| **SESSION-005** | `test_session_005_isolated_tenant_binding_enforced` | Session bound to isolated tenant sandbox | **PASSED** |
| **SESSION-006** | `test_session_006_session_creation_emits_audit_telemetry` | `session.created` audit record logged | **PASSED** |
| **SESSION-007** | `test_session_007_valid_active_session_returns_context` | Valid session returns 200 OK & evaluator identity | **PASSED** |
| **SESSION-008** | `test_session_008_unregistered_access_token_rejected_401` | Forged access token returns 401 INVALID_SESSION | **PASSED** |
| **SESSION-009** | `test_session_009_validation_slides_idle_expiration` | Validation slides idle expiration forward | **PASSED** |
| **SESSION-010** | `test_session_010_idle_timeout_rejected` | Inactive session exceeding 30 min fails | **PASSED** |
| **SESSION-011** | `test_session_011_absolute_timeout_rejected` | Session exceeding 7 days fails validation | **PASSED** |
| **SESSION-012** | `test_session_012_session_expiry_sweeper_transitions_expired_sessions` | Sweeper marks timed-out sessions as EXPIRED | **PASSED** |
| **SESSION-013** | `test_session_013_refresh_returns_new_access_and_refresh_tokens` | Refresh returns new access & refresh tokens | **PASSED** |
| **SESSION-014** | `test_session_014_rotated_token_marked_consumed` | Old token marked CONSUMED with timestamp | **PASSED** |
| **SESSION-015** | `test_session_015_replaced_token_links_to_new_token_id` | Consumed token links to replacement ID | **PASSED** |
| **SESSION-016** | `test_session_016_token_family_lineage_preserved` | Token family ID maintained across rotations | **PASSED** |
| **SESSION-017** | `test_session_017_new_access_token_allows_api_access` | Rotated access token authorizes API requests | **PASSED** |
| **SESSION-018** | `test_session_018_refresh_emits_audit_telemetry` | `session.refreshed` audit event recorded | **PASSED** |
| **SESSION-019** | `test_session_019_consumed_refresh_token_replay_rejected_401` | Replaying consumed token returns 401 | **PASSED** |
| **SESSION-020** | `test_session_020_replay_revokes_parent_session` | Replay immediately revokes parent session | **PASSED** |
| **SESSION-021** | `test_session_021_replay_revokes_all_sessions_in_family` | Replay revokes ALL sessions in token family | **PASSED** |
| **SESSION-022** | `test_session_022_replay_revokes_all_refresh_tokens_in_family` | Replay revokes all active refresh tokens in family | **PASSED** |
| **SESSION-023** | `test_session_023_new_access_token_invalidated_after_replay` | Access token issued before replay is invalidated | **PASSED** |
| **SESSION-024** | `test_session_024_high_severity_replay_audit_event_logged` | `COMPROMISE_DETECTED` audit record emitted | **PASSED** |
| **SESSION-025** | `test_session_025_20_competing_threads_atomic_refresh_race` | 20 threads racing: exactly 1 succeeds, 19 fail | **PASSED** |
| **SESSION-026** | `test_session_026_concurrency_race_does_not_split_token_families` | Concurrency race produces no split branches | **PASSED** |
| **SESSION-027** | `test_session_027_repository_atomic_conditional_rotation_thread_safety` | Atomic status transition thread safety | **PASSED** |
| **SESSION-028** | `test_session_028_concurrent_session_validation_and_refresh_thread_safety` | Concurrent validation & refresh without error | **PASSED** |
| **SESSION-029** | `test_session_029_concurrent_logout_and_api_calls_fail_closed` | Concurrent logout & API calls fail closed | **PASSED** |
| **SESSION-030** | `test_session_030_high_volume_read_write_stability` | 100 concurrent read/write ops without corruption | **PASSED** |
| **SESSION-031** | `test_session_031_logout_terminates_single_session` | Logout invalidates calling session token | **PASSED** |
| **SESSION-032** | `test_session_032_logout_all_terminates_all_evaluator_sessions` | Logout-all terminates all evaluator sessions | **PASSED** |
| **SESSION-033** | `test_session_033_device_deactivation_cascades_to_sessions` | Device deactivation terminates device sessions | **PASSED** |
| **SESSION-034** | `test_session_034_license_revocation_sla_under_50ms` | License revocation terminates sessions (SLA < 50ms) | **PASSED** |
| **SESSION-035** | `test_session_035_refresh_with_host_cookie_sets_secure_cookie` | `__Host-` cookie attributes verified | **PASSED** |
| **SESSION-036** | `test_session_036_logout_clears_host_cookie` | Logout clears `__Host-` cookie | **PASSED** |
| **SESSION-037** | `test_session_037_hostile_cors_origin_rejected_403` | Hostile CORS origin rejected with 403 | **PASSED** |
| **SESSION-038** | `test_session_038_csrf_token_mismatch_rejected_403` | CSRF token mismatch rejected with 403 | **PASSED** |
| **SESSION-039** | `test_session_039_websocket_ticket_issuance_and_consumption` | Single-use 60s ticket issued and consumed | **PASSED** |
| **SESSION-040** | `test_session_040_websocket_ticket_replay_and_expiry_prevention` | Ticket replay rejected (TICKET_ALREADY_CONSUMED) | **PASSED** |
| **SESSION-041** | `test_session_041_background_job_retains_context_and_revalidates` | Background job retains context & revalidates | **PASSED** |
| **SESSION-042** | `test_session_042_background_job_aborts_on_mid_execution_revocation` | Mid-job revocation aborts worker immediately | **PASSED** |
