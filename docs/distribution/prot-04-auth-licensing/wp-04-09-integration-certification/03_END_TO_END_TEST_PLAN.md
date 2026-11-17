# PROT-04.09 — Dossier 03: End-to-End Test Plan

## 1. Test Strategy & Scope

The End-to-End Verification Protocol executes 101 distinct integration scenarios spanning every security boundary of the AEGIS-DocIntel Protected Demo Edition.

The test suite is implemented in:
[test_prot_04_09_integration_protocol.py](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/tests/security/integration_certification/test_prot_04_09_integration_protocol.py)

---

## 2. Test Workstreams & Coverage

```
+---------------------------------------------------------------------------------------+
|                       PROT-04.09 INTEGRATION TEST WORKSTREAMS                         |
+---------------------------------------------------------------------------------------+
|  Workstream 01: Authentication, Activation & Device Proofs      (INT-AUTH-001 - 012)  |
|  Workstream 02: Cryptographic Licensing & Key Lifecycles         (INT-LIC-001 - 012)  |
|  Workstream 03: Entitlement Enforcement & RBAC Boundary          (INT-ENT-001 - 010)  |
|  Workstream 04: Quotas, Atomic Reservations & Resource Limiting (INT-QUOTA-001 - 012) |
|  Workstream 05: Session Lifecycles, Token Rotation & Revocation  (INT-SESS-001 - 014) |
|  Workstream 06: Private Engine Isolation & Gateway Boundary      (INT-ENG-001 - 010)  |
|  Workstream 07: Cross-Cutting Subsystem Security Guarantees       (CROSS-001 - 015)   |
|  Workstream 08: End-to-End Evaluator User Journeys               (JOURNEY-A - F)     |
|  Workstream 09: Resilience, Chaos & Disaster Recovery            (RES-INT-001 - 010)  |
+---------------------------------------------------------------------------------------+
|  TOTAL INTEGRATION SCENARIOS: 101 SCENARIOS (100% AUTOMATED & VERIFIED)               |
+---------------------------------------------------------------------------------------+
```

---

## 3. Comprehensive Verification Matrix

### Workstream 01: Authentication & Device Binding
- **INT-AUTH-001**: Valid activation code + Ed25519 PoP signature returns active license & session.
- **INT-AUTH-002**: Invalid activation code returns HTTP 400.
- **INT-AUTH-003**: Expired challenge response returns HTTP 400.
- **INT-AUTH-004**: Replayed activation challenge returns HTTP 400.
- **INT-AUTH-005**: Tampered Ed25519 device signature rejected with HTTP 400/401.
- **INT-AUTH-006**: Device registration exceeding max_devices returns HTTP 409 Conflict.
- **INT-AUTH-007**: Suspended license activation code rejected HTTP 403.
- **INT-AUTH-008**: Revoked license activation code rejected HTTP 403.
- **INT-AUTH-009**: Expired license activation code rejected HTTP 400/403.
- **INT-AUTH-010**: Activation bound to another evaluator enforces authoritative account.
- **INT-AUTH-011**: Deactivated device cannot refresh or access APIs.
- **INT-AUTH-012**: Valid device registration successfully issues session.

### Workstream 02: Licensing & Key Management
- **INT-LIC-001**: Cryptographically valid Ed25519 signed license passes verification.
- **INT-LIC-002**: Tampered license payload bytes trigger `LicenseSignatureError`.
- **INT-LIC-003**: Corrupted signature string triggers `LicenseSignatureError`.
- **INT-LIC-004**: Unknown key_id in protected header rejected.
- **INT-LIC-005**: Expired license document rejected.
- **INT-LIC-006**: Not-yet-valid license document rejected.
- **INT-LIC-007**: Revoked license present in registry rejected.
- **INT-LIC-008**: Unknown forward-compatible claims safely preserved.
- **INT-LIC-009**: New key signs new license; verifies cleanly.
- **INT-LIC-010**: Retired key in `VERIFY_ONLY` validates circulating licenses.
- **INT-LIC-011**: Retired key rejects new license issuance.
- **INT-LIC-012**: Compromised signing key immediately invalidates all associated licenses.

### Workstream 03: Entitlement & RBAC
- **INT-ENT-001**: Permitted evaluation feature returns HTTP 200.
- **INT-ENT-002**: Unentitled feature returns HTTP 403 Forbidden.
- **INT-ENT-003**: Client modifying role to `admin` receives zero elevation.
- **INT-ENT-004**: Client modifying tenant header receives zero data leakage.
- **INT-ENT-005**: Empty entitlement payload fails closed.
- **INT-ENT-006**: Incompatible policy version rejected.
- **INT-ENT-007**: Administrative mid-session override immediately takes effect.
- **INT-ENT-008**: Overrides take effect within the current turn.
- **INT-ENT-009**: Cross-tenant document inspection returns HTTP 404 (IDOR safe).
- **INT-ENT-010**: Evaluator calling administrative routes returns HTTP 403.

