# Security & Compliance — Deployment Assumptions

This document states explicitly what this codebase assumes its deployment
environment provides, versus what it enforces itself. Anyone deploying this
system is responsible for the "environment provides" column.

| Control | This codebase | The deployment environment must provide |
|---|---|---|
| TLS / encryption in transit | No code-level enforcement | A TLS-terminating reverse proxy/load balancer in front of the app |
| `AEGIS_ENVIRONMENT` variable | Defaults fail-safe to "production" | Must NOT be set to "development" in any real deployment (see Phase 10) |
| Document persistence | SQLite store persists document metadata and raw bytes across restarts (`src/services/container.py`) | A persistent filesystem volume / directory mount with appropriate OS-level permissions and backup retention |
| Document Integrity & Checksum | Enforces SHA-256 byte verification on rehydration and tombstoned cascading deletion | Volume durability and backup snapshots to prevent storage media failure |
| Encryption at rest | SQLite database files and audit logs stored unencrypted by application layer | Underlying volume-level encryption (e.g. LUKS, AWS EBS encrypted volumes, BitLocker) |
| Network isolation | `0.0.0.0` bind is the default (Phase 10) | A firewall/security-group restricting inbound access appropriately |
