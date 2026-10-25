# AEGIS-DocIntel — Deployment & Runtime Guide

This guide describes how to configure, launch, monitor, and maintain AEGIS-DocIntel across development, staging, and production environments.

> [!NOTE]
> The system is designed with a fail-closed architecture: in production mode (`AEGIS_ENVIRONMENT=production`), the application strictly validates all settings at startup and refuses to boot if insecure defaults (such as in-memory storage, unhashed API keys, or wildcard CORS) are detected.

---

## 1. Prerequisites & System Dependencies

- **Python Runtime:** Python 3.12 (standard 64-bit).
- **OCR & Document Extraction Engines:**
  - `tesseract-ocr` (for scanned PDF / OCR fallback)
  - `poppler-utils` (`pdftotext`, `pdftoppm`)
- **System Memory:** Minimum 2 GB RAM (4 GB recommended for dense vector models).
- **Persistent Storage:** Local or mounted volume for SQLite (`AEGIS_SQLITE_PATH`).

---

## 2. Configuration & Environment Variables

AEGIS-DocIntel reads settings via [`src/core/settings.py`](../../src/core/settings.py) and supports `.env` files. A template of all available environment variables is provided in [`.env.example`](../../.env.example).

### Core Runtime Variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `AEGIS_ENVIRONMENT` | `development` | Target environment (`development`, `staging`, `production`, `test`). |
| `AEGIS_HOST` | `0.0.0.0` | Listen host interface. |
| `AEGIS_PORT` | `8000` | HTTP service port. |
| `AEGIS_SQLITE_PATH` | `data/documents.db` | Path to persistent SQLite document database. |
| `AEGIS_MAX_UPLOAD_BYTES` | `209715200` (200MB) | Enforced maximum file upload ceiling. |
| `AEGIS_REQUEST_TIMEOUT_SECONDS` | `60.0` | Global timeout for downstream operations and shutdown. |
| `AEGIS_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `AEGIS_ENABLE_DOCS` | `true` (false in prod) | Toggles Swagger UI (`/docs`) and OpenAPI spec (`/openapi.json`). |
| `AEGIS_CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins (wildcard `*` rejected in production). |

### Production Startup Validation Rules

When `AEGIS_ENVIRONMENT=production`, the service enforces strict invariants:
1. **Persistent Database:** In-memory SQLite (`:memory:`) is rejected.
2. **CORS Restrictions:** Wildcard CORS (`*`) is forbidden.
3. **Authentication Required:** Either JWT secrets (`AEGIS_JWT_SECRET` / public key) or valid API key hashes (`AEGIS_API_KEY_HASHES`) must be supplied.
4. **JWT Claims:** `AEGIS_JWT_ISSUER` and `AEGIS_JWT_AUDIENCE` are mandatory when JWT authentication is used.
5. **No Raw Keys:** Raw unhashed API keys in configuration are rejected; pre-computed SHA-256 hashes must be provided.
6. **External Model Consent:** External LLM calls require explicit declaration (`AEGIS_ALLOW_EXTERNAL_LLM=true`).

---

## 3. Container Deployment (Docker)

A hardened Docker container runs as a non-privileged user (`aegis`, UID 1000):

```bash
# Build the container image
docker build -t aegis-docintel:latest .

# Run container with mounted persistent volume
docker run -d \
  --name aegis-service \
  -p 8000:8000 \
  -e AEGIS_ENVIRONMENT=production \
  -e AEGIS_SQLITE_PATH=/app/data/documents.db \
  -e AEGIS_ENABLE_DOCS=false \
  -e AEGIS_API_KEY_HASHES="01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b" \
  -v aegis_data:/app/data \
  aegis-docintel:latest
```

---

## 4. Health and Readiness Probes

AEGIS-DocIntel provides dedicated probes for container orchestrators (Kubernetes, ECS, Docker Swarm):

- **Liveness Probe:** `GET /health`
  - Validates that the event loop is active and process is responsive.
  - Returns `200 OK` with status `healthy` or `degraded`.
- **Readiness Probe:** `GET /readiness`
  - Validates that the service container is started and persistent SQLite database is accessible and queryable (`SELECT 1 FROM documents`).
  - Returns `200 OK` when ready to serve traffic; returns `503 Service Unavailable` if database write/read locks fail.

---

## 5. Operations & Runbooks

- [Operations Runbook](operations-runbook.md) — Day-2 operations, telemetry, and monitoring.
- [Backup & Restore Runbook](backup-and-restore.md) — Disaster recovery procedures and integrity checks.
- [Rollback Runbook](rollback.md) — Emergency deployment rollback and state reversion.