### Workstream 04: Quotas & Resource Limits
- **INT-QUOTA-001**: Normal operation within limit settles cleanly.
- **INT-QUOTA-002**: Exceeding limit returns HTTP 429 Too Many Requests.
- **INT-QUOTA-003**: Concurrency race at boundary prevents negative balance.
- **INT-QUOTA-004**: Failed operation rolls back pending reservation.
- **INT-QUOTA-005**: Retried request with identical idempotency key avoids double charge.
- **INT-QUOTA-006**: Expired reservation automatically reclaimed.
- **INT-QUOTA-007**: Usage ledger drift triggers high-severity alert MON-007.
- **INT-QUOTA-008**: Tenant A cannot consume Tenant B's quota.
- **INT-QUOTA-009**: LLM timeout applies conservative settlement fallback.
- **INT-QUOTA-010**: Oversized file upload rejected prior to ingestion.
- **INT-QUOTA-011**: Simultaneous parsing jobs cap enforced.
- **INT-QUOTA-012**: Manual admin adjustment records verifiable audit log.

### Workstream 05: Session Lifecycles & Revocation
- **INT-SESSION-001**: Active session validates cleanly.
- **INT-SESSION-002**: Expired session rejected HTTP 401.
- **INT-SESSION-003**: Refresh token rotated; prior token invalidated.
- **INT-SESSION-004**: Refresh token replay triggers immediate family revocation.
- **INT-SESSION-005**: Single session logout invalidates target session.
- **INT-SESSION-006**: Logout-all invalidates all evaluator sessions.
- **INT-SESSION-007**: Device deactivation cascades to all linked sessions.
- **INT-SESSION-008**: License revocation cascades to all linked sessions.
- **INT-SESSION-009**: Evaluator account suspension blocks access.
- **INT-SESSION-010**: Single-use WebSocket ticket issued and consumed.
- **INT-SESSION-011**: Mid-turn logout preserves background audit records.
- **INT-SESSION-012**: Active background job aborts on mid-execution revocation.
- **INT-SESSION-013**: Revocation cache propagation SLA < 50ms verified.
- **INT-SESSION-014**: Revocation authority failure causes gateway to fail closed.

### Workstream 06: Private Engine Isolation
- **INT-ENGINE-001**: Gateway-authorized HMAC token accepted by Engine Guard.
- **INT-ENGINE-002**: Direct unauthenticated request rejected HTTP 401.
- **INT-ENGINE-003**: Request with forged tenant context rejected HTTP 403.
- **INT-ENGINE-004**: Expired service token rejected HTTP 401.
- **INT-ENGINE-005**: Replayed quota reservation ID rejected HTTP 403.
- **INT-ENGINE-006**: Request missing quota reservation rejected HTTP 403.
- **INT-ENGINE-007**: Request with revoked license rejected HTTP 403.
- **INT-ENGINE-008**: Evaluator attempting internal admin operation rejected HTTP 403.
- **INT-ENGINE-009**: Engine source code verified absent from client package.
- **INT-ENGINE-010**: Provider credentials verified absent from client artifacts.

### Workstream 07: Cross-Cutting Guarantees (CROSS-001 - 015)
- **CROSS-001**: Evaluator A cannot request Evaluator B's document.
- **CROSS-002**: Evaluator presenting mismatched tenant ID denied access.
- **CROSS-003**: Evaluator modifying role claim cannot execute admin actions.
- **CROSS-004**: Expired license with valid JWT denied access.
- **CROSS-005**: Revoked session with valid JWT denied access.
- **CROSS-006**: Valid license on deactivated device denied access.
- **CROSS-007**: Valid session with disabled entitlement denied access.
- **CROSS-008**: Valid entitlement with exhausted quota denied access.
- **CROSS-009**: Frontend session cannot bypass engine guard.
- **CROSS-010**: Concurrent requests exceeding quota fail atomically.
- **CROSS-011**: Replay of consumed refresh token revokes token family.
- **CROSS-012**: Revocation during active WebSocket disconnects cleanly.
- **CROSS-013**: Revocation during long-running processing aborts execution.
- **CROSS-014**: Security authority failure causes fail-closed denial.
- **CROSS-015**: Static release scanner confirms zero private keys in client package.

### Workstream 08: End-to-End User Journeys (JOURNEY-A - F)
- **JOURNEY-A**: First-time evaluator (code -> challenge -> activate -> upload -> query).
- **JOURNEY-B**: Evaluator reaches quota (quota exhausted -> 429 -> admin adjustment -> success).
- **JOURNEY-C**: Device transfer (active device -> recovery code unbind -> new device activate).
- **JOURNEY-D**: License revocation (operator revokes -> refresh denied -> API denied -> audit logged).
- **JOURNEY-E**: Client tampering (modified client -> server-side rejection -> zero privilege escalation).
- **JOURNEY-F**: Security incident (replay detected -> family revoked -> incident declared -> evidence attached -> closed).

### Workstream 09: Resilience & Chaos (RES-INT-001 - 010)
- **RES-INT-001**: Database offline -> Fail closed.
- **RES-INT-002**: License authority offline -> Deny issuance.
- **RES-INT-003**: Quota authority offline -> Fail closed on metered operations.
- **RES-INT-004**: Audit pipeline buffering -> Zero dropped logs.
- **RES-INT-005**: Private engine unavailable -> Safe generic error.
- **RES-INT-006**: Worker crash recovery -> Zero double charge.
- **RES-INT-007**: Gateway restart during refresh -> Zero token branching.
- **RES-INT-008**: Revocation cache SLA (< 50ms) propagation.
- **RES-INT-009**: Duplicate audit event delivery -> Idempotent handling.
- **RES-INT-010**: Backup restore from older snapshot -> No resurrection of revoked licenses.
