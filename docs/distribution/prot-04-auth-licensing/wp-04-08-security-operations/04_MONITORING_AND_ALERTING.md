# PROT-04.08 — Dossier 04: Monitoring, Threat Detection & Alerting Engine

## 1. Threat Detection Engine Overview
The AEGIS Monitoring Engine continuously evaluates emitted security events against 12 formal threat detection rules (`MON-001` through `MON-012`). The engine uses sliding time windows, stateful sliding buckets, and multi-threaded locks to guarantee zero missed detections under high concurrent traffic.

---

## 2. Formal Detection Rule Specifications

### MON-001: Activation Code Brute-Force (Account Level)
- **Condition**: $> 5$ activation failures for a single evaluator account within a 15-minute sliding window ($900\text{s}$).
- **Severity**: `HIGH`
- **Automated Containment**: Temporarily lock target account for 30 minutes; require administrative reset.
- **Runbook**: `IR-05`.

### MON-002: Activation Code Brute-Force (Source IP Level)
- **Condition**: $> 20$ activation failures originating from a single source IP within a 5-minute window ($300\text{s}$).
- **Severity**: `HIGH`
- **Automated Containment**: Apply IP-level rate-limiting (`429 Too Many Requests`) for 60 minutes.
- **Runbook**: `IR-05`.

### MON-003: Refresh Token Replay Reuse
- **Condition**: Presentation of a consumed/rotated refresh token ($1$ event).
- **Severity**: `CRITICAL`
- **Automated Containment**: Atomic revocation of entire token family, immediate termination of active sessions, and broadcast alert.
- **Runbook**: `IR-06`.

### MON-004: Forged / Tampered License Signature
- **Condition**: Presentation of an evaluation license whose Ed25519 signature fails verification ($1$ event).
- **Severity**: `CRITICAL`
- **Automated Containment**: Reject request with `403 Forbidden`, flag client fingerprint in threat register.
- **Runbook**: `IR-04`.

### MON-005: Rapid Device Transfers
- **Condition**: $\ge 3$ distinct hardware device registrations for the same evaluation license within 7 days ($604,800\text{s}$).
- **Severity**: `WARNING`
- **Automated Containment**: Require administrative approval before additional device bindings are permitted.
- **Runbook**: `IR-04`.

### MON-006: Cross-Tenant Access Attempt
- **Condition**: Authenticated user attempts to access resources belonging to a different tenant ID ($1$ event).
- **Severity**: `CRITICAL`
- **Automated Containment**: Terminate evaluator session, record security incident, dispatch high-priority alert.
- **Runbook**: `IR-07`.

### MON-007: Usage Ledger Quota Reconciliation Mismatch
- **Condition**: Drift between in-memory quota counters and transactional database ledger ($> 0$ units).
- **Severity**: `HIGH`
- **Automated Containment**: Reconcile balances from authoritative append-only usage entries.
- **Runbook**: `IR-08`.

### MON-008: Alert Delivery Sink Failure
- **Condition**: Security webhook or remote SIEM syslog destination returns non-2xx or connection timeout.
- **Severity**: `HIGH`
- **Automated Containment**: Enqueue failed alert to persistent retry queue, log delivery failure event locally.
- **Runbook**: `IR-09`.

### MON-009: Rapid WebSocket Handshake Failures
- **Condition**: $> 10$ failed WebSocket ticket presentations from a single source within 60 seconds ($60\text{s}$).
- **Severity**: `HIGH`
- **Automated Containment**: Throttle WebSocket connections from source IP.
- **Runbook**: `IR-01`.

### MON-010: Cryptographic Audit Integrity Failure
- **Condition**: Hash-chain continuity failure or external checkpoint mismatch detected ($1$ event).
- **Severity**: `CRITICAL`
- **Automated Containment**: Lock audit log against writes, declare P1 security incident, alert SOC immediately.
- **Runbook**: `IR-09`.

### MON-011: Privileged Role Escalation Attempt
- **Condition**: Evaluator credentials presented to administrative routes (`/v1/admin/*`).
- **Severity**: `CRITICAL`
- **Automated Containment**: Immediate 403 response, session invalidation, and operator audit trail update.
- **Runbook**: `IR-01`.

### MON-012: Emergency Key Compromise Signal
- **Condition**: Operator triggers administrative key compromise endpoint.
- **Severity**: `CRITICAL`
- **Automated Containment**: Transition target key to `COMPROMISED`, invalidate cache, reject dependent tokens.
- **Runbook**: `IR-02`.

---

## 3. Resilience, Degradation & Fail-Closed Behavior
1. **Sliding Window Maintenance**: Sliding windows are pruned dynamically on each event evaluation to prevent unbounded memory growth.
2. **Channel Delivery Retries**: Alert delivery failures are buffered in an internal failure log (`_delivery_failures`) with backoff retries.
3. **Fail-Closed Mode**: If the monitoring service enters degraded mode (`set_degraded_mode(True)`), all critical operations fall back to fail-closed state, preventing unmonitored evaluation execution.
