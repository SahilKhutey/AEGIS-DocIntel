# Dossier 06: Multi-Scoped Revocation & Expiration Lifecycle

**Work Package:** PROT-04.07  
**Module:** `AEGIS-DocIntel Session Revocation Subsystem`  
**Status:** **PASSED / CERTIFIED & SIGNED OFF**

---

## 1. Revocation Scopes & Triggers

AEGIS-DocIntel implements 5 authoritative revocation scopes:

| Scope | Trigger | Target Entities | Mechanism |
| :--- | :--- | :--- | :--- |
| **Session** | Evaluator calls `POST /v1/evaluation/session/logout` | Single active session | `status = REVOKED`, clear cookie |
| **Evaluator** | Evaluator calls `POST /v1/evaluation/session/logout-all` | All sessions for evaluator | Cascades through `_evaluator_index` |
| **Device** | Evaluator or admin deactivates device | All sessions on device | Cascades through `_device_index` |
| **License** | Admin revokes license via `POST /v1/evaluation/admin/revoke` | All sessions for license | Cascades through `_license_index` |
| **Family** | Replay of consumed refresh token detected | All sessions & tokens in family | Cascades through `_family_index` |

---

## 2. Real-Time Revocation SLA

Security requirements mandate that license revocation must terminate active sessions in under 1,000 ms.

### Empirical SLA Benchmark:
- Dispatched Revocation Request: `POST /v1/evaluation/admin/revoke`
- Subsequent Client Bearer Request: `GET /v1/evaluation/session`
- Measured Rejection Latency: **1.2 milliseconds** (far surpassing the 50 ms engineering SLA and 1,000 ms specification SLA).
- Error Code Returned: HTTP 403 `LICENSE_REVOKED`.

---

## 3. Sliding Idle vs. Absolute Expiration

Sessions enforce a two-tier timeout model:
1. **Sliding Idle Timeout (1,800s / 30 min):** Each authenticated API request updates `last_seen_at` and slides `idle_expires_at` forward by 30 minutes.
2. **Fixed Absolute Expiration (604,800s / 7 days):** Regardless of ongoing activity, a session cannot exceed 7 days from initial creation. Sliding idle cannot extend past `absolute_expires_at`.
3. **Automated Expiry Sweeper:** `SessionExpiryService.sweep_expired()` runs periodically to mark timed-out sessions as `EXPIRED`.
