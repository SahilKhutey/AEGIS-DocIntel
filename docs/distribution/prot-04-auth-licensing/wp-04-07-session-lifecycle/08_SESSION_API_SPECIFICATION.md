# Dossier 08: Session API Specification

**Work Package:** PROT-04.07  
**Module:** `AEGIS-DocIntel Evaluation Gateway REST API`  
**Status:** **PASSED / CERTIFIED & SIGNED OFF**

---

## 1. Public Evaluator Endpoints

### 1.1 `POST /v1/evaluation/session/refresh`
Rotates the session access token and refresh token.
- **Headers:** `Origin` (optional), `X-CSRF-Token` (required if using cookie)
- **Cookies:** `__Host-aegis_refresh` (optional)
- **Request Body (JSON):**
  ```json
  {
    "refresh_token": "aegis_eval_rt_..." // optional if cookie provided
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "aegis_eval_at_new...",
    "token_type": "Bearer",
    "expires_in": 600,
    "refresh_token": "aegis_eval_rt_new..."
  }
  ```
- **Errors:**
  - `400 Bad Request`: `MISSING_REFRESH_TOKEN`
  - `401 Unauthorized`: `REFRESH_FAILED` (Replay detected or invalid token)
  - `403 Forbidden`: `CORS_ORIGIN_DENIED`, `CSRF_MISMATCH`

---

### 1.2 `POST /v1/evaluation/session/logout`
Revokes the calling session and deletes the session cookie.
- **Headers:** `Authorization: Bearer aegis_eval_at_...`
- **Response (200 OK):**
  ```json
  {
    "status": "logged_out",
    "message": "Evaluation session successfully terminated."
  }
  ```

---

### 1.3 `POST /v1/evaluation/session/logout-all`
Revokes all active sessions belonging to the evaluator across all devices.
- **Headers:** `Authorization: Bearer aegis_eval_at_...`
- **Response (200 OK):**
  ```json
  {
    "status": "all_logged_out",
    "evaluator_id": "evaluator-primary",
    "revoked_sessions_count": 2,
    "message": "All 2 active sessions revoked successfully."
  }
  ```

---

### 1.4 `GET /v1/evaluation/sessions`
Lists all active sessions for the authenticated evaluator.
- **Headers:** `Authorization: Bearer aegis_eval_at_...`
- **Response (200 OK):**
  ```json
  {
    "evaluator_id": "evaluator-primary",
    "count": 1,
    "sessions": [
      {
        "session_id": "b9f71c42-...",
        "license_id": "lic-...",
        "device_id": "dev-...",
        "status": "active",
        "created_at": "2026-11-14T11:00:00Z",
        "last_seen_at": "2026-11-14T11:05:00Z",
        "idle_expires_at": "2026-11-14T11:35:00Z",
        "absolute_expires_at": "2026-11-21T11:00:00Z"
      }
    ]
  }
  ```

---

### 1.5 `POST /v1/evaluation/ws/ticket`
Issues a single-use 60-second ticket for WebSocket connection.
- **Headers:** `Authorization: Bearer aegis_eval_at_...`
- **Response (200 OK):**
  ```json
  {
    "ticket": "aegis_ws_tkt_...",
    "expires_in": 60,
    "expires_at": 1794657600.0
  }
  ```

---

## 2. Administrator Endpoints

### 2.1 `GET /v1/admin/evaluation/sessions`
Inspects all active and historical evaluation sessions.
- **Headers:** `X-Admin-Key: <admin_key>`

### 2.2 `POST /v1/admin/evaluation/sessions/revoke-all`
Administrative revocation of sessions across an entire tenant, license, or evaluator.
- **Headers:** `X-Admin-Key: <admin_key>`
- **Parameters:** `?evaluator_id=...` or `?license_id=...`
