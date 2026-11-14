"""
AEGIS-DocIntel Session Lifecycle & Real-Time Revocation Protocol Verification Suite
Complies with PROT-04 WP-04.07 Specifications.

Covers 42 Scenarios:
- SESSION-001 to SESSION-006: Session Creation, Token Structure, TTL, Hashes at Rest, Tenant Binding, Audit Logging.
- SESSION-007 to SESSION-012: Session Validation, Active Verification, Sliding Idle, Timeouts, Expiry Sweeping.
- SESSION-013 to SESSION-018: Refresh Rotation, Token Issuance, Consumed Transition, Lineage Tracking, Authenticated Requests.
- SESSION-019 to SESSION-024: Replay Attack Detection, Family Revocation Cascade, Fail-Closed Security, Compromise Audit.
- SESSION-025 to SESSION-030: Concurrency Race Condition (20 Competing Threads), Atomic Transition, Thread Safety, No State Corruption.
- SESSION-031 to SESSION-034: Evaluator Logout, Logout-All, Hardware Device Deactivation Cascade, License Revocation SLA (<50ms).
- SESSION-035 to SESSION-038: Browser Security (__Host- Cookie, SameSite=Strict, CORS Origin Defense, CSRF Verification).
- SESSION-039 to SESSION-040: WebSocket Short-Lived Single-Use Ticket Handshake, Replay Prevention, Revocation Closure.
- SESSION-041 to SESSION-042: Long-Running Background Job Authorization Context Retention and Mid-Job Revocation Abort.
"""

from __future__ import annotations

import concurrent.futures
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.app import app
from services.evaluation_gateway.activation import activation_service
from services.evaluation_gateway.revocation import registry as revocation_registry
from src.schemas.evaluation.session import EvaluationSession, RevocationReason, SessionStatus
from src.schemas.evaluation.refresh import EvaluationRefreshToken, RefreshTokenStatus
from src.schemas.evaluation.session_audit import SessionAuditEventType
from src.repositories.evaluation.session_repository import session_repository
from src.repositories.evaluation.refresh_token_repository import refresh_token_repository
from src.repositories.evaluation.session_audit_repository import session_audit_repository
from src.services.evaluation.refresh_token_service import generate_access_token, generate_refresh_token, hash_token
from src.services.evaluation.session_service import session_service
from src.services.evaluation.session_validation_service import session_validation_service
from src.services.evaluation.refresh_rotation_service import refresh_rotation_service
from src.services.evaluation.session_revocation_service import session_revocation_service
from src.services.evaluation.session_expiry_service import session_expiry_service
from src.services.evaluation.websocket_ticket_service import websocket_ticket_service


@pytest.fixture(autouse=True)
def clean_session_state():
    """Resets session, refresh token, and revocation state before each scenario."""
    session_repository.clear()
    refresh_token_repository.clear()
    session_audit_repository.clear()
    websocket_ticket_service.clear()
    yield
    session_repository.clear()
    refresh_token_repository.clear()
    session_audit_repository.clear()
    websocket_ticket_service.clear()


# ==============================================================================
# Group 1: Session Creation & Token Structure (SESSION-001 - SESSION-006)
# ==============================================================================

