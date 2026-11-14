# WP-04.02: WebSocket Connection Authentication & Stream Lifecycle

**Document:** `06_WEBSOCKET_AUTH_REVIEW.md`  
**Work Package:** PROT-04.02 — Production Authentication Hardening  
**Target:** Bidirectional Streaming Ingress, Ticket/Token Verification & Connection Termination  
**Status:** **AUDITED, HARDENED & VERIFIED**  
**Classification:** Internal Security Architecture Report  

---

## 1. WebSocket Protocol Ingress Paradigm

Because WebSocket connections establish a persistent TCP socket via an ASGI HTTP upgrade handshake, standard HTTP request-response middleware cannot authenticate individual stream events.

### 1.1 `AuthGuardMiddleware` Protocol Handling
In `src/api/auth_guard.py`:
```python
if scope["type"] != "http":
    await self.app(scope, receive, send)
    return
```
The guard passes `websocket` ASGI scopes through directly to the router to prevent premature TCP disconnection before the ASGI connection lifecycle begins.

---

## 2. Route-Level Handshake Authentication (`get_current_tenant_ws`)

WebSocket routes in AEGIS (e.g. `@router.websocket("/ws/{session_id}")` in `src/api/routers/queries.py`) declare:
```python
async def query_websocket(
    websocket: WebSocket,
    session_id: str,
    tenant: TenantContext = Depends(get_current_tenant_ws),
):
    ...
```

### 2.1 Handshake Credential Extraction
`get_current_tenant_ws` in `src/api/auth.py` evaluates credentials during the initial connection handshake:
1. **Header Parsing:** Inspects `Authorization: Bearer <token>` and `X-API-Key`.
2. **Query Parameter Fallback:** If browser WebSocket APIs cannot attach custom headers, inspects `?token=<jwt>` or `?api_key=<key>`.
3. **Cryptographic Validation:** Passes the credential to `_validate_jwt()` or `_validate_api_key()`.

### 2.2 Fail-Closed Disconnect Frame
If credentials are missing, expired, or invalid:
```python
async def _safe_close():
    if hasattr(websocket, "close"):
        try:
            close_res = websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            if inspect.isawaitable(close_res):
                await close_res
        except Exception:
            pass

if not (token or api_key):
    await _safe_close()
    raise HTTPException(status_code=401, detail="WebSocket authentication required")
```
The server sends a standard WebSocket close frame with code `1008` (Policy Violation) and terminates the socket before receiving any JSON messages or sending any streaming output (`AUTH-H-026`).

---

## 3. Streaming Stream Security Invariants

1. **Pre-Accept Authorization:** Connections are rejected prior to `await websocket.accept()`.
2. **Tenant Scoping:** All downstream LLM streaming tokens, RAG query chunks, and intermediate extraction results are partitioned by `tenant.tenant_id`.
3. **Revocation Monitoring:** Active long-running streams periodically check session validity against the evaluation revocation registry, aborting stream generation if the session is revoked mid-query.
