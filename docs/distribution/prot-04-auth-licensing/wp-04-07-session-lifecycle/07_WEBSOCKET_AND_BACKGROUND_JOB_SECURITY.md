# Dossier 07: WebSocket & Background Job Security Architecture

**Work Package:** PROT-04.07  
**Module:** `AEGIS-DocIntel Real-Time & Asynchronous Execution Security`  
**Status:** **PASSED / CERTIFIED & SIGNED OFF**

---

## 1. WebSocket Single-Use Ticket Handshake

### Threat Model:
WebSocket connection handshakes occur via HTTP `GET` requests where tokens are commonly passed in query parameters (`/ws?token=...`). This exposes high-value credentials to web proxy logs, browser histories, and CDN access logs.

### Solution Protocol:
1. **Ticket Request:** Evaluator client sends authenticated HTTP request:
   ```http
   POST /v1/evaluation/ws/ticket
   Authorization: Bearer aegis_eval_at_...
   ```
2. **Ephemeral Ticket Generation:** Server issues a 256-bit single-use ticket (`aegis_ws_tkt_...`) with a strict **60-second TTL**.
3. **Handshake Execution:** Client connects to `wss://gateway/v1/evaluation/ws?ticket=aegis_ws_tkt_...`.
4. **Atomic Consumption:** Server consumes the ticket on connect. If the ticket is replayed, or if 60 seconds have elapsed, the connection is rejected immediately (`TICKET_ALREADY_CONSUMED` or `TICKET_EXPIRED`).
5. **Revocation Closure:** The server binds the active WebSocket connection to the parent `session_id`. If the session or license is revoked, the WebSocket connection is terminated immediately with code `1008 (Policy Violation)`.

---

## 2. Long-Running Background Job Security

### Threat Model:
A long-running document extraction, OCR, or comparison pipeline may take several minutes to process. If an evaluator's license is revoked mid-job, an unhardened system would continue processing and return proprietary results.

### Solution Protocol:
1. **Authorization Context Retention:** Workers receive an immutable `JobSecurityContext` containing `session_id`, `license_id`, and `tenant_id`.
2. **Periodic Revalidation:** Before processing each document page or batch, the worker queries `SessionValidationService.validate_access_token()`.
3. **Fail-Closed Mid-Execution Abort:** If the session or license status is no longer `ACTIVE`, the worker halts execution immediately, purges temporary extracted artifacts, and raises `PermissionError("Job aborted: LICENSE_REVOKED")`.