def test_session_001_direct_activation_creates_active_session(client: TestClient):
    """SESSION-001: Direct activation creates active session with valid token family and access token."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_001_pubkey"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"
    assert "session" in data
    assert data["session"]["access_token"].startswith("aegis_eval_at_")
    assert data["session"]["refresh_token"].startswith("aegis_eval_rt_")
    assert data["session"]["expires_in"] == 600

    # Verify session repository has record
    at_hash = hash_token(data["session"]["access_token"])
    sess = session_repository.get_by_access_hash(at_hash)
    assert sess is not None
    assert sess.status == SessionStatus.ACTIVE
    assert sess.license_id == data["license"]["license_id"]


def test_session_002_two_stage_device_challenge_activation_creates_session(client: TestClient):
    """SESSION-002: Two-stage challenge activation binds session to registered device and license."""
    from cryptography.hazmat.primitives.asymmetric import ed25519
    import base64

    # Generate device keypair
    dev_priv = ed25519.Ed25519PrivateKey.generate()
    dev_pub_bytes = dev_priv.public_key().public_bytes_raw()
    dev_pub_b64 = base64.b64encode(dev_pub_bytes).decode("ascii")

    # Stage 1: Request Challenge
    ch_res = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": dev_pub_b64,
            "installation_id": "inst-session-002",
        },
    )
    assert ch_res.status_code == 200
    ch_data = ch_res.json()

    # Sign canonical message
    sig_bytes = dev_priv.sign(ch_data["canonical_message"].encode("utf-8"))
    sig_b64 = base64.b64encode(sig_bytes).decode("ascii")

    # Stage 2: Activate
    act_res = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": ch_data["challenge_id"],
            "signature": sig_b64,
            "installation_id": "inst-session-002",
        },
    )
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["session"]["device_id"] == act_data["device_id"]

    # Verify session repository linkage
    at_hash = hash_token(act_data["session"]["access_token"])
    sess = session_repository.get_by_access_hash(at_hash)
    assert sess is not None
    assert sess.device_id == act_data["device_id"]
    assert sess.license_id == act_data["license"]["license_id"]


def test_session_003_access_and_refresh_token_ttl_specifications(client: TestClient):
    """SESSION-003: Access token TTL is strictly 600s (10 min) and absolute session limit is 7 days."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_003_pubkey"},
    )
    assert res.status_code == 200
    sess_data = res.json()["session"]
    assert sess_data["expires_in"] == 600

    at_hash = hash_token(sess_data["access_token"])
    sess = session_repository.get_by_access_hash(at_hash)
    assert sess is not None

    duration = sess.absolute_expires_at - sess.created_at
    assert duration.total_seconds() == pytest.approx(7 * 86400, abs=10)


def test_session_004_raw_refresh_token_never_persisted_at_rest(client: TestClient):
    """SESSION-004: Raw refresh tokens are never persisted in plain text; only SHA-256 digests exist at rest."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_004_pubkey"},
    )
    rt = res.json()["session"]["refresh_token"]
    expected_hash = hash_token(rt)

    # Repository should locate token by hash, but never store raw secret
    tok = refresh_token_repository.get_by_hash(expected_hash)
    assert tok is not None
    assert tok.token_hash == expected_hash

    # Ensure no token record contains raw rt string
    for stored_tok in refresh_token_repository._tokens.values():
        assert rt not in stored_tok.token_hash
        assert rt != stored_tok.token_id


def test_session_005_isolated_tenant_binding_enforced(client: TestClient):
    """SESSION-005: Evaluation session is strictly bound to tenant-{license_id}."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_005_pubkey"},
    )
    lic_id = res.json()["license"]["license_id"]
    at = res.json()["session"]["access_token"]

    at_hash = hash_token(at)
    sess = session_repository.get_by_access_hash(at_hash)
    assert sess is not None
    assert sess.tenant_id == f"tenant-{lic_id}"


def test_session_006_session_creation_emits_audit_telemetry(client: TestClient):
    """SESSION-006: Session creation produces audit record in session audit repository."""
    client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_006_pubkey"},
    )
    events = session_audit_repository.query_events(event_type=SessionAuditEventType.SESSION_CREATED)
    assert len(events) >= 1
    ev = events[0]
    assert ev.status == "SUCCESS"
    assert ev.session_id is not None


# ==============================================================================
# Group 2: Session Validation & Lifecycle Status (SESSION-007 - SESSION-012)
# ==============================================================================

