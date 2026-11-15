# Workstream REM-05: Session Lifecycle, Refresh Rotation & Revocation

**Initiative:** PROT-FINAL-02  
**Domain:** Evaluator Session Management, Rotating Refresh Tokens & Real-Time Revocation  
**Implementation Modules:**
- [src/services/evaluation/session_service.py](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/src/services/evaluation/session_service.py)
- [src/services/evaluation/refresh_rotation_service.py](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/src/services/evaluation/refresh_rotation_service.py)
- [src/services/evaluation/revocation_service.py](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/src/services/evaluation/revocation_service.py)
- [src/services/evaluation/websocket_ticket_service.py](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/src/services/evaluation/websocket_ticket_service.py)
- [src/api/routers/evaluation/sessions.py](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/src/api/routers/evaluation/sessions.py)
**Verification Suite:** [tests/security/evaluation/test_rem_05_sessions.py](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/tests/security/evaluation/test_rem_05_sessions.py)  
**Status:** **15/15 Tests Passed (100%)**

---

## 1. Problem Statement & Audit Findings

The audit confirmed that:
1. **Client-Side "Logout" Weakness:** Merely discarding a token from browser local storage is not server-side revocation. The backend must authoritatively terminate sessions and invalidate tokens.
2. **Refresh Token Replay Vulnerability:** If a refresh token is intercepted, an attacker could maintain persistent access unless token rotation with strict replay compromise cascading is enforced.
3. **Revocation Propagation Lag:** When an administrator revokes a license, all linked active sessions, API calls, and WebSockets must be terminated immediately (<50ms SLA).
4. **Token Leakage via WebSocket URLs:** Passing long-lived bearer tokens in WebSocket query parameters exposes secrets in browser history and proxy access logs.

---

## 2. Engineering Changes Executed

### 2.1 Short-Lived Access Tokens & Rotation Lineage
In `src/services/evaluation/session_service.py` and `refresh_rotation_service.py`:
- Access tokens expire after **600 seconds (10 minutes)**.
- Sliding idle timeout: **1800 seconds (30 minutes)**; absolute max lifetime: **7 days**.
- Every refresh operation issues a brand new access token and a brand new refresh token, atomically transitioning the previous refresh token to `CONSUMED`.

### 2.2 Replay Attack Detection & Family Revocation
- If an already consumed refresh token is presented again, the system recognizes a token replay attack.
- **Compromise Cascade:** The entire token family and all linked active sessions are immediately revoked server-side, and a high-severity security audit event (`REFRESH_REUSE_DETECTED`) is logged.

### 2.3 Real-Time Revocation & Multi-Target Dispatches
In `src/services/evaluation/revocation_service.py`:
- Revoking a license (`revocation_registry.revoke()`) propagates immediately to all linked sessions, terminating them within <50ms.
- Single logout (`POST /v1/evaluation/session/logout`) revokes the current session.
- Global evaluator logout (`POST /v1/evaluation/session/logout-all`) revokes all sessions belonging to the evaluator across all devices.

### 2.4 Single-Use WebSocket Handshake Tickets
In `src/services/evaluation/websocket_ticket_service.py`:
- Evaluators request a short-lived single-use ticket (`POST /v1/evaluation/ws/ticket`) with a 60-second TTL.
- Consuming the ticket during the WebSocket upgrade handshake immediately marks it consumed, preventing replay.
- Expired or consumed tickets are rejected fail-closed.

### 2.5 Hashes-at-Rest Security
All access tokens and refresh tokens are stored exclusively as SHA-256 digests in `SessionRepository` and `RefreshTokenRepository`. Plaintext tokens never touch persistent storage.

---

## 3. Acceptance Verification (SES-REM-001 through 015)

| Test ID | Scenario | Verification Result |
|---|---|---|
| `SES-REM-001` | Session creation upon activation | PASSED (Active, tokens issued) |
| `SES-REM-002` | Session binding to device key & license | PASSED (Device & session linked) |
| `SES-REM-003` | Access token TTL enforcement (600s) | PASSED (TTL & sliding idle verified) |
| `SES-REM-004` | Refresh token rotation | PASSED (New pair issued, old consumed) |
| `SES-REM-005` | Refresh token replay detected | PASSED (HTTP 401 Replay Detected) |
| `SES-REM-006` | Compromise cascade family revocation | PASSED (Child access tokens revoked) |
| `SES-REM-007` | Single logout revokes access token | PASSED (Immediate termination) |
| `SES-REM-008` | Global evaluator logout | PASSED (All evaluator sessions dead) |
| `SES-REM-009` | License revocation terminates sessions | PASSED (<50ms SLA verified) |
| `SES-REM-010` | Revoked session denied on protected APIs | PASSED (HTTP 401/403) |
| `SES-REM-011` | WebSocket ticket issuance | PASSED (Single-use ticket, 60s TTL) |
| `SES-REM-012` | WebSocket ticket single-use consumption | PASSED (Replay rejected) |
| `SES-REM-013` | WebSocket ticket expiration | PASSED (Expired rejected) |
| `SES-REM-014` | Concurrency race protection on refresh | PASSED (1 succeeds, others rejected) |
| `SES-REM-015` | Token hashes stored at rest | PASSED (No plaintext in repository) |
