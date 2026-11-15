# PROT-04.08 — Dossier 07: Operational Incident Response Runbooks (IR-01 through IR-10)

## Runbook IR-01: Compromised Evaluator Session Containment
- **Trigger**: Anomaly detection, suspicious IP change, or evaluator self-report.
- **Execution Steps**:
  1. Identify affected evaluator ID and session token from request correlation headers.
  2. Invoke `POST /v1/evaluation/session/logout` (single session) or `POST /v1/evaluation/session/logout-all`.
  3. Validate immediate termination: ensure subsequent API calls return `401 Unauthorized`.
  4. Attach session termination log to incident evidence register.

---

## Runbook IR-02: Emergency License Signing Key Invalidation
- **Trigger**: Detection or credible notification of Ed25519 private key leak.
- **Execution Steps**:
  1. Identify compromised `key_id`.
  2. Invoke `key_rotation_service.emergency_compromise_key(key_id)`.
  3. Execute `key_rotation_service.rotate_license_signing_key()` to promote a clean new key.
  4. Verify that all licenses signed by the compromised key return `403 Forbidden` on verification.
  5. Issue emergency client patch updating the trusted verification key registry.

---

## Runbook IR-03: API Key Invalidation & Rotation
- **Trigger**: Exposed gateway API key in evaluator logs, git commits, or external repositories.
- **Execution Steps**:
  1. Call `key_rotation_service.rotate_api_key(key_id)`.
  2. Confirm old key immediately fails with `401 Unauthorized`.
  3. Safely provision new high-entropy key to authorized operator via encrypted vault.

---

## Runbook IR-04: License Revocation & Evaluator Suspension
- **Trigger**: Non-payment, term violation, or fraudulent activation.
- **Execution Steps**:
  1. Call `revocation_registry.revoke(license_id)`.
  2. Active gateway sessions evaluate revocation state during token presentation ($< 50\text{ms}$).
  3. Evaluator requests immediately reject with `403 Forbidden` (`LICENSE_REVOKED`).

---

## Runbook IR-05: Activation Code Brute-Force Mitigation
- **Trigger**: `MON-001` ($> 5$ account failures) or `MON-002` ($> 20$ IP failures).
- **Execution Steps**:
  1. Trigger dynamic rate limiter for offending IP (return `429 Too Many Requests`).
  2. Lock target evaluator activation code for 30 minutes.
  3. Dispatch warning notification to evaluator's registered email address.

---

## Runbook IR-06: Refresh Token Replay Response
- **Trigger**: `MON-003` (Presentation of consumed refresh token).
- **Execution Steps**:
  1. Invalidate entire token family immediately via `session_revocation_service`.
  2. Terminate all active evaluation sessions tied to that family.
  3. Declare P1 security incident: capture client IP and user-agent of the replay presenter.

---

## Runbook IR-07: Cross-Tenant Access Breach Protocol
- **Trigger**: `MON-006` (Evaluator tenant ID does not match target resource tenant ID).
- **Execution Steps**:
  1. Immediately abort request with `403 Forbidden`.
  2. Terminate user session.
  3. Isolate affected tenant database partitions and review audit access trail for data leakage.

---

## Runbook IR-08: Database Backup Integrity Failure & Restore
- **Trigger**: Checksum mismatch or corrupted persistent storage.
- **Execution Steps**:
  1. Verify cryptographic backup SHA-256 checksum (`backup_verification_service.verify_backup_integrity`).
  2. If valid, execute restore with authoritative revocation reconciliation (`restore_and_reconcile`).
  3. Enforce **Non-Resurrection Rule**: confirm previously revoked entities remain revoked.

---

## Runbook IR-09: Audit Log Integrity Tamper Response
- **Trigger**: `MON-010` (Hash-chain break or external checkpoint divergence).
- **Execution Steps**:
  1. Lock audit ingest pipeline against further writes.
  2. Isolate server memory and extract forensic snapshot.
  3. Identify first corrupted entry index $k$.
  4. Compare with signed external witness checkpoint to identify tampered or missing blocks.

---

## Runbook IR-10: Distribution Package Tampering Detection
- **Trigger**: Package hash mismatch or unexpected binary modification.
- **Execution Steps**:
  1. Halt release pipeline and withdraw corrupted binary download URLs.
  2. Execute static scan for leaked secrets or unauthorized development tokens.
  3. Rebuild binary from verified git commit in isolated hermetic CI environment.