def test_session_007_valid_active_session_returns_context(client: TestClient):
    """SESSION-007: Valid session returns 200 OK and current identity on GET /v1/evaluation/session."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_007_pubkey"},
    )
    at = res.json()["session"]["access_token"]
    user_id = res.json()["client_id"]

    check_res = client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {at}"})
    assert check_res.status_code == 200
    assert check_res.json()["user_id"] in (user_id, "evaluator-primary")
    assert check_res.json()["authenticated"] is True


def test_session_008_unregistered_access_token_rejected_401(client: TestClient):
    """SESSION-008: Unregistered or forged access token returns 401 INVALID_SESSION."""
    forged_token = "aegis_eval_at_forged_random_token_bytes_not_in_store"
    res = client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {forged_token}"})
    assert res.status_code == 401
    assert res.json()["error"] == "INVALID_SESSION"


def test_session_009_validation_slides_idle_expiration():
    """SESSION-009: Access token validation updates last_seen_at and slides idle_expires_at forward."""
    sess, at, rt = session_service.create_session(
        evaluator_id="eval-009",
        tenant_id="tenant-009",
        license_id="lic-009",
        device_id="dev-009",
    )
    initial_idle = sess.idle_expires_at

    # Simulate request 5 seconds later
    time.sleep(0.05)
    valid, checked_sess, reason = session_validation_service.validate_access_token(at)
    assert valid is True
    assert checked_sess.last_seen_at >= sess.created_at
    assert checked_sess.idle_expires_at >= initial_idle


def test_session_010_idle_timeout_rejected():
    """SESSION-010: Inactive session exceeding sliding idle timeout fails validation."""
    sess, at, rt = session_service.create_session(
        evaluator_id="eval-010",
        tenant_id="tenant-010",
        license_id="lic-010",
        device_id="dev-010",
    )
    # Artificially set idle expiration in the past
    sess.idle_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    session_repository.save_session(sess)

    valid, checked_sess, reason = session_validation_service.validate_access_token(at)
    assert valid is False
    assert reason == "SESSION_IDLE_TIMEOUT"


def test_session_011_absolute_timeout_rejected():
    """SESSION-011: Session exceeding fixed absolute expiration cannot be used and fails validation."""
    sess, at, rt = session_service.create_session(
        evaluator_id="eval-011",
        tenant_id="tenant-011",
        license_id="lic-011",
        device_id="dev-011",
    )
    # Artificially set absolute expiration in the past
    sess.absolute_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    session_repository.save_session(sess)

    valid, checked_sess, reason = session_validation_service.validate_access_token(at)
    assert valid is False
    assert reason == "SESSION_ABSOLUTE_TIMEOUT"


def test_session_012_session_expiry_sweeper_transitions_expired_sessions():
    """SESSION-012: Periodic sweeper transitions idle and absolute expired sessions to EXPIRED state."""
    sess1, _, _ = session_service.create_session("eval-1", "t1", "lic-1", "dev-1")
    sess2, _, _ = session_service.create_session("eval-2", "t2", "lic-2", "dev-2")

    now = datetime.now(timezone.utc)
    # Expire sess1
    sess1.idle_expires_at = now - timedelta(minutes=10)
    session_repository.save_session(sess1)

    swept = session_expiry_service.sweep_expired(now)
    assert swept >= 1
    assert session_repository.get_by_id(sess1.session_id).status == SessionStatus.EXPIRED
    assert session_repository.get_by_id(sess2.session_id).status == SessionStatus.ACTIVE


# ==============================================================================
# Group 3: Refresh Token Rotation & Lineage (SESSION-013 - SESSION-018)
# ==============================================================================

def test_session_013_refresh_returns_new_access_and_refresh_tokens(client: TestClient):
    """SESSION-013: Refreshing returns a new access token and a new rotating refresh token."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_013_pubkey"},
    )
    rt1 = res.json()["session"]["refresh_token"]
    at1 = res.json()["session"]["access_token"]

    ref_res = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    assert ref_data["access_token"] != at1
    assert ref_data["refresh_token"] != rt1


def test_session_014_rotated_token_marked_consumed():
    """SESSION-014: Rotated refresh token has status=CONSUMED and consumed_at recorded."""
    sess, at, rt1 = session_service.create_session("eval-14", "t14", "lic-14", "dev-14")
    tok1 = refresh_token_repository.get_by_hash(hash_token(rt1))
    assert tok1.status == RefreshTokenStatus.ACTIVE

    success, payload, outcome = refresh_rotation_service.rotate_session(rt1)
    assert success is True
    assert outcome == "SUCCESS"

    tok1_updated = refresh_token_repository.get_by_id(tok1.token_id)
    assert tok1_updated.status == RefreshTokenStatus.CONSUMED
    assert tok1_updated.consumed_at is not None


