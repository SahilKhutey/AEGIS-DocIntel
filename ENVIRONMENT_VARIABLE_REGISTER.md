# AEGIS-DocIntel — WP-08.05: Environment Variable Register

> **Work Package**: WP-08 — Integration (Work Item WP-08.05)  
> **Status**: **REGISTER AUDITED**  
> **Date**: 2026-11-04  

---

## 1. Classification Taxonomy
- **PUBLIC**: Safe for frontend or public logs (e.g., hostnames, port numbers, log levels).
- **INTERNAL**: Application operational configuration; never exposed to end-users.
- **SECRET**: Cryptographic keys, credentials, or connection secrets; strictly forbidden in logs or image layers.

---

## 2. Configuration Register

| Variable Name | Classification | Default Value | Required Environments | Description / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `AEGIS_ENVIRONMENT` | PUBLIC | `development` | Local, CI, Staging, Production | Deployment stage identifier (`production`, `staging`, `ci`) |
| `AEGIS_API_HOST` | PUBLIC | `0.0.0.0` | All | Network interface binding |
| `AEGIS_API_PORT` | PUBLIC | `8000` | All | API listener port |
| `AEGIS_LOG_LEVEL` | PUBLIC | `INFO` | All | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `AEGIS_MAX_UPLOAD_BYTES` | INTERNAL | `209715200` | Staging, Production | Maximum upload size in bytes (200 MB default) |
| `AEGIS_DATABASE_URL` | SECRET | `None` (fallback SQLite) | Staging, Production | PostgreSQL connection string |
| `AEGIS_REDIS_URL` | SECRET | `None` (fallback in-memory)| Staging, Production | Redis queue and lease connection string |
| `AEGIS_JWT_ISSUER` | INTERNAL | `aegis-auth` | Staging, Production | Expected JWT token issuer claim |
| `AEGIS_JWT_AUDIENCE` | INTERNAL | `aegis-api` | Staging, Production | Expected JWT token audience claim |
| `AEGIS_JWT_PUBLIC_KEY` | SECRET | `None` | Staging, Production | PEM-encoded RSA/EC public key for JWT validation |
| `AEGIS_API_KEYS` | SECRET | `None` | Staging, Production | Comma-delimited hashed API keys for service accounts |
| `S3_ENDPOINT` | INTERNAL | `http://localhost:9000` | Staging, Production | MinIO / AWS S3 endpoint |
| `S3_ACCESS_KEY` | SECRET | `None` | Staging, Production | Object storage access identifier |
| `S3_SECRET_KEY` | SECRET | `None` | Staging, Production | Object storage secret credential |
| `TIKTOKEN_CACHE_DIR` | INTERNAL | `/tmp/tiktoken` | All | Read-only/scratch token cache path |

---

## 3. Secret Protection Rules

1. Secrets must never appear in `git` commits or Docker image layers.
2. Missing required production secrets trigger immediate startup abortion (`ConfigurationError`).
3. Secrets are redacted automatically from structlog events and HTTP error payloads.
