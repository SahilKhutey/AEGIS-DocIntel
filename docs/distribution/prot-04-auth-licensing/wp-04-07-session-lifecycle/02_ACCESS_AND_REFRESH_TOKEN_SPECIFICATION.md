# Dossier 02: Access & Refresh Token Specification

**Work Package:** PROT-04.07  
**Module:** `AEGIS-DocIntel Cryptographic Credentials`  
**Status:** **PASSED / CERTIFIED & SIGNED OFF**

---

## 1. Credential Specifications

AEGIS-DocIntel implements a dual-token credential model:

| Parameter | Access Token (`access_token`) | Refresh Token (`refresh_token`) | WebSocket Ticket (`ws_ticket`) |
| :--- | :--- | :--- | :--- |
| **Token Prefix** | `aegis_eval_at_` | `aegis_eval_rt_` | `aegis_ws_tkt_` |
| **Entropy Source** | `secrets.token_urlsafe(32)` | `secrets.token_urlsafe(48)` | `secrets.token_urlsafe(32)` |
| **Entropy Length** | 256 bits (32 bytes) | 384 bits (48 bytes) | 256 bits (32 bytes) |
| **Time-to-Live (TTL)** | 600 seconds (10 minutes) | 604,800 seconds (7 days) | 60 seconds (1 minute) |
| **Storage at Rest** | SHA-256 Digest | SHA-256 Digest Only | Ephemeral Memory Map |
| **Rotation Policy** | Re-issued on each refresh | Single-use: rotated on each use | Single-use: consumed on connect |
| **Transmission** | `Authorization: Bearer <at>` | `__Host-aegis_refresh` cookie or JSON | URL query param `?ticket=<tkt>` |

---

## 2. Cryptographic Digest Calculation

Raw refresh tokens are transformed immediately upon receipt:

$$\text{TokenHash} = \text{SHA-256}(\text{RawToken})$$

No subsystem, database query, logging decorator, or error handler has access to the raw token string once dispatched to the client.

```python
import hashlib

def hash_token(raw_token: str) -> str:
    cleaned = (raw_token or "").strip()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
```

---

## 3. Token Format & Representation

```text
Access Token:
aegis_eval_at_K9jF3mX7qL2vP8wE4zR1tY6uI0oA5sD8fG3hJ2kL1nM

Refresh Token:
aegis_eval_rt_W8xN2pQ9vL4rM7tZ1kC6bY3sF8jH0qT5aD2eG4wK9mX1yU7iO3pA5sD8fG3hJ2kL

WebSocket Ticket:
aegis_ws_tkt_P7qL2vP8wE4zR1tY6uI0oA5sD8fG3hJ2kL1nM9jF3mX
```