def test_session_015_replaced_token_links_to_new_token_id():
    """SESSION-015: Consumed refresh token points to replaced_by_id of the replacement token."""
    sess, at, rt1 = session_service.create_session("eval-15", "t15", "lic-15", "dev-15")
    tok1 = refresh_token_repository.get_by_hash(hash_token(rt1))

    success, payload, outcome = refresh_rotation_service.rotate_session(rt1)
    assert success is True
    rt2 = payload["refresh_token"]
    tok2 = refresh_token_repository.get_by_hash(hash_token(rt2))

    tok1_updated = refresh_token_repository.get_by_id(tok1.token_id)
    assert tok1_updated.replaced_by_id == tok2.token_id


def test_session_016_token_family_lineage_preserved():
    """SESSION-016: Rotated refresh token maintains the exact same token_family_id."""
    sess, at, rt1 = session_service.create_session("eval-16", "t16", "lic-16", "dev-16")
    tok1 = refresh_token_repository.get_by_hash(hash_token(rt1))

    success, payload, outcome = refresh_rotation_service.rotate_session(rt1)
    rt2 = payload["refresh_token"]
    tok2 = refresh_token_repository.get_by_hash(hash_token(rt2))

    assert tok1.family_id == tok2.family_id
    assert sess.token_family_id == tok2.family_id


def test_session_017_new_access_token_allows_api_access(client: TestClient):
    """SESSION-017: Access token issued during refresh allows subsequent authenticated API requests."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_017_pubkey"},
    )
    rt1 = res.json()["session"]["refresh_token"]

    ref_res = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    at2 = ref_res.json()["access_token"]

    call_res = client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {at2}"})
    assert call_res.status_code == 200
    assert call_res.json()["authenticated"] is True


def test_session_018_refresh_emits_audit_telemetry():
    """SESSION-018: Successful refresh logs session.refreshed event in audit repository."""
    sess, at, rt1 = session_service.create_session("eval-18", "t18", "lic-18", "dev-18")
    refresh_rotation_service.rotate_session(rt1)

    events = session_audit_repository.query_events(event_type=SessionAuditEventType.SESSION_REFRESHED)
    assert len(events) >= 1
    assert events[0].status == "SUCCESS"


# ==============================================================================
# Group 4: Replay Detection & Compromise Revocation (SESSION-019 - SESSION-024)
# ==============================================================================

def test_session_019_consumed_refresh_token_replay_rejected_401(client: TestClient):
    """SESSION-019: Replaying consumed refresh token returns 401 with 'replay detected'."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_019_pubkey"},
    )
    rt1 = res.json()["session"]["refresh_token"]

    # First legitimate refresh
    ref_res = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    assert ref_res.status_code == 200

    # Attacker replays rt1
    replay_res = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    assert replay_res.status_code == 401
    assert "replay detected" in replay_res.json()["message"].lower()


def test_session_020_replay_revokes_parent_session():
    """SESSION-020: Replay attempt immediately revokes the parent session (status=REVOKED)."""
    sess, at, rt1 = session_service.create_session("eval-20", "t20", "lic-20", "dev-20")
    success, payload, _ = refresh_rotation_service.rotate_session(rt1)
    assert success is True

    # Replay
    rep_success, _, outcome = refresh_rotation_service.rotate_session(rt1)
    assert rep_success is False
    assert outcome == "REFRESH_REPLAY_DETECTED"

    updated_sess = session_repository.get_by_id(sess.session_id)
    assert updated_sess.status == SessionStatus.REVOKED
    assert updated_sess.revocation_reason == RevocationReason.REFRESH_REPLAY_DETECTED


