# WP-04.03 Dossier 07: Activation API Specification

**Work Package:** PROT-04.03  
**Title:** OpenAPI Endpoints, Schemas, Status Codes & Error Contracts  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  

---

## 1. Endpoints Overview

| Method | Endpoint | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/v1/evaluation/device/challenge` | Public (Rate-Limited) | Stage 1: Request cryptographic proof challenge |
| `POST` | `/v1/evaluation/device/activate` | Public (Rate-Limited) | Stage 2: Submit signature proof & receive license |
| `GET` | `/v1/evaluation/devices` | Bearer Token | List all registered devices under active license |
| `GET` | `/v1/evaluation/devices/{id}` | Bearer Token | Retrieve details of a registered device |
| `POST` | `/v1/evaluation/devices/{id}/deactivate` | Bearer Token | Deactivate registered device and revoke sessions |
| `POST` | `/v1/evaluation/device/heartbeat` | Bearer Token | Presence check-in updating device timestamp |
| `POST` | `/v1/evaluation/devices/{id}/recover` | Recovery Code / Bearer | Emergency release of an inaccessible device |
| `POST` | `/v1/evaluation/activate` | Public (Rate-Limited) | Legacy / direct evaluation activation endpoint |

---

## 2. API Contract Specifications

### 2.1 Stage 1: Challenge Request
`POST /v1/evaluation/device/challenge`

#### Request Body
```json
{
  "activation_code": "AEGIS-EVAL-2026-DEMO",
  "device_public_key": "-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEA0dev1...",
  "installation_id": "inst-win-dev01",
  "device_label": "Primary Evaluator Laptop",
  "platform": "windows"
}
```

#### Response `HTTP 200 OK`
```json
{
  "challenge_id": "45c43d83-4a11-4770-b49c-f127cb46db07",
  "nonce": "7n8K_P9xR2tL6mQ0vW4yZ1aC3eG5iK8m",
  "canonical_message": "AEGIS-EVAL-DEVICE-PROOF-V1\nchallenge_id=45c43d83-4a11-4770-b49c-f127cb46db07\nnonce=7n8K_P9xR2tL6mQ0vW4yZ1aC3eG5iK8m\npublic_key_fingerprint=8d3e91f16f2c0cbba5b0981b2dae2ec112bf8bfa2e9a3b632dbb73e5bf2ecb61\ninstallation_id=inst-win-dev01",
  "expires_at": "2026-11-14T10:15:00.000000+00:00",
  "key_fingerprint": "8d3e91f16f2c0cbba5b0981b2dae2ec112bf8bfa2e9a3b632dbb73e5bf2ecb61",
  "algorithm": "Ed25519"
}
```

---

### 2.2 Stage 2: Proof-of-Possession Activation
`POST /v1/evaluation/device/activate`

#### Request Body
```json
{
  "challenge_id": "45c43d83-4a11-4770-b49c-f127cb46db07",
  "signature": "MEYCIQD+5r9...base64 signature...",
  "installation_id": "inst-win-dev01",
  "client_version": "1.1.0"
}
```

#### Response `HTTP 200 OK`
```json
{
  "status": "active",
  "client_id": "evaluator-primary",
  "device_id": "8d3e91f1-4a11-4770-b49c-f127cb46db07",
  "recovery_code": "REC-A4B8-9F21",
  "license": {
    "product": "AEGIS_PROTECTED_EVALUATION",
    "license_id": "67a14e9b-0294-4d89-9133-784f1b3c9b71",
    "tier": "evaluation",
    "expires_at": "2026-11-28T09:30:00Z",
    "status": "ACTIVE"
  },
  "session": {
    "access_token": "aegis_eval_at_9d8s7df...",
    "token_type": "Bearer",
    "expires_in": 600,
    "refresh_token": "aegis_eval_rt_8f7d6s5...",
    "device_id": "8d3e91f1-4a11-4770-b49c-f127cb46db07"
  },
  "entitlements": {
    "documents.read": true,
    "documents.upload": true,
    "intelligence.query": true,
    "documents.compare": true,
    "evidence.inspect": true,
    "users.manage": false,
    "platform.admin": false
  },
  "quotas": {
    "max_documents": 5,
    "max_queries_per_day": 20,
    "max_comparisons_per_day": 5
  },
  "license_token": "eyJhbGciOiJFZDI1NTE5...",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\n..."
}
```

---

## 3. Standardized Error Responses

All error payloads conform to the AEGIS Ingress Hardening Specification:

```json
{
  "error": "DEVICE_LIMIT_EXCEEDED",
  "message": "Device limit exceeded (1/1). Deactivate an existing registered device before activating a new one."
}
```

| HTTP Status | Error String | Cause |
| :--- | :--- | :--- |
| `400 Bad Request` | `INVALID_ACTIVATION_CODE` | Code unrecognized, empty, or expired |
| `400 Bad Request` | `MALFORMED_PUBLIC_KEY` | Public key cannot be parsed as Ed25519 or RSA |
| `400 Bad Request` | `INSTALLATION_MISMATCH` | `installation_id` does not match Stage 1 |
| `400 Bad Request` | `CHALLENGE_EXPIRED` | Challenge submitted after TTL elapsed |
| `400 Bad Request` | `CHALLENGE_ALREADY_CONSUMED` | Challenge replay detected |
| `401 Unauthorized` | `INVALID_DEVICE_SIGNATURE` | Cryptographic signature verification failed |
| `401 Unauthorized` | `RECOVERY_FAILED` | Emergency recovery code hash mismatch |
| `404 Not Found` | `CHALLENGE_NOT_FOUND` | `challenge_id` does not exist |
| `404 Not Found` | `DEVICE_NOT_FOUND` | Device ID not found under authenticated license |
| `409 Conflict` | `DEVICE_LIMIT_EXCEEDED` | Attempting to activate a 2nd active device |
| `429 Too Many Requests` | `RATE_LIMIT_EXCEEDED` | Exceeded 10 requests / IP / hour |