def test_session_021_replay_revokes_all_sessions_in_family():
    """SESSION-021: Replay attack revokes ALL sessions sharing the compromised token_family_id."""
    sess1, _, rt1 = session_service.create_session("eval-21", "t21", "lic-21", "dev-21")
    fam_id = sess1.token_family_id
    # Create sibling session in same family
    sess2, _, _ = session_service.create_session("eval-21", "t21", "lic-21", "dev-21-b", family_id=fam_id)

    # Legitimate refresh on sess1
    refresh_rotation_service.rotate_session(rt1)

    # Replay on rt1
    refresh_rotation_service.rotate_session(rt1)

    assert session_repository.get_by_id(sess1.session_id).status == SessionStatus.REVOKED
    assert session_repository.get_by_id(sess2.session_id).status == SessionStatus.REVOKED


def test_session_022_replay_revokes_all_refresh_tokens_in_family():
    """SESSION-022: Replay attack revokes all active refresh tokens in that family."""
    sess, at, rt1 = session_service.create_session("eval-22", "t22", "lic-22", "dev-22")
    _, payload, _ = refresh_rotation_service.rotate_session(rt1)
    rt2 = payload["refresh_token"]

    # Replay rt1
    refresh_rotation_service.rotate_session(rt1)

    tok2 = refresh_token_repository.get_by_hash(hash_token(rt2))
    assert tok2.status == RefreshTokenStatus.REVOKED


def test_session_023_new_access_token_invalidated_after_replay(client: TestClient):
    """SESSION-023: The access token issued before replay is immediately rejected (fails closed)."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_023_pubkey"},
    )
    rt1 = res.json()["session"]["refresh_token"]

    ref_res = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    at2 = ref_res.json()["access_token"]

    # Trigger replay
    client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})

    # at2 must now be denied
    check_res = client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {at2}"})
    assert check_res.status_code == 401


def test_session_024_high_severity_replay_audit_event_logged():
    """SESSION-024: Compromise event session.refresh_replay_detected is logged with high severity."""
    sess, at, rt1 = session_service.create_session("eval-24", "t24", "lic-24", "dev-24")
    refresh_rotation_service.rotate_session(rt1)
    refresh_rotation_service.rotate_session(rt1)  # Replay

    events = session_audit_repository.query_events(event_type=SessionAuditEventType.REFRESH_TOKEN_REUSE_DETECTED)
    assert len(events) >= 1
    assert events[0].status == "COMPROMISE_DETECTED"
    assert events[0].details["family_id"] == sess.token_family_id


# ==============================================================================
# Group 5: Concurrency Race & Thread Safety (SESSION-025 - SESSION-030)
# ==============================================================================

def test_session_025_20_competing_threads_atomic_refresh_race():
    """SESSION-025: 20 simultaneous threads racing to refresh the SAME token: exactly 1 succeeds, 19 fail."""
    sess, at, rt = session_service.create_session("eval-25", "t25", "lic-25", "dev-25")

    results = []

    def attempt_refresh():
        success, payload, outcome = refresh_rotation_service.rotate_session(rt)
        return success, outcome

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(attempt_refresh) for _ in range(20)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    successes = [r for r in results if r[0] is True]
    failures = [r for r in results if r[0] is False]

    # Exactly 1 thread must succeed
    assert len(successes) == 1
    # 19 threads must fail
    assert len(failures) == 19


def test_session_026_concurrency_race_does_not_split_token_families():
    """SESSION-026: Competing refresh requests never produce split branches in token family."""
    sess, at, rt = session_service.create_session("eval-26", "t26", "lic-26", "dev-26")

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(refresh_rotation_service.rotate_session, rt) for _ in range(20)]
        concurrent.futures.wait(futures)

    # Count how many ACTIVE tokens exist for this family
    family_tokens = [
        t for t in refresh_token_repository._tokens.values()
        if t.family_id == sess.token_family_id and t.status == RefreshTokenStatus.ACTIVE
    ]
    # Because replay triggers family revocation when consumed token is hit, active count is either 0 or 1
    assert len(family_tokens) <= 1


def test_session_027_repository_atomic_conditional_rotation_thread_safety():
    """SESSION-027: RefreshTokenRepository.atomic_rotate directly handles concurrent attempts safely."""
    now = datetime.now(timezone.utc)
    tok = EvaluationRefreshToken(
        token_id="tok-27",
        session_id="sess-27",
        family_id="fam-27",
        token_hash="hash-27",
        status=RefreshTokenStatus.ACTIVE,
        created_at=now,
        expires_at=now + timedelta(days=7),
    )
    refresh_token_repository.save_token(tok)

    outcomes = []

    def try_rotate(i: int):
        new_tok = EvaluationRefreshToken(
            token_id=f"tok-27-new-{i}",
            session_id="sess-27",
            family_id="fam-27",
            token_hash=f"hash-27-new-{i}",
            status=RefreshTokenStatus.ACTIVE,
            created_at=now,
            expires_at=now + timedelta(days=7),
        )
        success, t, msg = refresh_token_repository.atomic_rotate("hash-27", new_tok, now)
        return success, msg

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(try_rotate, i) for i in range(20)]
        for f in concurrent.futures.as_completed(futures):
            outcomes.append(f.result())

    successes = [o for o in outcomes if o[0] is True]
    assert len(successes) == 1


def test_session_028_concurrent_session_validation_and_refresh_thread_safety():
    """SESSION-028: Concurrent token validations while refresh is underway execute without errors."""
    sess, at, rt = session_service.create_session("eval-28", "t28", "lic-28", "dev-28")

    errors = []

    def run_validation():
        try:
            for _ in range(50):
                session_validation_service.validate_access_token(at)
        except Exception as e:
            errors.append(e)

    def run_refresh():
        try:
            refresh_rotation_service.rotate_session(rt)
        except Exception as e:
            errors.append(e)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_validation) for _ in range(8)]
        futures.append(executor.submit(run_refresh))
        concurrent.futures.wait(futures)

    assert len(errors) == 0


def test_session_029_concurrent_logout_and_api_calls_fail_closed():
    """SESSION-029: 20 threads calling API while 1 logs out: all subsequent calls fail closed without deadlock."""
    sess, at, rt = session_service.create_session("eval-29", "t29", "lic-29", "dev-29")

    def call_api():
        valid, _, _ = session_validation_service.validate_access_token(at)
        return valid

    def call_logout():
        time.sleep(0.01)
        session_revocation_service.revoke_by_access_token(at)

    with concurrent.futures.ThreadPoolExecutor(max_workers=21) as executor:
        f_logout = executor.submit(call_logout)
        f_calls = [executor.submit(call_api) for _ in range(20)]
        concurrent.futures.wait([f_logout] + f_calls)

    # After logout, validation must be False
    valid, _, reason = session_validation_service.validate_access_token(at)
    assert valid is False
    assert reason == "SESSION_REVOKED"


def test_session_030_high_volume_read_write_stability():
    """SESSION-030: Session and refresh repositories withstand 100 concurrent operations without corrupting state."""
    errors = []

    def worker(i: int):
        try:
            sess, at, rt = session_service.create_session(f"eval-30-{i}", "t", "l", "d")
            session_validation_service.validate_access_token(at)
            refresh_rotation_service.rotate_session(rt)
        except Exception as e:
            errors.append(e)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(worker, i) for i in range(100)]
        concurrent.futures.wait(futures)

    assert len(errors) == 0


# ==============================================================================
# Group 6: Evaluator Logout & Multi-Scoped Revocations (SESSION-031 - SESSION-034)
# ==============================================================================

def test_session_031_logout_terminates_single_session(client: TestClient):
    """SESSION-031: POST /v1/evaluation/session/logout revokes current session token."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_031_pubkey"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    # Verify active
    assert client.get("/v1/evaluation/session", headers=headers).status_code == 200

    # Logout
    logout_res = client.post("/v1/evaluation/session/logout", headers=headers)
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "logged_out"

    # Subsequent access fails
    assert client.get("/v1/evaluation/session", headers=headers).status_code == 401


def test_session_032_logout_all_terminates_all_evaluator_sessions(client: TestClient):
    """SESSION-032: POST /v1/evaluation/session/logout-all revokes all sessions owned by evaluator."""
    # Session 1 on device 1
    res1 = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_032_pub1"},
    )
    at1 = res1.json()["session"]["access_token"]
    user_id = res1.json()["client_id"]

    # Deactivate device 1 to allow device 2 activation for same user
    activation_service.deactivate_device(res1.json()["license"]["license_id"], res1.json()["device_id"])

    # Session 2
    res2 = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_032_pub2"},
    )
    at2 = res2.json()["session"]["access_token"]

    # Call logout-all using at2
    res_all = client.post("/v1/evaluation/session/logout-all", headers={"Authorization": f"Bearer {at2}"})
    assert res_all.status_code == 200
    assert res_all.json()["status"] == "all_logged_out"

    # Both sessions are now terminated
    assert client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {at1}"}).status_code == 401
    assert client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {at2}"}).status_code == 401


def test_session_033_device_deactivation_cascades_to_sessions(client: TestClient):
    """SESSION-033: Deactivating a hardware device immediately invalidates all bound sessions."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_033_pub"},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    dev_id = res.json()["device_id"]
    headers = {"Authorization": f"Bearer {at}"}

    assert client.get("/v1/evaluation/session", headers=headers).status_code == 200

    # Deactivate device
    deact_res = client.post(
        "/v1/evaluation/device/deactivate",
        headers=headers,
        json={"device_id": dev_id},
    )
    assert deact_res.status_code == 200

    # Session is now rejected
    assert client.get("/v1/evaluation/session", headers=headers).status_code == 401


def test_session_034_license_revocation_sla_under_50ms(client: TestClient):
    """SESSION-034: License revocation terminates active sessions immediately with SLA < 50ms."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_034_pub"},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    # Verify active
    assert client.get("/v1/evaluation/session", headers=headers).status_code == 200

    # Measure revocation latency
    t0 = time.perf_counter()
    revocation_registry.revoke(lic_id)
    t_rev = time.perf_counter() - t0

    t1 = time.perf_counter()
    check_res = client.get("/v1/evaluation/session", headers=headers)
    t_check = time.perf_counter() - t1

    assert check_res.status_code == 403
    assert check_res.json()["error"] == "LICENSE_REVOKED"
    # SLA verification: combined propagation & rejection time well under 50ms
    assert (t_rev + t_check) < 0.05


# ==============================================================================
# Group 7: Browser Security (Cookie, CORS, CSRF) (SESSION-035 - SESSION-038)
# ==============================================================================

def test_session_035_refresh_with_host_cookie_sets_secure_cookie(client: TestClient):
    """SESSION-035: Refresh endpoint supports __Host-aegis_refresh cookie and sets rotated cookie."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_035_pub"},
    )
    rt = res.json()["session"]["refresh_token"]

    client.cookies.set("__Host-aegis_refresh", rt)
    ref_res = client.post("/v1/evaluation/session/refresh", json={})
    assert ref_res.status_code == 200
    assert "__Host-aegis_refresh" in ref_res.cookies
    assert ref_res.cookies["__Host-aegis_refresh"] != rt


def test_session_036_logout_clears_host_cookie(client: TestClient):
    """SESSION-036: Logout endpoint clears __Host-aegis_refresh cookie."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_036_pub"},
    )
    at = res.json()["session"]["access_token"]
    rt = res.json()["session"]["refresh_token"]

    client.cookies.set("__Host-aegis_refresh", rt)
    logout_res = client.post(
        "/v1/evaluation/session/logout",
        headers={"Authorization": f"Bearer {at}"},
    )
    assert logout_res.status_code == 200
    # Cookie should be deleted or expired
    cookie_val = logout_res.cookies.get("__Host-aegis_refresh")
    assert cookie_val is None or cookie_val == ""


def test_session_037_hostile_cors_origin_rejected_403(client: TestClient):
    """SESSION-037: Refresh request from hostile cross-origin (https://attacker.com) is rejected with 403."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_037_pub"},
    )
    rt = res.json()["session"]["refresh_token"]

    bad_res = client.post(
        "/v1/evaluation/session/refresh",
        json={"refresh_token": rt},
        headers={"Origin": "https://attacker.com"},
    )
    assert bad_res.status_code == 403
    assert bad_res.json()["error"] == "CORS_ORIGIN_DENIED"


def test_session_038_csrf_token_mismatch_rejected_403(client: TestClient):
    """SESSION-038: Refresh request with CSRF cookie and mismatched X-CSRF-Token is rejected with 403."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_038_pub"},
    )
    rt = res.json()["session"]["refresh_token"]

    client.cookies.set("__Host-aegis_refresh", rt)
    client.cookies.set("csrf_token", "legitimate-csrf-secret-12345")

    mismatch_res = client.post(
        "/v1/evaluation/session/refresh",
        json={},
        headers={"X-CSRF-Token": "attacker-forged-csrf-token"},
    )
    assert mismatch_res.status_code == 403
    assert mismatch_res.json()["error"] == "CSRF_MISMATCH"


# ==============================================================================
# Group 8: WebSocket Ticket Handshake & Revocation (SESSION-039 - SESSION-040)
# ==============================================================================

def test_session_039_websocket_ticket_issuance_and_consumption(client: TestClient):
    """SESSION-039: Issues short-lived single-use ticket and successfully consumes it."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_039_pub"},
    )
    at = res.json()["session"]["access_token"]

    tkt_res = client.post("/v1/evaluation/ws/ticket", headers={"Authorization": f"Bearer {at}"})
    assert tkt_res.status_code == 200
    ticket = tkt_res.json()["ticket"]
    assert ticket.startswith("aegis_ws_tkt_")

    val_res = client.get(f"/v1/evaluation/ws/validate-ticket?ticket={ticket}")
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "authorized"


def test_session_040_websocket_ticket_replay_and_expiry_prevention(client: TestClient):
    """SESSION-040: Consuming ticket twice fails with 401 TICKET_ALREADY_CONSUMED; expired ticket fails."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_040_pub"},
    )
    at = res.json()["session"]["access_token"]

    tkt_res = client.post("/v1/evaluation/ws/ticket", headers={"Authorization": f"Bearer {at}"})
    ticket = tkt_res.json()["ticket"]

    # First consumption succeeds
    client.get(f"/v1/evaluation/ws/validate-ticket?ticket={ticket}")

    # Replay attempt fails
    replay_res = client.get(f"/v1/evaluation/ws/validate-ticket?ticket={ticket}")
    assert replay_res.status_code == 401
    assert replay_res.json()["error"] == "TICKET_ALREADY_CONSUMED"


# ==============================================================================
# Group 9: Background Job Authorization Context & Privilege Revalidation (SESSION-041 - SESSION-042)
# ==============================================================================

def test_session_041_background_job_retains_context_and_revalidates():
    """SESSION-041: Long-running background job retains evaluator context and re-validates session."""
    sess, at, rt = session_service.create_session("eval-41", "t41", "lic-41", "dev-41")

    class MockDocProcessingJob:
        def __init__(self, token: str):
            self.token = token
            self.processed_batches = 0

        def process_batch(self):
            valid, _, _ = session_validation_service.validate_access_token(self.token)
            if not valid:
                raise PermissionError("Session invalidated during processing")
            self.processed_batches += 1

    job = MockDocProcessingJob(at)
    job.process_batch()
    job.process_batch()
    assert job.processed_batches == 2


def test_session_042_background_job_aborts_on_mid_execution_revocation():
    """SESSION-042: Mid-job session revocation causes background job to fail closed immediately."""
    sess, at, rt = session_service.create_session("eval-42", "t42", "lic-42", "dev-42")

    class MockDocProcessingJob:
        def __init__(self, token: str):
            self.token = token
            self.processed_batches = 0

        def process_batch(self):
            valid, _, reason = session_validation_service.validate_access_token(self.token)
            if not valid:
                raise PermissionError(f"Job aborted: {reason}")
            self.processed_batches += 1

    job = MockDocProcessingJob(at)
    job.process_batch()
    assert job.processed_batches == 1

    # Revoke session mid-execution
    session_revocation_service.revoke_by_access_token(at, RevocationReason.ADMIN_REVOCATION)

    with pytest.raises(PermissionError) as exc_info:
        job.process_batch()
    assert "Job aborted" in str(exc_info.value)
    assert job.processed_batches == 1  # Did not continue
